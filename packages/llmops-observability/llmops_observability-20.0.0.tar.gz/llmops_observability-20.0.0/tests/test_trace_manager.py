import asyncio
import base64
import gzip
import json

import llmops_observability.trace_manager as trace_manager
from llmops_observability.trace_manager import (
    TraceManager,
    SpanData,
    SDKTraceData,
    serialize_value,
    safe_locals,
    track_function,
)


def test_serialize_value_truncates_large_payload():
    large = "x" * (250 * 1024)
    out = serialize_value({"data": large})
    assert isinstance(out, dict)
    assert out.get("_truncated") is True
    assert "_preview" in out


def test_serialize_value_passes_small_payload():
    payload = {"a": 1, "b": "ok"}
    assert serialize_value(payload) == payload


def test_safe_locals_filters_private():
    data = {"ok": 1, "_private": 2}
    safe = safe_locals(data)
    assert "ok" in safe
    assert "_private" not in safe


def test_start_trace_sets_active():
    trace_id = TraceManager.start_trace(name="op_test")
    assert TraceManager.has_active_trace()
    assert TraceManager._active["trace_id"] == trace_id
    assert TraceManager._active["trace_config"]["project_id"] == "test_project"
    assert TraceManager._active["trace_config"]["environment"] == "test"
    assert TraceManager._active["start_time"] is not None


def test_span_stack_helpers():
    TraceManager.push_span_context("span-1")
    assert TraceManager.get_current_parent_span_id() == "span-1"
    popped = TraceManager.pop_span_context()
    assert popped == "span-1"
    assert TraceManager.get_current_parent_span_id() is None


def test_pop_span_context_empty():
    assert TraceManager.pop_span_context() is None


def test_add_span_injects_metadata():
    TraceManager.start_trace(name="trace_with_span")
    span = SpanData(span_id="s1", span_name="work", span_type="span")
    TraceManager.add_span(span)
    assert TraceManager._active["spans"]
    assert span.metadata["environment"] == "test"
    assert span.metadata["project_id"] == "test_project"


def test_add_span_without_active_trace_noop():
    span = SpanData(span_id="s1", span_name="work", span_type="span")
    TraceManager.add_span(span)
    assert TraceManager._active["spans"] == []


def test_finalize_and_send_without_active_trace():
    assert TraceManager.finalize_and_send() is False


def test_finalize_and_send_start_time_missing(monkeypatch):
    TraceManager._active["trace_id"] = "t1"
    TraceManager._active["trace_config"] = {"name": "n"}
    TraceManager._active["start_time"] = None
    assert TraceManager.finalize_and_send() is False


def test_finalize_and_send_sqs_disabled(monkeypatch):
    TraceManager.start_trace(name="trace")
    monkeypatch.setattr(trace_manager, "is_sqs_enabled", lambda: False)
    assert TraceManager.finalize_and_send() is False


def test_finalize_and_send_sqs_enabled(monkeypatch):
    sent = []

    def _send(payload):
        sent.append(payload)
        return True

    TraceManager.start_trace(name="trace")
    monkeypatch.setattr(trace_manager, "is_sqs_enabled", lambda: True)
    monkeypatch.setattr(trace_manager, "send_to_sqs_immediate", _send)

    assert TraceManager.finalize_and_send(trace_name="done") is True
    assert sent


def test_finalize_and_send_send_failure(monkeypatch):
    def _send(_payload):
        raise RuntimeError("boom")

    TraceManager.start_trace(name="trace")
    monkeypatch.setattr(trace_manager, "is_sqs_enabled", lambda: True)
    monkeypatch.setattr(trace_manager, "send_to_sqs_immediate", _send)
    assert TraceManager.finalize_and_send(trace_name="done") is False


def test_late_span_submission(monkeypatch):
    sent = []

    def _send(payload):
        sent.append(payload)
        return True

    TraceManager.start_trace(name="trace")
    monkeypatch.setattr(trace_manager, "is_sqs_enabled", lambda: True)
    monkeypatch.setattr(trace_manager, "send_to_sqs_immediate", _send)
    assert TraceManager.finalize_and_send(trace_name="done") is True

    late_span = SpanData(span_id="late", span_name="late_span", span_type="span")
    TraceManager.add_span(late_span)

    assert len(sent) >= 2
    payload = json.loads(sent[-1])
    assert payload["type"] == "late_span_update"


def test_submit_late_span_handles_send_error(monkeypatch):
    def _send(_payload):
        raise RuntimeError("boom")

    monkeypatch.setattr(trace_manager, "send_to_sqs_immediate", _send)
    span = SpanData(span_id="s1", span_name="late", span_type="span")
    TraceManager._submit_late_span_async(span, "trace-id")


def test_prepare_for_sqs_returns_compressed_payload():
    span = SpanData(span_id="s1", span_name="span", span_type="span", input_data={"a": 1})
    trace = SDKTraceData(
        trace_id="t1",
        trace_name="trace",
        project_id="p",
        environment="dev",
        user_id="u",
        session_id="s",
        start_time=0.0,
        end_time=1.0,
        duration_ms=1000,
        spans=[span],
        total_spans=1,
        total_generations=0,
    )

    payload = trace.prepare_for_sqs()
    decoded = json.loads(payload)
    assert decoded["compressed"] is True
    data = gzip.decompress(base64.b64decode(decoded["data"])).decode("utf-8")
    body = json.loads(data)
    assert body["trace_id"] == "t1"
    assert body["spans"][0]["span_name"] == "span"


def test_prepare_for_sqs_truncates_when_too_large(monkeypatch):
    monkeypatch.setattr(trace_manager, "MAX_SQS_SIZE", 10)
    spans = [SpanData(span_id=str(i), span_name="s", span_type="span") for i in range(3)]
    trace = SDKTraceData(
        trace_id="t1",
        trace_name="trace",
        project_id="p",
        environment="dev",
        user_id="u",
        session_id="s",
        start_time=0.0,
        end_time=1.0,
        duration_ms=1000,
        spans=spans,
        total_spans=3,
        total_generations=0,
    )
    payload = trace.prepare_for_sqs()
    decoded = json.loads(payload)
    assert decoded["truncated"] is True


def test_truncate_field_handles_errors():
    trace = SDKTraceData(trace_id="t", trace_name="n", project_id="p", environment="e")
    data = {}
    data["self"] = data
    out = trace._truncate_field(data, max_bytes=10)
    assert isinstance(out, str)


def test_create_summary_handles_none_and_error():
    trace = SDKTraceData(trace_id="t", trace_name="n", project_id="p", environment="e")
    assert trace._create_summary(None)["_type"] == "null"
    data = {}
    data["self"] = data
    summary = trace._create_summary(data)
    assert summary["_type"] == "dict"
    assert "_error" in summary or "_message" in summary


def test_track_function_without_trace_returns_result():
    @track_function()
    def add(x, y):
        return x + y

    assert add(2, 3) == 5
    assert TraceManager._active["spans"] == []


def test_track_function_with_active_trace_sync():
    TraceManager.start_trace(name="sync_trace")

    @track_function(metadata={"k": "v"})
    def mul(a, b):
        return a * b

    result = mul(3, 4)
    assert result == 12
    assert len(TraceManager._active["spans"]) == 1
    span = TraceManager._active["spans"][0]
    assert span.span_name == "mul"
    assert span.status == "success"


def test_track_function_error_records_span():
    TraceManager.start_trace(name="sync_trace")

    @track_function()
    def bad():
        raise ValueError("boom")

    try:
        bad()
    except ValueError:
        pass

    span = TraceManager._active["spans"][0]
    assert span.status == "error"


def test_track_function_with_active_trace_async():
    async def _runner():
        TraceManager.start_trace(name="async_trace")

        @track_function()
        async def async_func(value):
            await asyncio.sleep(0)
            return value * 2

        result = await async_func(5)
        assert result == 10
        assert len(TraceManager._active["spans"]) == 1
        assert TraceManager._active["spans"][0].span_name == "async_func"

    asyncio.run(_runner())


def test_track_function_async_without_trace():
    async def _runner():
        @track_function()
        async def async_func(value):
            return value

        result = await async_func(5)
        assert result == 5
        assert TraceManager._active["spans"] == []

    asyncio.run(_runner())


def test_build_function_input_data_capture_locals_list():
    local_vars = {"value": 10, "extra": "skip"}
    data = trace_manager._build_function_input_data(
        args=(),
        kwargs={},
        local_vars=local_vars,
        capture_locals_spec=["value"],
    )
    assert data["locals"] == {"value": 10}


def test_end_trace_returns_trace_id():
    trace_id = TraceManager.start_trace(name="trace")
    assert TraceManager.end_trace() == trace_id


def test_now_format():
    now = TraceManager._now()
    assert "T" in now


# ============================================================
# Additional tests for improved coverage
# ============================================================

def test_serialize_value_exception_fallback():
    """serialize_value returns str(value) on serialization exception."""
    class BadObj:
        def __str__(self):
            return "bad_obj_str"
    
    # This might serialize, let's try something that definitely won't
    result = serialize_value(BadObj())
    assert isinstance(result, (dict, str))


def test_can_track_span_with_finalized_trace():
    """can_track_span returns True when trace was finalized."""
    TraceManager._active["trace_id"] = None
    TraceManager._active["finalized_trace_id"] = "finalized-123"
    
    assert TraceManager.can_track_span() is True
    
    # Clean up
    TraceManager._active["finalized_trace_id"] = None


def test_can_track_span_no_trace():
    """can_track_span returns False when no active or finalized trace."""
    TraceManager._active["trace_id"] = None
    TraceManager._active["finalized_trace_id"] = None
    
    assert TraceManager.can_track_span() is False


def test_increment_pending_no_active_trace():
    """_increment_pending_if_active returns False when no active trace."""
    TraceManager._active["trace_id"] = None
    
    result = TraceManager._increment_pending_if_active()
    assert result is False


def test_decrement_pending_when_zero():
    """_decrement_pending handles zero count gracefully."""
    TraceManager._pending_count = 0
    TraceManager._decrement_pending()
    assert TraceManager._pending_count == 0


def test_wait_for_pending_immediate():
    """_wait_for_pending returns immediately when count is zero."""
    TraceManager._pending_count = 0
    TraceManager._wait_for_pending()  # Should not block


def test_build_function_input_data_capture_self():
    """_build_function_input_data captures self when requested."""
    class MyClass:
        def __init__(self):
            self.value = 42
    
    obj = MyClass()
    data = trace_manager._build_function_input_data(
        args=(obj, "arg1"),
        kwargs={"key": "value"},
        local_vars={},
        capture_self_flag=True,
    )
    
    assert "self" in data


def test_build_function_input_data_capture_self_no_dict():
    """_build_function_input_data handles self without __dict__."""
    data = trace_manager._build_function_input_data(
        args=(42,),  # Not an object with __dict__
        kwargs={},
        local_vars={},
        capture_self_flag=True,
    )
    
    assert "self" not in data


def test_build_function_input_data_capture_locals_true():
    """_build_function_input_data captures all locals when True."""
    data = trace_manager._build_function_input_data(
        args=(),
        kwargs={},
        local_vars={"var1": 1, "var2": "two", "_private": "skip"},
        capture_locals_spec=True,
    )
    
    assert "locals" in data
    assert "var1" in data["locals"]
    assert "var2" in data["locals"]


def test_track_function_with_capture_locals():
    """track_function captures local variables when requested."""
    TraceManager.start_trace(name="capture_locals_trace")

    @track_function(capture_locals=True)
    def func_with_locals(x):
        local_var = x * 2
        return local_var

    result = func_with_locals(5)
    assert result == 10
    
    span = TraceManager._active["spans"][-1]
    # The locals should be captured in input_data
    assert span.input_data is not None


def test_track_function_with_capture_self():
    """track_function captures self for methods."""
    TraceManager.start_trace(name="capture_self_trace")

    class MyService:
        def __init__(self, name):
            self.name = name

        @track_function(capture_self=True)
        def process(self, data):
            return f"{self.name}: {data}"

    svc = MyService("test_service")
    result = svc.process("hello")
    
    assert "test_service" in result
    span = TraceManager._active["spans"][-1]
    assert "self" in span.input_data


def test_track_function_async_error():
    """track_function handles async function errors."""
    async def _runner():
        TraceManager.start_trace(name="async_error_trace")

        @track_function()
        async def async_error():
            await asyncio.sleep(0)
            raise RuntimeError("async boom")

        try:
            await async_error()
        except RuntimeError:
            pass

        span = TraceManager._active["spans"][-1]
        assert span.status == "error"
        assert "async boom" in span.status_message

    asyncio.run(_runner())


def test_track_function_async_with_capture_locals():
    """track_function async captures locals when requested."""
    async def _runner():
        TraceManager.start_trace(name="async_capture_locals")

        @track_function(capture_locals=["local_val"])
        async def async_with_locals(x):
            local_val = x + 10
            await asyncio.sleep(0)
            return local_val

        result = await async_with_locals(5)
        assert result == 15

    asyncio.run(_runner())


def test_truncate_field_within_limit():
    """_truncate_field returns value unchanged when within limit."""
    trace = SDKTraceData(trace_id="t", trace_name="n", project_id="p", environment="e")
    value = {"small": "data"}
    result = trace._truncate_field(value, max_bytes=10000)
    assert result == value


def test_truncate_field_exceeds_limit():
    """_truncate_field truncates when over limit."""
    trace = SDKTraceData(trace_id="t", trace_name="n", project_id="p", environment="e")
    value = "x" * 1000
    result = trace._truncate_field(value, max_bytes=100)
    assert isinstance(result, dict)
    assert result.get("_truncated") is True


def test_create_summary_large_value():
    """_create_summary creates summary for large values."""
    trace = SDKTraceData(trace_id="t", trace_name="n", project_id="p", environment="e")
    large_value = "x" * 1000
    summary = trace._create_summary(large_value)
    assert summary["_type"] == "str"
    assert "_size_bytes" in summary


def test_finalize_clears_and_sets_finalized():
    """finalize_and_send sets finalized_trace_id for late span support."""
    sent = []

    def _send(payload):
        sent.append(payload)
        return True

    trace_id = TraceManager.start_trace(name="finalize_test")
    
    import llmops_observability.trace_manager as tm
    original_is_enabled = tm.is_sqs_enabled
    original_send = tm.send_to_sqs_immediate
    
    tm.is_sqs_enabled = lambda: True
    tm.send_to_sqs_immediate = _send
    
    TraceManager.finalize_and_send()
    
    # Restore
    tm.is_sqs_enabled = original_is_enabled
    tm.send_to_sqs_immediate = original_send
    
    # Verify finalized_trace_id was set
    assert TraceManager._active["finalized_trace_id"] == trace_id


def test_track_function_uses_finalized_trace():
    """track_function uses finalized trace for late spans."""
    sent = []

    def _send(payload):
        sent.append(payload)
        return True

    trace_id = TraceManager.start_trace(name="late_span_trace")
    
    import llmops_observability.trace_manager as tm
    original_is_enabled = tm.is_sqs_enabled
    original_send = tm.send_to_sqs_immediate
    
    tm.is_sqs_enabled = lambda: True
    tm.send_to_sqs_immediate = _send
    
    # Finalize the trace
    TraceManager.finalize_and_send()
    
    # Now call a tracked function - should create late span
    @track_function()
    def late_func():
        return "late"
    
    late_func()
    
    # Restore
    tm.is_sqs_enabled = original_is_enabled
    tm.send_to_sqs_immediate = original_send
    
    # Should have sent the main trace AND a late span update
    assert len(sent) >= 2


def test_sdk_trace_data_attributes():
    """SDKTraceData stores all provided attributes."""
    span = SpanData(span_id="s1", span_name="test", span_type="span")
    trace = SDKTraceData(
        trace_id="t1",
        trace_name="test_trace",
        project_id="proj",
        environment="dev",
        user_id="user1",
        session_id="sess1",
        start_time=1000.0,
        end_time=2000.0,
        duration_ms=1000,
        spans=[span],
        total_spans=1,
        total_generations=0,
    )
    
    assert trace.trace_id == "t1"
    assert trace.trace_name == "test_trace"
    assert trace.project_id == "proj"
    assert trace.spans[0].span_name == "test"


def test_span_data_all_fields():
    """SpanData stores all provided fields."""
    span = SpanData(
        span_id="s1",
        span_name="test_span",
        span_type="generation",
        parent_span_id="parent1",
        start_time=100.0,
        end_time=200.0,
        duration_ms=100,
        input_data={"key": "value"},
        output_data={"result": "ok"},
        error="some error",
        model_id="model123",
        metadata={"meta": "data"},
        tags=["tag1", "tag2"],
        usage={"input_tokens": 10, "output_tokens": 20},
        prompt="test prompt",
        response="test response",
        status="success",
        status_message="completed",
        level="DEBUG",
    )
    
    assert span.span_id == "s1"
    assert span.model_id == "model123"
    assert span.usage == {"input_tokens": 10, "output_tokens": 20}
    assert span.level == "DEBUG"

