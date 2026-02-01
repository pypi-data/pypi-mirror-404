# src/llmops_observability/sqs.py
"""
Production-grade SQS sender with batching, spillover, and clean shutdown.
Ported from veriskGO with enhanced error handling and resilience.
"""

import json
import boto3
import queue
import threading
import time
import os
import atexit
import tempfile
import logging
from typing import Optional, Dict, Any

from .config import (
    SPILLOVER_FILE,
    SQS_WORKER_COUNT,
    SQS_BATCH_SIZE,
    SQS_BATCH_TIMEOUT,
    SQS_FLUSH_TIME_THRESHOLD,
    SQS_SHUTDOWN_TIMEOUT,
    get_sqs_config,
)

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[llmops_observability] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

MAIN_PID = os.getpid()


class _LLMOpsObservabilitySQS:
    """
    PRODUCTION-GRADE SQS SENDER
    - Daemon worker threads (never block shutdown)
    - Force-flush on exit (guarantees delivery)
    - Clean shutdown (prevents Event loop is closed errors on Windows)
    - Auto spillover for failed sends
    - Resilient to SQS outages
    """

    SHUTDOWN_SENTINEL = None  # Used to tell workers to stop

    def __init__(self):
        self.client: Optional[Any] = None
        self.queue_url: Optional[str] = None
        self.sqs_enabled = False
        self._init_once = False

        # Internal queue for batching
        self._q: queue.Queue = queue.Queue(maxsize=0)

        # Flag to stop workers cleanly
        self._shutting_down = False

        # Restore spillover messages from disk
        self._load_spillover()

        # Start worker threads
        self.worker_count = SQS_WORKER_COUNT
        self.workers = []
        for i in range(self.worker_count):
            t = threading.Thread(target=self._safe_worker_loop, daemon=True)
            t.start()
            self.workers.append(t)

        # Don't initialize immediately - wait until first use
        # This allows environment variables to be set after import

    # -------------------------------------------------------
    # CLEAN SHUTDOWN SUPPORT
    # -------------------------------------------------------
    def shutdown(self):
        """Safely stop worker threads without touching asyncio loop."""
        if self._shutting_down:
            return
        self._shutting_down = True

        # Signal workers to exit
        for _ in range(self.worker_count):
            self._q.put(self.SHUTDOWN_SENTINEL)

        # Wait for them to finish
        for t in self.workers:
            try:
                t.join(timeout=SQS_SHUTDOWN_TIMEOUT)
            except Exception:
                pass

    # -------------------------------------------------------
    # SPILLOVER SAVE (Fallback storage)
    # -------------------------------------------------------
    def _spillover_save(self, message: Dict[str, Any] | str):
        """Save message to disk if SQS send fails (for recovery)."""
        try:
            with open(SPILLOVER_FILE, "a") as f:
                if isinstance(message, dict):
                    f.write(json.dumps(message) + "\n")
                else:
                    f.write(message + "\n")
            logger.debug(f"Message saved to spillover: {message.get('event_type') if isinstance(message, dict) else 'unknown'}")
        except Exception as e:
            logger.error(f"Spillover save failed: {e}")

    # -------------------------------------------------------
    # SPILLOVER LOAD (Recovery from disk)
    # -------------------------------------------------------
    def _load_spillover(self):
        """Load spillover messages from disk (recovery on startup)."""
        if not os.path.exists(SPILLOVER_FILE):
            return

        try:
            logger.info("Restoring spillover queue from disk...")
            with open(SPILLOVER_FILE, "r") as f:
                for line in f:
                    try:
                        self._q.put(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            os.remove(SPILLOVER_FILE)
            logger.info("Spillover restored and cleaned.")
        except Exception as e:
            logger.error(f"Spillover load failed: {e}")

    # -------------------------------------------------------
    # SAFE WORKER LOOP (auto-restarting on crash)
    # -------------------------------------------------------
    def _safe_worker_loop(self):
        """Worker loop that auto-restarts on crash."""
        while True:
            try:
                self._worker_loop()
                return
            except Exception as e:
                logger.error(f"Worker crashed: {e}")
                time.sleep(0.5)
                logger.info("Restarting worker...")

    # -------------------------------------------------------
    # REAL WORKER LOOP (batch processing)
    # -------------------------------------------------------
    def _worker_loop(self):
        """Main worker loop with batch accumulation and send."""
        batch = []
        while True:
            try:
                msg = self._q.get(timeout=SQS_BATCH_TIMEOUT)

                # Shutdown signal
                if msg is self.SHUTDOWN_SENTINEL:
                    return

                batch.append(msg)

            except queue.Empty:
                pass

            # Batch conditions: flush if batch size >= 10 or time-based (every ~1s)
            flush_size = len(batch) >= SQS_BATCH_SIZE
            flush_time = batch and (time.time() % 1 < SQS_FLUSH_TIME_THRESHOLD)

            if flush_size or flush_time:
                try:
                    self._send_batch(batch)
                except RuntimeError as e:
                    if "Event loop is closed" in str(e):
                        # Safe ignore — Windows cleanup issue
                        return
                    raise
                batch = []

    # -------------------------------------------------------
    # FORCE FLUSH
    # -------------------------------------------------------
    def force_flush(self):
        """Synchronously send all remaining messages (used on shutdown)."""
        batch = []
        while not self._q.empty():
            try:
                msg = self._q.get_nowait()
                if msg is not self.SHUTDOWN_SENTINEL:
                    batch.append(msg)
            except Exception:
                break

        if batch:
            self._send_batch(batch)

        time.sleep(0.1)

    # -------------------------------------------------------
    # AWS INIT (Lazy initialization with fallback)
    # -------------------------------------------------------
    def _auto_initialize(self):
        """Initialize AWS SQS client from config. Fails gracefully if misconfigured."""
        if self._init_once and self.client:
            return

        cfg = get_sqs_config()
        self.queue_url = cfg.get("aws_sqs_url")

        if not self.queue_url:
            logger.info("No SQS URL configured -> SQS disabled.")
            self.sqs_enabled = False
            self._init_once = True
            return

        try:
            session = boto3.Session(
                # profile_name=cfg.get("aws_profile"),
                region_name=cfg.get("aws_region")
            )
            self.client = session.client("sqs")

            # Test connection
            self.client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=["QueueArn"]
            )

            self.sqs_enabled = True
            logger.info(f"SQS connected -> {self.queue_url}")

        except Exception as e:
            logger.warning(f"SQS initialization failed: {e} -> Spillover enabled.")
            self.client = None
            self.sqs_enabled = False

        self._init_once = True

    # -------------------------------------------------------
    # PUBLIC SEND API
    # -------------------------------------------------------
    def send(self, message: Optional[Dict[str, Any]]) -> bool:
        """
        Queue a message for batched send to SQS.
        Non-blocking; if SQS is down, spillover to disk.
        
        Args:
            message: Dictionary message to send
            
        Returns:
            bool: True if queued successfully
        """
        if not message:
            return False

        if not self.sqs_enabled:
            self._auto_initialize()

        try:
            self._q.put_nowait(message)
            return True
        except Exception as e:
            logger.debug(f"Queue full -> spillover: {e}")
            self._spillover_save(message)
            return False

    def send_immediate(self, message) -> bool:
        """
        Send message immediately without batching.
        Use for critical messages like trace_end.
        Falls back to spillover if SQS unavailable.
        
        Args:
            message: Dictionary message or JSON string to send
            
        Returns:
            bool: True if sent successfully
        """
        if not message:
            return False

        if not self.sqs_enabled:
            self._auto_initialize()

        if not self.client:
            logger.debug("SQS unavailable for immediate send -> spillover")
            # For spillover, convert string to dict if needed
            if isinstance(message, str):
                try:
                    message = json.loads(message)
                except Exception:
                    pass
            self._spillover_save(message)
            return False

        try:
            # Handle both dict and string payloads
            if isinstance(message, str):
                message_body = message
            else:
                message_body = json.dumps(message)
            
            self.client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body
            )
            
            # Extract event type for logging
            event_type = "trace_data"
            if isinstance(message, dict):
                event_type = message.get('event_type', 'trace_data')
            elif isinstance(message, str):
                try:
                    parsed = json.loads(message)
                    event_type = parsed.get('trace_id', 'compressed_trace')
                except Exception:
                    pass
            
            logger.debug(f"Immediate send OK: {event_type}")
            return True
        except Exception as e:
            logger.warning(f"Immediate send failed: {e} -> spillover")
            # For spillover, convert string to dict if needed
            if isinstance(message, str):
                try:
                    message = json.loads(message)
                except Exception:
                    pass
            self._spillover_save(message)
            return False

    # -------------------------------------------------------
    # BATCH SEND
    # -------------------------------------------------------
    def _send_batch(self, batch):
        """Send a batch of messages to SQS. Retry individually on failure."""
        if not batch:
            return

        if not self.client:
            self._auto_initialize()

        if not self.client:
            logger.debug(f"SQS unavailable -> spillover {len(batch)} messages")
            for msg in batch:
                self._spillover_save(msg)
            return

        entries = [
            {"Id": str(i), "MessageBody": json.dumps(msg)}
            for i, msg in enumerate(batch[:10])  # Max 10 per batch API call
        ]

        try:
            response = self.client.send_message_batch(
                QueueUrl=self.queue_url,
                Entries=entries
            )
            logger.debug(f"Batch send OK: {len(entries)} messages")
        except Exception as e:
            logger.warning(f"Batch send failed: {e} -> retry individual")
            self._retry_individual(batch)

    # -------------------------------------------------------
    # RETRY INDIVIDUAL MESSAGES
    # -------------------------------------------------------
    def _retry_individual(self, batch):
        """Retry individual messages if batch send fails."""
        # Ensure SQS client exists
        if not self.client:
            self._auto_initialize()

        client = self.client
        if not client:
            logger.debug(f"Client unavailable -> spilling {len(batch)} messages")
            for msg in batch:
                self._spillover_save(msg)
            return

        for msg in batch:
            try:
                client.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=json.dumps(msg)
                )
                logger.debug(f"Individual send OK: {msg.get('event_type')}")
            except Exception as e:
                logger.warning(f"Individual send FAILED: {e} -> spillover")
                self._spillover_save(msg)


# -------------------------------------------------------
# SINGLETON INSTANCE
# -------------------------------------------------------
_sqs_instance = _LLMOpsObservabilitySQS()


def send_to_sqs(bundle: Optional[Dict[str, Any]]) -> bool:
    """Send a message to SQS queue (batched)."""
    return _sqs_instance.send(bundle)


def send_to_sqs_immediate(bundle) -> bool:
    """Send a message to SQS queue (immediate, no batching). Accepts dict or JSON string."""
    return _sqs_instance.send_immediate(bundle)


def flush_sqs():
    """Force flush all pending messages to SQS."""
    return _sqs_instance.force_flush()


def is_sqs_enabled() -> bool:
    """Check if SQS is enabled and initialized."""
    if not _sqs_instance._init_once:
        _sqs_instance._auto_initialize()
    return _sqs_instance.sqs_enabled


# -------------------------------------------------------
# AUTO-FLUSH + CLEAN SHUTDOWN
# -------------------------------------------------------
def _cleanup_at_exit():
    """Cleanup handler registered with atexit."""
    if os.getpid() != MAIN_PID:
        return

    logger.info("Flushing and shutting down SQS...")

    try:
        _sqs_instance.shutdown()     # Stop background threads
        _sqs_instance.force_flush()  # Send remaining messages
    except Exception as e:
        logger.error(f"Exit flush failed: {e}")


atexit.register(_cleanup_at_exit)
