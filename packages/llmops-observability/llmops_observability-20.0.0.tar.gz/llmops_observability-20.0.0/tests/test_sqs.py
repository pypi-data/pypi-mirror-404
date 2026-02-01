import json
import os

import llmops_observability.sqs as sqs


def _make_instance(monkeypatch, tmp_path):
    monkeypatch.setattr(sqs, "SQS_WORKER_COUNT", 0)
    spill_path = tmp_path / "spillover.jsonl"
    monkeypatch.setattr(sqs, "SPILLOVER_FILE", str(spill_path), raising=False)
    return sqs._LLMOpsObservabilitySQS()


def test_auto_initialize_disables_when_no_url(monkeypatch, tmp_path):
    monkeypatch.delenv("AWS_SQS_URL", raising=False)
    inst = _make_instance(monkeypatch, tmp_path)
    assert inst.sqs_enabled is False
    assert inst.client is None


def test_auto_initialize_success_and_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(sqs, "SQS_WORKER_COUNT", 0)
    monkeypatch.setattr(sqs, "SPILLOVER_FILE", str(tmp_path / "spillover.jsonl"), raising=False)
    monkeypatch.setattr(
        sqs,
        "get_sqs_config",
        lambda: {"aws_sqs_url": "https://example.com/q", "aws_profile": "p", "aws_region": "r"},
    )

    class Client:
        def get_queue_attributes(self, **_):
            return {"Attributes": {}}

    class Session:
        def client(self, name):
            assert name == "sqs"
            return Client()

    monkeypatch.setattr(sqs.boto3, "Session", lambda **_: Session())
    inst = sqs._LLMOpsObservabilitySQS()
    # Trigger auto-initialization (lazy init)
    inst._auto_initialize()
    assert inst.sqs_enabled is True

    class BadClient:
        def get_queue_attributes(self, **_):
            raise RuntimeError("boom")

    class BadSession:
        def client(self, name):
            return BadClient()

    monkeypatch.setattr(sqs.boto3, "Session", lambda **_: BadSession())
    inst2 = sqs._LLMOpsObservabilitySQS()
    # Trigger auto-initialization (lazy init)
    inst2._auto_initialize()
    assert inst2.sqs_enabled is False


def test_send_immediate_spillover_when_no_client(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)
    inst.sqs_enabled = True
    inst.client = None

    ok = inst.send_immediate({"event_type": "spill"})
    assert ok is False

    with open(sqs.SPILLOVER_FILE, "r") as f:
        lines = f.readlines()
    assert lines


def test_send_immediate_with_string_payload(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)

    class Client:
        def __init__(self):
            self.sent = []

        def send_message(self, QueueUrl, MessageBody):
            self.sent.append((QueueUrl, MessageBody))
            return {"MessageId": "ok"}

    inst.client = Client()
    inst.queue_url = "https://example.com/queue"
    inst.sqs_enabled = True

    ok = inst.send_immediate('{"trace_id":"t1"}')
    assert ok is True
    assert inst.client.sent


def test_send_immediate_failure_spills(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)

    class Client:
        def send_message(self, QueueUrl, MessageBody):
            raise RuntimeError("boom")

    inst.client = Client()
    inst.queue_url = "https://example.com/queue"
    inst.sqs_enabled = True

    ok = inst.send_immediate({"event_type": "immediate"})
    assert ok is False
    assert os.path.exists(sqs.SPILLOVER_FILE)


def test_send_immediate_uses_client(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)

    class Client:
        def __init__(self):
            self.sent = []

        def send_message(self, QueueUrl, MessageBody):
            self.sent.append((QueueUrl, MessageBody))
            return {"MessageId": "ok"}

    inst.client = Client()
    inst.queue_url = "https://example.com/queue"
    inst.sqs_enabled = True

    ok = inst.send_immediate({"event_type": "immediate", "value": 2})
    assert ok is True
    assert inst.client.sent


def test_send_queue_full_spills(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)
    inst.sqs_enabled = True

    class Q:
        def put_nowait(self, _msg):
            raise RuntimeError("full")

    inst._q = Q()
    ok = inst.send({"event_type": "qfull"})
    assert ok is False
    assert os.path.exists(sqs.SPILLOVER_FILE)


def test_send_batch_spills_when_no_client(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)
    inst.client = None
    inst.sqs_enabled = True
    inst._send_batch([{"event_type": "a"}, {"event_type": "b"}])

    with open(sqs.SPILLOVER_FILE, "r") as f:
        lines = f.readlines()
    assert len(lines) >= 2


def test_send_batch_with_client(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)

    class Client:
        def __init__(self):
            self.batches = []

        def send_message_batch(self, QueueUrl, Entries):
            self.batches.append((QueueUrl, Entries))
            return {"Successful": Entries}

    inst.client = Client()
    inst.queue_url = "https://example.com/queue"
    inst.sqs_enabled = True

    inst._send_batch([{"event_type": "a"}, {"event_type": "b"}])
    assert inst.client.batches


def test_retry_individual_spills_on_failure(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)

    class Client:
        def send_message(self, QueueUrl, MessageBody):
            raise RuntimeError("boom")

    inst.client = Client()
    inst.queue_url = "https://example.com/queue"
    inst.sqs_enabled = True

    inst._retry_individual([{"event_type": "a"}])
    with open(sqs.SPILLOVER_FILE, "r") as f:
        lines = f.readlines()
    assert lines


def test_retry_individual_with_no_client(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)
    inst.client = None
    inst.sqs_enabled = True

    called = {"init": False}

    def _auto_init():
        called["init"] = True

    inst._auto_initialize = _auto_init
    inst._retry_individual([{"event_type": "a"}])
    assert called["init"] is True


def test_load_spillover_requeues(monkeypatch, tmp_path):
    spill_path = tmp_path / "spillover.jsonl"
    spill_path.write_text(json.dumps({"event_type": "a"}) + "\n")

    monkeypatch.setattr(sqs, "SQS_WORKER_COUNT", 0)
    monkeypatch.setattr(sqs, "SPILLOVER_FILE", str(spill_path), raising=False)

    inst = sqs._LLMOpsObservabilitySQS()
    assert not os.path.exists(sqs.SPILLOVER_FILE)
    assert inst._q.qsize() >= 1


def test_load_spillover_skips_bad_json(monkeypatch, tmp_path):
    spill_path = tmp_path / "spillover.jsonl"
    spill_path.write_text("bad json\n")
    monkeypatch.setattr(sqs, "SQS_WORKER_COUNT", 0)
    monkeypatch.setattr(sqs, "SPILLOVER_FILE", str(spill_path), raising=False)
    inst = sqs._LLMOpsObservabilitySQS()
    assert inst._q.qsize() == 0


def test_worker_loop_shutdown_sentinel(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)
    inst._q.put(inst.SHUTDOWN_SENTINEL)
    inst._worker_loop()


def test_safe_worker_loop_recovers(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)
    calls = {"count": 0}

    def _boom_then_stop():
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("boom")
        return None

    monkeypatch.setattr(inst, "_worker_loop", _boom_then_stop)
    monkeypatch.setattr(sqs.time, "sleep", lambda _t: None)
    inst._safe_worker_loop()
    assert calls["count"] == 2


def test_force_flush_sends_batch(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)
    sent = []

    def _send_batch(batch):
        sent.append(list(batch))

    inst._send_batch = _send_batch
    inst._q.put({"event_type": "a"})
    inst._q.put(inst.SHUTDOWN_SENTINEL)
    inst.force_flush()
    assert sent


def test_shutdown_marks_shutting_down(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)
    inst.shutdown()
    assert inst._shutting_down is True


def test_public_wrappers(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)
    monkeypatch.setattr(sqs, "_sqs_instance", inst)
    assert sqs.send_to_sqs({"event_type": "x"}) is True
    assert sqs.send_to_sqs_immediate({"event_type": "y"}) in (True, False)
    assert sqs.flush_sqs() is None
    assert sqs.is_sqs_enabled() in (True, False)


def test_cleanup_at_exit(monkeypatch, tmp_path):
    inst = _make_instance(monkeypatch, tmp_path)
    monkeypatch.setattr(sqs, "_sqs_instance", inst)
    monkeypatch.setattr(sqs.os, "getpid", lambda: sqs.MAIN_PID)
    sqs._cleanup_at_exit()


# ============================================================
# Additional tests for improved branch coverage
# ============================================================

def test_cleanup_at_exit_not_main_pid(monkeypatch, tmp_path):
    """_cleanup_at_exit skips when not main process."""
    inst = _make_instance(monkeypatch, tmp_path)
    monkeypatch.setattr(sqs, "_sqs_instance", inst)
    # Return different PID than MAIN_PID
    monkeypatch.setattr(sqs.os, "getpid", lambda: sqs.MAIN_PID + 1)
    
    shutdown_called = {"called": False}
    original_shutdown = inst.shutdown
    def track_shutdown():
        shutdown_called["called"] = True
        original_shutdown()
    inst.shutdown = track_shutdown
    
    sqs._cleanup_at_exit()
    # Shutdown should NOT be called
    assert shutdown_called["called"] is False


def test_cleanup_at_exit_exception(monkeypatch, tmp_path):
    """_cleanup_at_exit handles exceptions gracefully."""
    inst = _make_instance(monkeypatch, tmp_path)
    monkeypatch.setattr(sqs, "_sqs_instance", inst)
    monkeypatch.setattr(sqs.os, "getpid", lambda: sqs.MAIN_PID)
    
    def boom_shutdown():
        raise RuntimeError("shutdown failed")
    inst.shutdown = boom_shutdown
    
    # Should not raise
    sqs._cleanup_at_exit()


def test_spillover_save_with_string_message(monkeypatch, tmp_path):
    """_spillover_save handles string messages."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    inst._spillover_save('{"event_type": "string_msg"}')
    
    with open(sqs.SPILLOVER_FILE, "r") as f:
        content = f.read()
    assert '{"event_type": "string_msg"}' in content


def test_spillover_save_exception(monkeypatch, tmp_path):
    """_spillover_save handles file write exception."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    # Set spillover file to an invalid path
    monkeypatch.setattr(sqs, "SPILLOVER_FILE", "/nonexistent/path/spillover.jsonl")
    
    # Should not raise, just log error
    inst._spillover_save({"event_type": "test"})


def test_load_spillover_exception(monkeypatch, tmp_path):
    """_load_spillover handles file read exception."""
    spill_path = tmp_path / "spillover.jsonl"
    spill_path.write_text('{"event_type": "a"}\n')
    
    monkeypatch.setattr(sqs, "SQS_WORKER_COUNT", 0)
    monkeypatch.setattr(sqs, "SPILLOVER_FILE", str(spill_path))
    
    # Make os.remove fail
    original_remove = os.remove
    def bad_remove(path):
        raise OSError("Cannot remove")
    monkeypatch.setattr(os, "remove", bad_remove)
    
    # Should not raise, but log error
    inst = sqs._LLMOpsObservabilitySQS()


def test_shutdown_already_shutting_down(monkeypatch, tmp_path):
    """shutdown does nothing if already shutting down."""
    inst = _make_instance(monkeypatch, tmp_path)
    inst._shutting_down = True
    
    # This should return immediately
    inst.shutdown()
    assert inst._shutting_down is True


def test_shutdown_thread_join_exception(monkeypatch, tmp_path):
    """shutdown handles thread join exception."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    # Create a mock worker thread that raises on join
    class BadThread:
        def join(self, timeout=None):
            raise RuntimeError("join failed")
    
    inst.workers = [BadThread()]
    inst.worker_count = 1
    
    # Should not raise
    inst.shutdown()
    assert inst._shutting_down is True


def test_worker_loop_event_loop_closed_error(monkeypatch, tmp_path):
    """_worker_loop handles 'Event loop is closed' RuntimeError."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    call_count = {"count": 0}
    
    def mock_send_batch(batch):
        call_count["count"] += 1
        raise RuntimeError("Event loop is closed")
    
    inst._send_batch = mock_send_batch
    
    # Put a message to trigger batch send
    inst._q.put({"event_type": "test"})
    
    # Worker should exit gracefully on Event loop closed
    inst._worker_loop()
    assert call_count["count"] == 1


def test_worker_loop_other_runtime_error(monkeypatch, tmp_path):
    """_worker_loop re-raises non-event-loop RuntimeErrors."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    def mock_send_batch(batch):
        raise RuntimeError("some other error")
    
    inst._send_batch = mock_send_batch
    inst._q.put({"event_type": "test"})
    
    with pytest.raises(RuntimeError, match="some other error"):
        inst._worker_loop()


def test_force_flush_get_exception(monkeypatch, tmp_path):
    """force_flush handles queue.get exception."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    class BadQueue:
        def empty(self):
            return False
        
        def get_nowait(self):
            raise RuntimeError("queue error")
    
    inst._q = BadQueue()
    
    # Should not raise
    inst.force_flush()


def test_send_message_none(monkeypatch, tmp_path):
    """send returns False for None message."""
    inst = _make_instance(monkeypatch, tmp_path)
    assert inst.send(None) is False


def test_send_immediate_message_none(monkeypatch, tmp_path):
    """send_immediate returns False for None message."""
    inst = _make_instance(monkeypatch, tmp_path)
    assert inst.send_immediate(None) is False


def test_send_immediate_spillover_with_string_message(monkeypatch, tmp_path):
    """send_immediate spills string message correctly."""
    inst = _make_instance(monkeypatch, tmp_path)
    inst.sqs_enabled = True
    inst.client = None
    
    ok = inst.send_immediate('{"trace_id": "t1"}')
    assert ok is False
    
    with open(sqs.SPILLOVER_FILE, "r") as f:
        content = f.read()
    assert "t1" in content


def test_send_immediate_spillover_with_invalid_json_string(monkeypatch, tmp_path):
    """send_immediate handles invalid JSON string during spillover."""
    inst = _make_instance(monkeypatch, tmp_path)
    inst.sqs_enabled = True
    inst.client = None
    
    # Pass a non-JSON string
    ok = inst.send_immediate("not valid json")
    assert ok is False
    
    # Should still save to spillover
    assert os.path.exists(sqs.SPILLOVER_FILE)


def test_send_immediate_extracts_trace_id_from_string(monkeypatch, tmp_path):
    """send_immediate extracts trace_id for logging from JSON string."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    class Client:
        def __init__(self):
            self.sent = []
        
        def send_message(self, QueueUrl, MessageBody):
            self.sent.append((QueueUrl, MessageBody))
            return {"MessageId": "ok"}
    
    inst.client = Client()
    inst.queue_url = "https://example.com/queue"
    inst.sqs_enabled = True
    
    # Send JSON string with trace_id
    ok = inst.send_immediate('{"trace_id": "trace123", "data": "test"}')
    assert ok is True


def test_send_immediate_failure_with_string_spills_dict(monkeypatch, tmp_path):
    """send_immediate converts valid JSON string to dict for spillover on failure."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    class Client:
        def send_message(self, QueueUrl, MessageBody):
            raise RuntimeError("send failed")
    
    inst.client = Client()
    inst.queue_url = "https://example.com/queue"
    inst.sqs_enabled = True
    
    ok = inst.send_immediate('{"event_type": "test_event"}')
    assert ok is False
    
    with open(sqs.SPILLOVER_FILE, "r") as f:
        content = f.read()
    assert "test_event" in content


def test_send_immediate_failure_with_invalid_json_string(monkeypatch, tmp_path):
    """send_immediate handles invalid JSON string on failure spillover."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    class Client:
        def send_message(self, QueueUrl, MessageBody):
            raise RuntimeError("send failed")
    
    inst.client = Client()
    inst.queue_url = "https://example.com/queue"
    inst.sqs_enabled = True
    
    ok = inst.send_immediate("not json")
    assert ok is False
    assert os.path.exists(sqs.SPILLOVER_FILE)


def test_send_batch_empty(monkeypatch, tmp_path):
    """_send_batch does nothing for empty batch."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    sent = {"called": False}
    def track_batch(*args, **kwargs):
        sent["called"] = True
    
    inst.client = MagicMock()
    inst.client.send_message_batch = track_batch
    
    inst._send_batch([])
    assert sent["called"] is False


def test_send_batch_exception_triggers_retry(monkeypatch, tmp_path):
    """_send_batch calls _retry_individual on exception."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    class Client:
        def send_message_batch(self, **kwargs):
            raise RuntimeError("batch failed")
        
        def send_message(self, **kwargs):
            return {"MessageId": "ok"}
    
    inst.client = Client()
    inst.queue_url = "https://example.com/queue"
    inst.sqs_enabled = True
    
    retried = {"called": False}
    original_retry = inst._retry_individual
    def track_retry(batch):
        retried["called"] = True
        original_retry(batch)
    inst._retry_individual = track_retry
    
    inst._send_batch([{"event_type": "a"}])
    assert retried["called"] is True


def test_retry_individual_success(monkeypatch, tmp_path):
    """_retry_individual sends messages individually."""
    inst = _make_instance(monkeypatch, tmp_path)
    
    class Client:
        def __init__(self):
            self.sent = []
        
        def send_message(self, QueueUrl, MessageBody):
            self.sent.append(MessageBody)
            return {"MessageId": "ok"}
    
    inst.client = Client()
    inst.queue_url = "https://example.com/queue"
    inst.sqs_enabled = True
    
    inst._retry_individual([{"event_type": "a"}, {"event_type": "b"}])
    assert len(inst.client.sent) == 2


def test_auto_initialize_already_initialized(monkeypatch, tmp_path):
    """_auto_initialize skips if already initialized with client."""
    inst = _make_instance(monkeypatch, tmp_path)
    inst._init_once = True
    inst.client = MagicMock()
    
    # Should return immediately without doing anything
    inst._auto_initialize()
    assert inst.client is not None


def test_is_sqs_enabled_triggers_auto_init(monkeypatch, tmp_path):
    """is_sqs_enabled triggers auto-initialization if not done."""
    inst = _make_instance(monkeypatch, tmp_path)
    inst._init_once = False
    monkeypatch.setattr(sqs, "_sqs_instance", inst)
    
    initialized = {"called": False}
    original_init = inst._auto_initialize
    def track_init():
        initialized["called"] = True
        original_init()
    inst._auto_initialize = track_init
    
    sqs.is_sqs_enabled()
    assert initialized["called"] is True


def test_send_triggers_auto_init(monkeypatch, tmp_path):
    """send triggers auto-initialization if SQS not enabled."""
    inst = _make_instance(monkeypatch, tmp_path)
    inst.sqs_enabled = False
    inst._init_once = False
    
    initialized = {"called": False}
    original_init = inst._auto_initialize
    def track_init():
        initialized["called"] = True
        original_init()
    inst._auto_initialize = track_init
    
    inst.send({"event_type": "test"})
    assert initialized["called"] is True


def test_send_immediate_triggers_auto_init(monkeypatch, tmp_path):
    """send_immediate triggers auto-initialization if SQS not enabled."""
    inst = _make_instance(monkeypatch, tmp_path)
    inst.sqs_enabled = False
    inst._init_once = False
    
    initialized = {"called": False}
    original_init = inst._auto_initialize
    def track_init():
        initialized["called"] = True
        original_init()
    inst._auto_initialize = track_init
    
    inst.send_immediate({"event_type": "test"})
    assert initialized["called"] is True


def test_send_batch_triggers_auto_init(monkeypatch, tmp_path):
    """_send_batch triggers auto-initialization if no client."""
    inst = _make_instance(monkeypatch, tmp_path)
    inst.client = None
    inst._init_once = False
    
    initialized = {"called": False}
    original_init = inst._auto_initialize
    def track_init():
        initialized["called"] = True
        original_init()
    inst._auto_initialize = track_init
    
    inst._send_batch([{"event_type": "test"}])
    assert initialized["called"] is True


# Import MagicMock for some tests
from unittest.mock import MagicMock
import pytest

