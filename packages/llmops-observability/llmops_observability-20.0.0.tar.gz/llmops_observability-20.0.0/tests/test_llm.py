import asyncio

import llmops_observability.llm as llm
from llmops_observability.llm import (
    extract_text,
    extract_usage,
    extract_model_id,
    track_llm_call,
)
from llmops_observability.trace_manager import TraceManager


def test_extract_text_handles_multiple_formats():
    assert extract_text("hello") == "hello"
    assert extract_text(123) == "123"

    bedrock = {"output": {"message": {"content": [{"text": "bedrock"}]}}}
    assert extract_text(bedrock) == "bedrock"

    anthropic = {"content": [{"text": "anthropic"}]}
    assert extract_text(anthropic) == "anthropic"

    titan = {"results": [{"outputText": "titan"}]}
    assert extract_text(titan) == "titan"

    cohere = {"generation": "cohere"}
    assert extract_text(cohere) == "cohere"

    ai21 = {"outputs": [{"text": "ai21"}]}
    assert extract_text(ai21) == "ai21"

    generic = {"text": "generic"}
    assert extract_text(generic) == "generic"

    openai = {"choices": [{"message": {"content": "openai"}}]}
    assert extract_text(openai) == "openai"


def test_extract_usage_from_result_usage_object():
    class Usage:
        def __init__(self):
            self.prompt_tokens = 10
            self.completion_tokens = 20
            self.total_tokens = 30

    class Result:
        def __init__(self):
            self.usage = Usage()

    usage = extract_usage(Result(), {})
    assert usage == {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}


def test_extract_usage_from_bedrock_dict():
    resp = {"usage": {"inputTokens": 5, "outputTokens": 7, "totalTokens": 12}}
    usage = extract_usage(resp, {})
    assert usage == {"input_tokens": 5, "output_tokens": 7, "total_tokens": 12}


def test_extract_usage_fallback_estimate():
    usage = extract_usage({}, {}, prompt="hello", response_text="world")
    assert usage["total_tokens"] >= 0


def test_estimate_tokens_handles_none_and_errors():
    assert llm._estimate_tokens(None) == 0

    class BadStr:
        def __str__(self):
            raise RuntimeError("boom")

    assert llm._estimate_tokens(BadStr()) == 0


def test_build_input_data_captures_locals_list():
    args = (1, 2)
    kwargs = {"k": "v"}
    local_vars = {"keep": 1, "drop": 2, "_private": 3}
    data = llm._build_input_data(args, kwargs, local_vars, capture_locals_spec=["keep"])
    assert data["locals"] == {"keep": 1}


def test_extract_model_id_from_kwargs_and_result():
    assert extract_model_id({}, {"model": "m1"}) == "m1"
    assert extract_model_id({}, {"modelId": "m2"}) == "m2"

    result = {"model": "m3"}
    assert extract_model_id(result, {}) == "m3"

    class ModelObj:
        def __init__(self):
            self.model = "m4"

    assert extract_model_id(ModelObj(), {}) == "m4"


def test_track_llm_call_without_active_trace_returns_raw_result():
    @track_llm_call()
    def llm_call(prompt: str):
        return {"output": {"message": {"content": [{"text": "resp"}]}}}

    result = llm_call("hi")
    assert result["output"]["message"]["content"][0]["text"] == "resp"
    assert TraceManager._active["spans"] == []


def test_track_llm_call_with_active_trace_sync():
    TraceManager.start_trace(name="llm_trace")

    @track_llm_call(model="test-model", metadata={"m": "v"})
    def llm_call(prompt: str):
        return {
            "output": {"message": {"content": [{"text": "resp"}]}},
            "usage": {"inputTokens": 10, "outputTokens": 20, "totalTokens": 30},
        }

    result = llm_call("hi")
    assert "output" in result
    assert TraceManager._active["spans"]
    span = TraceManager._active["spans"][-1]
    assert span.model_id == "test-model"
    assert span.status == "success"


def test_track_llm_call_capture_self():
    TraceManager.start_trace(name="llm_trace_self")

    class Client:
        def __init__(self, name):
            self.name = name

        @track_llm_call(capture_self=True)
        def call(self, prompt: str):
            return {"choices": [{"message": {"content": "ok"}}]}

    client = Client("c1")
    result = client.call("hello")
    assert result["choices"][0]["message"]["content"] == "ok"
    span = TraceManager._active["spans"][-1]
    assert "self" in span.input_data


def test_track_llm_call_with_active_trace_async():
    async def _runner():
        TraceManager.start_trace(name="llm_trace_async")

        @track_llm_call()
        async def async_llm(prompt: str):
            await asyncio.sleep(0)
            return {"choices": [{"message": {"content": "ok"}}]}

        result = await async_llm("hello")
        assert result["choices"][0]["message"]["content"] == "ok"
        assert TraceManager._active["spans"]

    asyncio.run(_runner())


def test_track_llm_call_error_records_span():
    TraceManager.start_trace(name="llm_trace_error")

    @track_llm_call()
    def llm_call(prompt: str):
        raise ValueError("bad")

    try:
        llm_call("hi")
    except ValueError:
        pass

    span = TraceManager._active["spans"][-1]
    assert span.status == "error"


# ============================================================
# Additional tests for improved coverage
# ============================================================

def test_extract_text_fallback_to_str_for_unknown_dict():
    """extract_text falls back to str() for unknown dict format."""
    unknown = {"unknown_format": "value"}
    result = extract_text(unknown)
    # Should return string representation since no format matched
    assert "unknown_format" in result


def test_extract_usage_returns_none_for_empty_usage_object():
    """extract_usage returns None when usage object has no attributes."""
    class EmptyUsage:
        pass

    class Result:
        def __init__(self):
            self.usage = EmptyUsage()

    usage = extract_usage(Result(), {})
    assert usage is None


def test_extract_usage_partial_attributes():
    """extract_usage handles usage object with only some attributes."""
    class PartialUsage:
        def __init__(self):
            self.prompt_tokens = 10
            # No completion_tokens or total_tokens

    class Result:
        def __init__(self):
            self.usage = PartialUsage()

    usage = extract_usage(Result(), {})
    assert usage == {"input_tokens": 10}


def test_extract_usage_bedrock_partial_tokens():
    """extract_usage handles Bedrock with only some token fields."""
    resp = {"usage": {"inputTokens": 5}}  # No outputTokens or totalTokens
    usage = extract_usage(resp, {})
    assert usage == {"input_tokens": 5}


def test_extract_usage_returns_none_when_no_usage():
    """extract_usage returns None when no usage info available."""
    usage = extract_usage({}, {})
    assert usage is None


def test_extract_model_id_from_model_id_kwarg():
    """extract_model_id checks model_id kwarg."""
    model = extract_model_id({}, {"model_id": "my-model"})
    assert model == "my-model"


def test_extract_model_id_from_result_modelId():
    """extract_model_id from result dict with modelId key."""
    result = {"modelId": "result-model-id"}
    model = extract_model_id(result, {})
    assert model == "result-model-id"


def test_extract_model_id_returns_none_when_not_found():
    """extract_model_id returns None when no model info."""
    model = extract_model_id({}, {})
    assert model is None


def test_extract_model_id_from_bedrock_instrumentation(monkeypatch):
    """extract_model_id uses auto-captured Bedrock data."""
    # Mock the bedrock instrumentation functions
    monkeypatch.setattr(llm, "BEDROCK_INSTRUMENTATION_AVAILABLE", True)
    monkeypatch.setattr(llm, "get_captured_model_data", lambda: {"model_id": "captured-model"})
    
    model = extract_model_id({}, {})
    assert model == "captured-model"


def test_extract_model_id_bedrock_capture_no_model_id(monkeypatch):
    """extract_model_id handles captured data without model_id."""
    monkeypatch.setattr(llm, "BEDROCK_INSTRUMENTATION_AVAILABLE", True)
    monkeypatch.setattr(llm, "get_captured_model_data", lambda: {"operation": "InvokeModel"})
    
    model = extract_model_id({}, {"model": "fallback-model"})
    assert model == "fallback-model"


def test_build_input_data_capture_locals_true():
    """_build_input_data captures all locals when capture_locals=True."""
    args = ()
    kwargs = {}
    local_vars = {"var1": "value1", "var2": 42, "_private": "skip"}
    
    data = llm._build_input_data(args, kwargs, local_vars, capture_locals_spec=True)
    
    assert "locals" in data
    assert "var1" in data["locals"]
    assert "var2" in data["locals"]
    # Private vars should be filtered by safe_locals


def test_build_input_data_capture_self_no_dict():
    """_build_input_data handles self without __dict__."""
    args = (42,)  # First arg is not an object with __dict__
    kwargs = {}
    
    data = llm._build_input_data(args, kwargs, None, capture_locals_spec=False, capture_self_flag=True)
    
    # Should not crash, and self should not be in data
    assert "self" not in data


def test_build_input_data_capture_self_with_exception(monkeypatch):
    """_build_input_data handles exception during self serialization."""
    from llmops_observability.trace_manager import serialize_value
    
    class BadObj:
        def __init__(self):
            self.value = "test"
    
    # Mock serialize_value to raise an exception
    original_serialize = llm.serialize_value
    def bad_serialize(obj):
        if isinstance(obj, BadObj):
            raise RuntimeError("Cannot serialize")
        return original_serialize(obj)
    
    monkeypatch.setattr(llm, "serialize_value", bad_serialize)
    
    args = (BadObj(),)
    kwargs = {}
    
    # Should not raise, just skip self
    data = llm._build_input_data(args, kwargs, None, capture_locals_spec=False, capture_self_flag=True)
    # self should not be in data because serialization failed
    assert "self" not in data


def test_track_llm_call_extracts_prompt_from_kwargs():
    """track_llm_call extracts prompt from kwargs."""
    TraceManager.start_trace(name="prompt_kwargs_trace")

    @track_llm_call()
    def llm_call(**kwargs):
        return {"text": "response"}

    result = llm_call(prompt="my prompt here")
    span = TraceManager._active["spans"][-1]
    assert span.prompt == "my prompt here"


def test_track_llm_call_extracts_messages_from_kwargs():
    """track_llm_call extracts messages from kwargs when no prompt."""
    TraceManager.start_trace(name="messages_kwargs_trace")

    @track_llm_call()
    def llm_call(**kwargs):
        return {"text": "response"}

    messages = [{"role": "user", "content": "hello"}]
    result = llm_call(messages=messages)
    span = TraceManager._active["spans"][-1]
    # prompt contains the serialized messages list
    assert span.prompt is not None
    assert "user" in str(span.prompt)  # Messages content is in the prompt


def test_track_llm_call_uses_metadata_model():
    """track_llm_call uses model from metadata if not in direct param."""
    TraceManager.start_trace(name="metadata_model_trace")

    @track_llm_call(metadata={"model": "metadata-model"})
    def llm_call():
        return {"text": "response"}

    result = llm_call()
    span = TraceManager._active["spans"][-1]
    assert span.model_id == "metadata-model"


def test_track_llm_call_no_usage_triggers_fallback():
    """track_llm_call uses fallback estimation when no usage in response."""
    TraceManager.start_trace(name="fallback_usage_trace")

    @track_llm_call()
    def llm_call(prompt):
        return {"text": "simple response without usage"}

    result = llm_call("test prompt")
    span = TraceManager._active["spans"][-1]
    # Usage should be estimated based on prompt and response
    assert span.usage is not None
    assert span.usage["total_tokens"] >= 0


def test_track_llm_call_async_error():
    """track_llm_call handles async function errors."""
    async def _runner():
        TraceManager.start_trace(name="async_error_trace")

        @track_llm_call()
        async def async_llm():
            await asyncio.sleep(0)
            raise RuntimeError("async error")

        try:
            await async_llm()
        except RuntimeError:
            pass

        span = TraceManager._active["spans"][-1]
        assert span.status == "error"
        assert "async error" in span.status_message

    asyncio.run(_runner())


def test_track_llm_call_async_without_trace():
    """track_llm_call async returns raw result when no active trace."""
    async def _runner():
        # Clear any active trace
        TraceManager._active["spans"] = []
        TraceManager._active["trace_id"] = None

        @track_llm_call()
        async def async_llm():
            return {"result": "ok"}

        result = await async_llm()
        assert result == {"result": "ok"}

    asyncio.run(_runner())


def test_track_llm_call_clears_bedrock_data(monkeypatch):
    """track_llm_call clears bedrock captured data after use."""
    cleared = {"called": False}
    
    def mock_clear():
        cleared["called"] = True
    
    monkeypatch.setattr(llm, "BEDROCK_INSTRUMENTATION_AVAILABLE", True)
    monkeypatch.setattr(llm, "clear_captured_model_data", mock_clear)
    monkeypatch.setattr(llm, "get_captured_model_data", lambda: None)
    
    TraceManager.start_trace(name="clear_bedrock_trace")

    @track_llm_call()
    def llm_call():
        return {"text": "response"}

    llm_call()
    assert cleared["called"] is True


def test_ensure_instrumentation_enabled_auto_enables(monkeypatch):
    """_ensure_instrumentation_enabled auto-enables if available."""
    enabled = {"called": False}
    
    def mock_enable():
        enabled["called"] = True
    
    monkeypatch.setattr(llm, "BEDROCK_INSTRUMENTATION_AVAILABLE", True)
    monkeypatch.setattr(llm, "enable_bedrock_instrumentation", mock_enable)
    monkeypatch.setattr(llm, "is_instrumentation_enabled", lambda: False)
    
    llm._ensure_instrumentation_enabled()
    assert enabled["called"] is True


def test_ensure_instrumentation_skips_if_already_enabled(monkeypatch):
    """_ensure_instrumentation_enabled skips if already enabled."""
    enabled = {"called": False}
    
    def mock_enable():
        enabled["called"] = True
    
    monkeypatch.setattr(llm, "BEDROCK_INSTRUMENTATION_AVAILABLE", True)
    monkeypatch.setattr(llm, "enable_bedrock_instrumentation", mock_enable)
    monkeypatch.setattr(llm, "is_instrumentation_enabled", lambda: True)
    
    llm._ensure_instrumentation_enabled()
    assert enabled["called"] is False


def test_ensure_instrumentation_handles_exception(monkeypatch):
    """_ensure_instrumentation_enabled handles enable exception gracefully."""
    def mock_enable():
        raise RuntimeError("Failed to enable")
    
    monkeypatch.setattr(llm, "BEDROCK_INSTRUMENTATION_AVAILABLE", True)
    monkeypatch.setattr(llm, "enable_bedrock_instrumentation", mock_enable)
    monkeypatch.setattr(llm, "is_instrumentation_enabled", lambda: False)
    
    # Should not raise
    llm._ensure_instrumentation_enabled()
