"""
Comprehensive tests for bedrock_instrumentation module.
Tests all functions and branches for maximum coverage.
"""
import io
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from llmops_observability.bedrock_instrumentation import (
    get_captured_model_data,
    clear_captured_model_data,
    _instrument_bedrock_call,
    enable_bedrock_instrumentation,
    disable_bedrock_instrumentation,
    is_instrumentation_enabled,
    _bedrock_call_context,
)


class TestGetCapturedModelData:
    """Tests for get_captured_model_data function."""

    def test_returns_none_by_default(self):
        """Default context value should be None."""
        clear_captured_model_data()
        assert get_captured_model_data() is None

    def test_returns_stored_data(self):
        """Returns data that was stored in context."""
        test_data = {"model_id": "test-model", "request_body": {"prompt": "test"}}
        _bedrock_call_context.set(test_data)
        assert get_captured_model_data() == test_data
        clear_captured_model_data()


class TestClearCapturedModelData:
    """Tests for clear_captured_model_data function."""

    def test_clears_context(self):
        """Clears data from context."""
        _bedrock_call_context.set({"model_id": "test"})
        clear_captured_model_data()
        assert get_captured_model_data() is None


class TestIsInstrumentationEnabled:
    """Tests for is_instrumentation_enabled function."""

    def test_returns_false_by_default(self):
        """Instrumentation disabled by default in tests."""
        # Disable first to ensure clean state
        disable_bedrock_instrumentation()
        assert is_instrumentation_enabled() is False


class TestDisableBedrockInstrumentation:
    """Tests for disable_bedrock_instrumentation function."""

    def test_disables_instrumentation(self):
        """Sets the flag to False."""
        disable_bedrock_instrumentation()
        assert is_instrumentation_enabled() is False

    def test_can_be_called_multiple_times(self):
        """Safe to call multiple times."""
        disable_bedrock_instrumentation()
        disable_bedrock_instrumentation()
        assert is_instrumentation_enabled() is False


class TestEnableBedrockInstrumentation:
    """Tests for enable_bedrock_instrumentation function."""

    def test_enables_instrumentation(self):
        """Enables instrumentation successfully."""
        disable_bedrock_instrumentation()  # Reset state
        
        with patch('llmops_observability.bedrock_instrumentation.wrapt') as mock_wrapt:
            enable_bedrock_instrumentation()
            assert is_instrumentation_enabled() is True
            mock_wrapt.wrap_function_wrapper.assert_called_once()

    def test_skips_if_already_enabled(self):
        """Does nothing if already enabled."""
        # First enable
        with patch('llmops_observability.bedrock_instrumentation.wrapt'):
            enable_bedrock_instrumentation()
        
        # Try enabling again - should skip
        with patch('llmops_observability.bedrock_instrumentation.wrapt') as mock_wrapt:
            enable_bedrock_instrumentation()
            # Should not be called since already enabled
            mock_wrapt.wrap_function_wrapper.assert_not_called()
        
        disable_bedrock_instrumentation()

    def test_raises_on_failure(self):
        """Raises exception on wrapt failure."""
        disable_bedrock_instrumentation()
        
        with patch('llmops_observability.bedrock_instrumentation.wrapt') as mock_wrapt:
            mock_wrapt.wrap_function_wrapper.side_effect = Exception("wrapt failed")
            
            with pytest.raises(Exception, match="wrapt failed"):
                enable_bedrock_instrumentation()
        
        disable_bedrock_instrumentation()


class TestInstrumentBedrockCall:
    """Tests for _instrument_bedrock_call wrapper function."""

    def setup_method(self):
        """Clean up before each test."""
        clear_captured_model_data()
        disable_bedrock_instrumentation()

    def teardown_method(self):
        """Clean up after each test."""
        clear_captured_model_data()
        disable_bedrock_instrumentation()

    def test_passthrough_when_disabled(self):
        """Just calls wrapped function when instrumentation disabled."""
        wrapped = MagicMock(return_value={"result": "ok"})
        instance = MagicMock()
        
        result = _instrument_bedrock_call(wrapped, instance, ("InvokeModel",), {})
        
        wrapped.assert_called_once_with("InvokeModel")
        assert result == {"result": "ok"}

    def test_passthrough_for_non_bedrock_service(self):
        """Skips non-bedrock-runtime services."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        wrapped = MagicMock(return_value={"result": "ok"})
        instance = MagicMock()
        instance.meta.service_model.service_name = "s3"
        
        result = _instrument_bedrock_call(wrapped, instance, ("InvokeModel",), {})
        
        wrapped.assert_called_once()
        assert result == {"result": "ok"}

    def test_passthrough_for_non_invoke_operations(self):
        """Skips non-InvokeModel/Converse operations."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        wrapped = MagicMock(return_value={"result": "ok"})
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        result = _instrument_bedrock_call(wrapped, instance, ("ListModels",), {})
        
        wrapped.assert_called_once()
        assert result == {"result": "ok"}

    def test_captures_invoke_model_data(self):
        """Captures model_id, request, and response for InvokeModel."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        request_body = json.dumps({"prompt": "Hello"}).encode()
        response_body = json.dumps({"completion": "Hi there"}).encode()
        
        # Create mock streaming body
        mock_stream = MagicMock()
        mock_stream.read.return_value = response_body
        
        wrapped = MagicMock(return_value={"body": mock_stream})
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        api_params = {"modelId": "anthropic.claude-v2", "body": request_body}
        
        result = _instrument_bedrock_call(
            wrapped, instance, 
            ("InvokeModel", api_params), 
            {"api_params": api_params}
        )
        
        captured = get_captured_model_data()
        assert captured is not None
        assert captured["model_id"] == "anthropic.claude-v2"
        assert captured["operation"] == "InvokeModel"
        assert captured["request_body"] == {"prompt": "Hello"}
        assert captured["response_body"] == {"completion": "Hi there"}

    def test_captures_converse_api_data(self):
        """Captures data for Converse API."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        response = {
            "output": {"message": {"content": [{"text": "Response"}]}},
            "usage": {"inputTokens": 10, "outputTokens": 5}
        }
        
        wrapped = MagicMock(return_value=response)
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        system_prompts = [{"text": "You are helpful"}]
        api_params = {
            "modelId": "anthropic.claude-3-sonnet",
            "messages": messages,
            "system": system_prompts
        }
        
        result = _instrument_bedrock_call(
            wrapped, instance,
            ("Converse", api_params),
            {"api_params": api_params}
        )
        
        captured = get_captured_model_data()
        assert captured is not None
        assert captured["model_id"] == "anthropic.claude-3-sonnet"
        assert captured["operation"] == "Converse"
        assert captured["messages"] == messages
        assert captured["system"] == system_prompts
        assert captured["response_body"] is not None

    def test_handles_string_request_body(self):
        """Handles string request body."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        request_body = json.dumps({"prompt": "Hello"})  # String, not bytes
        response_body = json.dumps({"completion": "Hi"}).encode()
        
        mock_stream = MagicMock()
        mock_stream.read.return_value = response_body
        
        wrapped = MagicMock(return_value={"body": mock_stream})
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        api_params = {"modelId": "test-model", "body": request_body}
        
        _instrument_bedrock_call(
            wrapped, instance,
            ("InvokeModel", api_params),
            {"api_params": api_params}
        )
        
        captured = get_captured_model_data()
        assert captured is not None
        assert captured["request_body"] == {"prompt": "Hello"}

    def test_handles_invalid_request_body_bytes(self):
        """Handles non-JSON bytes in request body."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        request_body = b"not json"
        response_body = json.dumps({"result": "ok"}).encode()
        
        mock_stream = MagicMock()
        mock_stream.read.return_value = response_body
        
        wrapped = MagicMock(return_value={"body": mock_stream})
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        api_params = {"modelId": "test-model", "body": request_body}
        
        _instrument_bedrock_call(
            wrapped, instance,
            ("InvokeModel", api_params),
            {"api_params": api_params}
        )
        
        captured = get_captured_model_data()
        assert captured is not None
        assert captured["request_body"] is None  # Failed to parse

    def test_handles_invalid_request_body_string(self):
        """Handles non-JSON string in request body."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        request_body = "not json at all"
        response_body = json.dumps({"result": "ok"}).encode()
        
        mock_stream = MagicMock()
        mock_stream.read.return_value = response_body
        
        wrapped = MagicMock(return_value={"body": mock_stream})
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        api_params = {"modelId": "test-model", "body": request_body}
        
        _instrument_bedrock_call(
            wrapped, instance,
            ("InvokeModel", api_params),
            {"api_params": api_params}
        )
        
        captured = get_captured_model_data()
        assert captured is not None
        assert captured["request_body"] is None

    def test_handles_invalid_response_body(self):
        """Handles non-JSON response body."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        request_body = json.dumps({"prompt": "test"}).encode()
        
        mock_stream = MagicMock()
        mock_stream.read.return_value = b"not json response"
        
        wrapped = MagicMock(return_value={"body": mock_stream})
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        api_params = {"modelId": "test-model", "body": request_body}
        
        _instrument_bedrock_call(
            wrapped, instance,
            ("InvokeModel", api_params),
            {"api_params": api_params}
        )
        
        captured = get_captured_model_data()
        assert captured is not None
        assert captured["response_body"] is None

    def test_handles_wrapped_exception(self):
        """Falls back to original call on exception."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        # First call raises, second call returns normally
        wrapped = MagicMock()
        wrapped.side_effect = [Exception("API error"), {"result": "fallback"}]
        
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        api_params = {"modelId": "test-model", "body": b"{}"}
        
        result = _instrument_bedrock_call(
            wrapped, instance,
            ("InvokeModel", api_params),
            {"api_params": api_params}
        )
        
        assert result == {"result": "fallback"}

    def test_restores_streaming_body(self):
        """Restores StreamingBody so downstream can read it."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        response_content = json.dumps({"completion": "test"}).encode()
        
        mock_stream = MagicMock()
        mock_stream.read.return_value = response_content
        
        wrapped = MagicMock(return_value={"body": mock_stream})
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        api_params = {"modelId": "test-model", "body": b"{}"}
        
        result = _instrument_bedrock_call(
            wrapped, instance,
            ("InvokeModel", api_params),
            {"api_params": api_params}
        )
        
        # Verify body was restored and can be read
        assert "body" in result
        restored_content = result["body"].read()
        assert restored_content == response_content

    def test_handles_converse_non_dict_response(self):
        """Handles Converse API with non-dict response."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        # Return a non-dict response
        wrapped = MagicMock(return_value="string response")
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        api_params = {"modelId": "test-model"}
        
        result = _instrument_bedrock_call(
            wrapped, instance,
            ("Converse", api_params),
            {"api_params": api_params}
        )
        
        captured = get_captured_model_data()
        assert captured is not None
        assert captured["response_body"] is None

    def test_extracts_params_from_args(self):
        """Extracts api_params from positional args when not in kwargs."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        response_body = json.dumps({"result": "ok"}).encode()
        mock_stream = MagicMock()
        mock_stream.read.return_value = response_body
        
        wrapped = MagicMock(return_value={"body": mock_stream})
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        api_params = {"modelId": "from-args-model", "body": b"{}"}
        
        # Pass params as second positional arg, not in kwargs
        _instrument_bedrock_call(
            wrapped, instance,
            ("InvokeModel", api_params),
            {}  # Empty kwargs
        )
        
        captured = get_captured_model_data()
        assert captured is not None
        assert captured["model_id"] == "from-args-model"

    def test_handles_no_body_in_request(self):
        """Handles request without body field."""
        import llmops_observability.bedrock_instrumentation as bi
        bi._instrumentation_enabled = True
        
        response = {"output": {"message": {"content": [{"text": "Hi"}]}}}
        wrapped = MagicMock(return_value=response)
        instance = MagicMock()
        instance.meta.service_model.service_name = "bedrock-runtime"
        
        # No body in params
        api_params = {"modelId": "test-model", "messages": []}
        
        _instrument_bedrock_call(
            wrapped, instance,
            ("Converse", api_params),
            {"api_params": api_params}
        )
        
        captured = get_captured_model_data()
        assert captured is not None
        assert captured["request_body"] is None


class TestInstrumentationIntegration:
    """Integration tests for the instrumentation workflow."""

    def setup_method(self):
        """Reset state before each test."""
        clear_captured_model_data()
        disable_bedrock_instrumentation()

    def teardown_method(self):
        """Clean up after tests."""
        clear_captured_model_data()
        disable_bedrock_instrumentation()

    def test_full_workflow(self):
        """Tests enable -> capture -> clear workflow."""
        # Enable instrumentation
        with patch('llmops_observability.bedrock_instrumentation.wrapt'):
            enable_bedrock_instrumentation()
        
        assert is_instrumentation_enabled() is True
        
        # Simulate captured data
        _bedrock_call_context.set({
            "model_id": "test-model",
            "operation": "InvokeModel",
            "request_body": {"prompt": "test"},
            "response_body": {"completion": "response"}
        })
        
        # Verify data is captured
        data = get_captured_model_data()
        assert data["model_id"] == "test-model"
        
        # Clear data
        clear_captured_model_data()
        assert get_captured_model_data() is None
        
        # Disable
        disable_bedrock_instrumentation()
        assert is_instrumentation_enabled() is False
