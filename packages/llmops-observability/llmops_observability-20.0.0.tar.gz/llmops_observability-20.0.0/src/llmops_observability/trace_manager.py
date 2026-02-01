"""
Simplified Trace Manager for LLMOps Observability
Collects all spans and sends as single SDKTraceData to SQS
"""
from __future__ import annotations
import uuid
import threading
import time
import traceback
import functools
import inspect
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union

from .sqs import send_to_sqs_immediate, is_sqs_enabled
from .config import (
    MAX_OUTPUT_SIZE,
    MAX_SQS_SIZE,
    MAX_SPAN_IO_SIZE,
    MAX_TRACE_IO_SIZE,
    TRUNCATION_PREVIEW_SIZE,
    PROMPT_RESPONSE_MAX_SIZE,
    get_project_id,
    get_environment,
)

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[llmops_observability] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def serialize_value(value: Any, max_size: int = MAX_OUTPUT_SIZE) -> Any:
    """Serialize value with size limit to prevent large data issues."""
    try:
        serialized_str = json.dumps(value, default=str)
        serialized_bytes = serialized_str.encode('utf-8')
        
        if len(serialized_bytes) <= max_size:
            return json.loads(serialized_str)
        
        # Too large - return truncation info
        preview_size = min(1000, max_size // 2)
        preview = serialized_str[:preview_size]
        
        logger.warning(f"Output truncated: {len(serialized_bytes)} bytes -> {max_size} bytes limit")
        
        return {
            "_truncated": True,
            "_original_size_bytes": len(serialized_bytes),
            "_original_size_mb": round(len(serialized_bytes) / (1024 * 1024), 2),
            "_preview": preview + "...",
            "_message": f"Output truncated (original: {round(len(serialized_bytes) / (1024 * 1024), 2)} MB, limit: {round(max_size / 1024, 0)} KB)"
        }
    except Exception as e:
        return str(value)


def safe_locals(d: Dict[str, Any]) -> Dict[str, Any]:
    """Safely serialize local variables"""
    return {k: serialize_value(v) for k, v in d.items() if not k.startswith("_")}


# Data models for SDK
class SpanData:
    """Individual span/generation data"""
    def __init__(self, **kwargs):
        self.span_id = kwargs.get('span_id')
        self.span_name = kwargs.get('span_name')
        self.span_type = kwargs.get('span_type')
        self.parent_span_id = kwargs.get('parent_span_id')
        self.start_time = kwargs.get('start_time')
        self.end_time = kwargs.get('end_time')
        self.duration_ms = kwargs.get('duration_ms')
        self.input_data = kwargs.get('input_data')
        self.output_data = kwargs.get('output_data')
        self.error = kwargs.get('error')
        self.model_id = kwargs.get('model_id')
        self.metadata = kwargs.get('metadata', {})
        self.tags = kwargs.get('tags', [])
        self.usage = kwargs.get('usage')
        self.prompt = kwargs.get('prompt')
        self.response = kwargs.get('response')
        self.status = kwargs.get('status', 'success')
        self.status_message = kwargs.get('status_message')
        self.level = kwargs.get('level', 'DEFAULT')


class SDKTraceData:
    """Complete trace data to be sent to SQS"""
    def __init__(self, **kwargs):
        self.trace_id = kwargs.get('trace_id')
        self.trace_name = kwargs.get('trace_name')
        self.project_id = kwargs.get('project_id')
        self.environment = kwargs.get('environment')
        self.user_id = kwargs.get('user_id')
        self.session_id = kwargs.get('session_id')
        self.start_time = kwargs.get('start_time')
        self.end_time = kwargs.get('end_time')
        self.duration_ms = kwargs.get('duration_ms')
        self.trace_input = kwargs.get('trace_input')
        self.trace_output = kwargs.get('trace_output')
        self.spans = kwargs.get('spans', [])
        self.metadata = kwargs.get('metadata', {})
        self.tags = kwargs.get('tags', [])
        self.total_spans = kwargs.get('total_spans', 0)
        self.total_generations = kwargs.get('total_generations', 0)
        self.sdk_name = kwargs.get('sdk_name', 'llmops-observability')
        self.sdk_version = kwargs.get('sdk_version', '2.0.0')
    
    def prepare_for_sqs(self) -> str:
        """Prepare trace data for SQS with compression"""
        import gzip
        import base64
        
        # Build payload
        processed_spans = []
        for span in self.spans:
            processed_spans.append({
                "span_id": span.span_id,
                "span_name": span.span_name,
                "span_type": span.span_type,
                "parent_span_id": span.parent_span_id,
                "start_time": span.start_time,
                "end_time": span.end_time,
                "duration_ms": span.duration_ms,
                "input_data": self._truncate_field(span.input_data, MAX_SPAN_IO_SIZE),
                "output_data": self._truncate_field(span.output_data, MAX_SPAN_IO_SIZE),
                "error": span.error,
                "model_id": span.model_id,
                "metadata": span.metadata,
                "tags": span.tags,
                "usage": span.usage,
                "prompt": self._truncate_field(span.prompt, PROMPT_RESPONSE_MAX_SIZE) if span.prompt else None,
                "response": self._truncate_field(span.response, PROMPT_RESPONSE_MAX_SIZE) if span.response else None,
                "status": span.status,
                "status_message": span.status_message,
                "level": span.level,
            })
        
        payload = {
            "trace_id": self.trace_id,
            "trace_name": self.trace_name,
            "project_id": self.project_id,
            "environment": self.environment,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "trace_input": self._truncate_field(self.trace_input, MAX_TRACE_IO_SIZE),
            "trace_output": self._truncate_field(self.trace_output, MAX_TRACE_IO_SIZE),
            "spans": processed_spans,
            "metadata": self.metadata,
            "tags": self.tags,
            "total_spans": self.total_spans,
            "total_generations": self.total_generations,
            "sdk_name": self.sdk_name,
            "sdk_version": self.sdk_version,
        }
        
        # Serialize to JSON
        json_str = json.dumps(payload, default=str)
        json_bytes = json_str.encode('utf-8')
        
        logger.info(f"Trace {self.trace_id} - Uncompressed size: {len(json_bytes)} bytes ({round(len(json_bytes)/1024, 2)} KB)")
        
        # Compress
        compressed = gzip.compress(json_bytes, compresslevel=6)
        logger.info(f"Trace {self.trace_id} - Compressed size: {len(compressed)} bytes ({round(len(compressed)/1024, 2)} KB)")
        
        # Check size
        if len(compressed) <= MAX_SQS_SIZE:
            return json.dumps({
                "compressed": True,
                "data": base64.b64encode(compressed).decode('utf-8'),
                "trace_id": self.trace_id,
            })
        
        # Too large - aggressive truncation
        logger.warning(f"Trace {self.trace_id} too large ({len(compressed)} bytes). Applying aggressive truncation.")
        
        summary_payload = {
            "trace_id": self.trace_id,
            "trace_name": self.trace_name,
            "project_id": self.project_id,
            "environment": self.environment,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "trace_input": self._create_summary(self.trace_input),
            "trace_output": self._create_summary(self.trace_output),
            "spans": (
                processed_spans[:5] + processed_spans[-5:] 
                if len(processed_spans) > 10 
                else processed_spans
            ),
            "spans_truncated": len(processed_spans) - 10 if len(processed_spans) > 10 else 0,
            "metadata": self.metadata,
            "tags": self.tags,
            "total_spans": self.total_spans,
            "total_generations": self.total_generations,
            "sdk_name": self.sdk_name,
            "sdk_version": self.sdk_version,
            "_warning": "Trace data truncated due to size limits"
        }
        
        json_str = json.dumps(summary_payload, default=str)
        compressed = gzip.compress(json_str.encode('utf-8'), compresslevel=9)
        
        return json.dumps({
            "compressed": True,
            "data": base64.b64encode(compressed).decode('utf-8'),
            "trace_id": self.trace_id,
            "truncated": True,
        })
    
    def _truncate_field(self, value: Any, max_bytes: int) -> Any:
        """Truncate field if too large"""
        if value is None:
            return None
        
        try:
            serialized = json.dumps(value, default=str)
            size = len(serialized.encode('utf-8'))
            
            if size <= max_bytes:
                return value
            
            preview_size = max_bytes // 2
            preview = serialized[:preview_size]
            
            return {
                "_truncated": True,
                "_original_size_bytes": size,
                "_original_size_kb": round(size / 1024, 2),
                "_preview": preview + "...",
                "_message": f"Field truncated ({round(size / 1024, 2)} KB -> {round(max_bytes / 1024, 2)} KB limit)"
            }
        except Exception as e:
            logger.warning(f"Failed to truncate field: {e}")
            return str(value)[:max_bytes]
    
    def _create_summary(self, value: Any) -> Dict[str, Any]:
        """Create summary of a value"""
        if value is None:
            return {"_type": "null", "_value": None}
        
        try:
            serialized = json.dumps(value, default=str)
            size = len(serialized.encode('utf-8'))
            
            return {
                "_type": type(value).__name__,
                "_size_bytes": size,
                "_size_kb": round(size / 1024, 2),
                "_preview": str(value)[:500] if size > 500 else value,
                "_message": "Full content omitted due to size"
            }
        except Exception:
            return {
                "_type": type(value).__name__,
                "_error": "Could not serialize"
            }


class TraceManager:
    """Simplified TraceManager"""
    _lock = threading.Lock()
    _pending_lock = threading.Lock()
    _pending_cond = threading.Condition(_pending_lock)
    _pending_count = 0
    _active: Dict[str, Any] = {
        "trace_id": None,
        "trace_config": None,
        "start_time": None,
        "spans": [],
        "stack": [],
        "finalized_trace_id": None,  # Track if trace was finalized (for late spans)
        "finalized_timestamp": None,  # When trace was finalized
    }

    @classmethod
    def has_active_trace(cls) -> bool:
        """Check if there's an active trace"""
        with cls._lock:
            return cls._active["trace_id"] is not None

    @classmethod
    def can_track_span(cls) -> bool:
        """Check if we can track spans (active OR finalized trace)"""
        with cls._lock:
            return cls._active["trace_id"] is not None or cls._active["finalized_trace_id"] is not None

    @classmethod
    def _now(cls) -> str:
        """Get current UTC timestamp"""
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def _reset_pending(cls) -> None:
        with cls._pending_cond:
            cls._pending_count = 0
            cls._pending_cond.notify_all()

    @classmethod
    def _increment_pending_if_active(cls) -> bool:
        with cls._lock:
            if cls._active.get("trace_id") is None:
                return False
        with cls._pending_cond:
            cls._pending_count += 1
            return True

    @classmethod
    def _decrement_pending(cls) -> None:
        with cls._pending_cond:
            if cls._pending_count > 0:
                cls._pending_count -= 1
            cls._pending_cond.notify_all()

    @classmethod
    def _wait_for_pending(cls) -> None:
        with cls._pending_cond:
            while cls._pending_count > 0:
                cls._pending_cond.wait()

    @classmethod
    def start_trace(
        cls,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Start a new trace"""
        # Get project_id and environment from config (centralized)
        project_id = get_project_id()
        environment = get_environment()
        
        trace_config = {
            "name": name,
            "project_id": project_id,
            "environment": environment,
            "user_id": user_id,
            "session_id": session_id,
            "metadata": metadata or {},
            "tags": tags or [],
            "trace_name": project_id,
        }
        
        cls._reset_pending()

        with cls._lock:
            trace_id = str(uuid.uuid4())
            cls._active["trace_id"] = trace_id
            cls._active["trace_config"] = trace_config
            cls._active["start_time"] = time.time()
            cls._active["spans"] = []
            cls._active["stack"] = []
            
            logger.info(
                f"Trace started: {trace_config['trace_name']} | "
                f"Operation: {trace_config['name']} | "
                f"Env: {trace_config['environment']} (ID: {trace_id})"
            )
            
            return trace_id

    @classmethod
    def add_span(cls, span: SpanData):
        """Add a completed span to the trace"""
        with cls._lock:
            trace_id = cls._active.get("trace_id")
            finalized_trace_id = cls._active.get("finalized_trace_id")
            
            # Auto-inject environment and project_id into span metadata
            trace_config = cls._active.get("trace_config", {})
            if trace_config:
                # Initialize metadata dict if needed
                if not span.metadata:
                    span.metadata = {}
                
                # Inject environment and project_id from trace config
                span.metadata["environment"] = trace_config.get("environment", "unknown")
                span.metadata["project_id"] = trace_config.get("project_id", "unknown_project")
            
            # If no active trace but we have a finalized one, this is a LATE SPAN
            if not trace_id and finalized_trace_id:
                cls._submit_late_span_async(span, finalized_trace_id)
                return
            
            # Normal path: add to current trace
            if not trace_id:
                logger.warning(f"Cannot add span {span.span_name} - no active trace")
                return
            
            cls._active["spans"].append(span)
            logger.debug(f"Span added: {span.span_name} ({span.duration_ms}ms)")

    @classmethod
    def push_span_context(cls, span_id: str):
        """Push span ID onto stack (for nesting)"""
        with cls._lock:
            cls._active["stack"].append(span_id)

    @classmethod
    def pop_span_context(cls) -> Optional[str]:
        """Pop span ID from stack"""
        with cls._lock:
            if cls._active["stack"]:
                return cls._active["stack"].pop()
            return None

    @classmethod
    def get_current_parent_span_id(cls) -> Optional[str]:
        """Get the current parent span ID from stack"""
        with cls._lock:
            if cls._active["stack"]:
                return cls._active["stack"][-1]
            return None

    @classmethod
    def end_trace(cls) -> Optional[str]:
        """End the current trace"""
        with cls._lock:
            trace_id = cls._active["trace_id"]
            
            if not trace_id:
                return None
            
            logger.info(f"Trace ended: {trace_id}")
            return trace_id

    @classmethod
    def _submit_late_span_async(cls, span: SpanData, original_trace_id: str):
        """Submit a single span as late arrival (separate SQS message for merging)"""
        import gzip
        import base64
        
        try:
            # Package JUST this span with reference to original trace
            payload = {
                "type": "late_span_update",           # Flag for Lambda
                "original_trace_id": original_trace_id,  # Links to main trace
                "span": {
                    "span_id": span.span_id,
                    "span_name": span.span_name,
                    "span_type": span.span_type,
                    "parent_span_id": span.parent_span_id,
                    "start_time": span.start_time,
                    "end_time": span.end_time,
                    "duration_ms": span.duration_ms,
                    "input_data": span.input_data,
                    "output_data": span.output_data,
                    "error": span.error,
                    "model_id": span.model_id,
                    "metadata": span.metadata,
                    "tags": span.tags,
                    "usage": span.usage,
                    "prompt": span.prompt,
                    "response": span.response,
                    "status": span.status,
                    "status_message": span.status_message,
                    "level": span.level,
                },
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            }
            
            # Compress
            json_str = json.dumps(payload, default=str)
            compressed = gzip.compress(json_str.encode('utf-8'), compresslevel=6)
            
            # Send as SQS message
            sqs_payload = json.dumps({
                "compressed": True,
                "data": base64.b64encode(compressed).decode('utf-8'),
                "trace_id": original_trace_id,
                "type": "late_span_update",
            })
            
            send_to_sqs_immediate(sqs_payload)
            logger.info(f"[LATE_SPAN] Late span submitted: {span.span_name} for trace {original_trace_id}")
            
        except Exception as e:
            logger.error(f"Failed to submit late span: {e}")
            traceback.print_exc()

    @classmethod
    def finalize_and_send(
        cls,
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_name: Optional[str] = None,
        trace_input: Optional[dict] = None,
        trace_output: Optional[dict] = None,
        extra_spans: list = [],
    ) -> bool:
        """Finalize trace and send to SQS"""
        cls._wait_for_pending()

        with cls._lock:
            trace_id = cls._active.get("trace_id")
            trace_config = cls._active.get("trace_config")
            start_time = cls._active.get("start_time")
            spans = cls._active.get("spans", [])
            
            if not trace_id or not trace_config:
                logger.error("No active trace to finalize")
                return False
            
            # Ensure start_time is not None
            if start_time is None:
                logger.error("Invalid trace state: start_time is None")
                return False
            
            # Use defaults from trace_config if not provided
            final_trace_name = trace_name or trace_config.get("name", "unknown")
            final_user_id = user_id or trace_config.get("user_id", "unknown_user")
            final_session_id = session_id or trace_config.get("session_id", "unknown_session")
            # Use defaults from trace_config if not provided
            final_trace_name = trace_name or trace_config.get("name", "unknown")
            final_user_id = user_id or trace_config.get("user_id", "unknown_user")
            final_session_id = session_id or trace_config.get("session_id", "unknown_session")
            
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            # Count generations
            total_generations = sum(1 for s in spans if s.span_type == "generation")
            
            # Build SDKTraceData
            trace_data = SDKTraceData(
                trace_id=trace_id,
                trace_name=final_trace_name,
                project_id=trace_config.get("project_id", "unknown_project"),
                environment=trace_config.get("environment", "development"),
                user_id=final_user_id,
                session_id=final_session_id,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                trace_input=trace_input or {},
                trace_output=trace_output or {},
                spans=spans,
                metadata=trace_config.get("metadata", {}),
                tags=trace_config.get("tags", []),
                total_spans=len(spans),
                total_generations=total_generations,
            )
            
            # Mark this trace as finalized (for late-arriving spans)
            cls._active["finalized_trace_id"] = trace_id
            cls._active["finalized_timestamp"] = time.time()
            
            # Clear active trace (but keep finalized_trace_id for late spans)
            cls._active["trace_id"] = None
            cls._active["trace_config"] = None
            cls._active["start_time"] = None
            cls._active["spans"] = []
            cls._active["stack"] = []
        
        # Send to SQS
        if not is_sqs_enabled():
            logger.warning("SQS not enabled - trace data not sent")
            return False
        
        try:
            # Prepare compressed payload
            compressed_payload = trace_data.prepare_for_sqs()
            
            # Send to SQS
            send_to_sqs_immediate(compressed_payload)
            
            logger.info(
                f"[OK] Trace finalized and sent to SQS: {final_trace_name} "
                f"(ID: {trace_id}, spans: {len(spans)})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error sending trace to SQS: {e}")
            traceback.print_exc()
            return False


# ============================================================
# Decorator: track_function
# ============================================================

def _build_function_input_data(
    args: tuple,
    kwargs: Dict[str, Any],
    local_vars: Optional[Dict[str, Any]] = None,
    capture_locals_spec: Union[bool, List[str]] = False,
    capture_self_flag: bool = False,
) -> Dict[str, Any]:
    """Build input_data dict with optional capture of locals and self"""
    input_data = {
        "args": serialize_value(args),
        "kwargs": serialize_value(kwargs),
    }
    
    # Capture self if requested
    if capture_self_flag and args and hasattr(args[0], '__dict__'):
        try:
            input_data["self"] = serialize_value(args[0])
        except Exception:
            pass
    
    # Capture local variables if requested
    if capture_locals_spec and local_vars:
        if isinstance(capture_locals_spec, bool) and capture_locals_spec:
            # Capture all locals (except private ones)
            input_data["locals"] = safe_locals(local_vars)
        elif isinstance(capture_locals_spec, list):
            # Capture only specified locals
            input_data["locals"] = {
                k: serialize_value(v) 
                for k, v in local_vars.items() 
                if k in capture_locals_spec
            }
    
    return input_data


def track_function(
    name: Optional[str] = None,
    *,
    metadata: Optional[Dict[str, Any]] = None,
    capture_locals: Union[bool, List[str]] = False,
    capture_self: bool = False,
):
    """Decorator to track function execution"""
    def decorator(func):
        span_name = name or func.__name__
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Track spans even after finalization (for late spans)
                if not TraceManager.can_track_span():
                    return await func(*args, **kwargs)

                pending_added = TraceManager._increment_pending_if_active()
                
                span_id = str(uuid.uuid4())
                parent_span_id = TraceManager.get_current_parent_span_id()
                start_time = time.time()
                
                TraceManager.push_span_context(span_id)
                
                error = None
                result = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    end_time = time.time()
                    duration_ms = int((end_time - start_time) * 1000)
                    
                    TraceManager.pop_span_context()
                    
                    # Capture local variables if needed
                    local_vars = {}
                    if capture_locals or capture_self:
                        try:
                            frame = inspect.currentframe()
                            if frame and frame.f_back:
                                local_vars = frame.f_back.f_locals.copy()
                        except Exception:
                            pass
                    
                    span_data = SpanData(
                        span_id=span_id,
                        span_name=span_name,
                        span_type="span",
                        parent_span_id=parent_span_id,
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                        input_data=_build_function_input_data(
                            args, kwargs, local_vars, capture_locals, capture_self
                        ),
                        output_data=serialize_value(result) if not error else None,
                        error=str(error) if error else None,
                        metadata=metadata or {},
                        status="error" if error else "success",
                        status_message=str(error) if error else None,
                    )
                    
                    TraceManager.add_span(span_data)

                    if pending_added:
                        TraceManager._decrement_pending()
            
            return async_wrapper
        
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Track spans even after finalization (for late spans)
                if not TraceManager.can_track_span():
                    return func(*args, **kwargs)

                pending_added = TraceManager._increment_pending_if_active()
                
                span_id = str(uuid.uuid4())
                parent_span_id = TraceManager.get_current_parent_span_id()
                start_time = time.time()
                
                TraceManager.push_span_context(span_id)
                
                error = None
                result = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    end_time = time.time()
                    duration_ms = int((end_time - start_time) * 1000)
                    
                    TraceManager.pop_span_context()
                    
                    # Capture local variables if needed
                    local_vars = {}
                    if capture_locals or capture_self:
                        try:
                            frame = inspect.currentframe()
                            if frame and frame.f_back:
                                local_vars = frame.f_back.f_locals.copy()
                        except Exception:
                            pass
                    
                    span_data = SpanData(
                        span_id=span_id,
                        span_name=span_name,
                        span_type="span",
                        parent_span_id=parent_span_id,
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                        input_data=_build_function_input_data(
                            args, kwargs, local_vars, capture_locals, capture_self
                        ),
                        output_data=serialize_value(result) if not error else None,
                        error=str(error) if error else None,
                        metadata=metadata or {},
                        status="error" if error else "success",
                        status_message=str(error) if error else None,
                    )
                    
                    TraceManager.add_span(span_data)

                    if pending_added:
                        TraceManager._decrement_pending()
            
            return sync_wrapper
    
    return decorator

