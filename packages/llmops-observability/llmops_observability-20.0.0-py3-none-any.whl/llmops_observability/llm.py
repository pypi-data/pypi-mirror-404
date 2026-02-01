"""
LLM tracking decorator for LLMOps Observability
Simplified version that collects data into SDKTraceData
"""
from __future__ import annotations
import functools
import inspect
import time
import uuid
import logging
from typing import Optional, Dict, Any, List, Union

from .trace_manager import TraceManager, serialize_value, SpanData, safe_locals

logger = logging.getLogger(__name__)

# Import bedrock instrumentation for auto-capture
try:
    from .bedrock_instrumentation import (
        get_captured_model_data, 
        clear_captured_model_data,
        enable_bedrock_instrumentation,
        is_instrumentation_enabled
    )
    BEDROCK_INSTRUMENTATION_AVAILABLE = True
except ImportError:
    BEDROCK_INSTRUMENTATION_AVAILABLE = False
    get_captured_model_data = None
    clear_captured_model_data = None
    enable_bedrock_instrumentation = None
    is_instrumentation_enabled = None


def _ensure_instrumentation_enabled():
    """Auto-enable Bedrock instrumentation on first use."""
    if BEDROCK_INSTRUMENTATION_AVAILABLE and enable_bedrock_instrumentation and is_instrumentation_enabled:
        if not is_instrumentation_enabled():
            try:
                enable_bedrock_instrumentation()
                logger.debug("Bedrock instrumentation auto-enabled")
            except Exception as e:
                logger.debug(f"Failed to auto-enable Bedrock instrumentation: {e}")


def extract_text(resp: Any) -> str:
    """Extract text from various LLM response formats."""
    if isinstance(resp, str):
        return resp

    if not isinstance(resp, dict):
        return str(resp)

    # Bedrock Converse API
    try:
        return resp["output"]["message"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        pass

    # Anthropic Messages API
    try:
        return resp["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        pass

    # Amazon Titan
    try:
        return resp["results"][0]["outputText"]
    except (KeyError, IndexError, TypeError):
        pass

    # Cohere
    try:
        return resp["generation"]
    except (KeyError, TypeError):
        pass

    # AI21
    try:
        return resp["outputs"][0]["text"]
    except (KeyError, IndexError, TypeError):
        pass

    # Generic text field
    try:
        return resp["text"]
    except (KeyError, TypeError):
        pass

    # OpenAI format
    try:
        return resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        pass

    return str(resp)


def _estimate_tokens(text: Optional[str]) -> int:
    """Approximate tokens when provider doesn't return usage."""
    if not text:
        return 0
    try:
        return max(0, int(len(str(text)) / 4))
    except Exception:
        return 0


def _build_input_data(
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


def _extract_prompt_from_captured(captured: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract prompt from Bedrock captured payloads."""
    if not captured:
        return None

    messages = captured.get("messages")
    if messages:
        return str(messages)

    request_body = captured.get("request_body")
    if isinstance(request_body, dict):
        for key in ("prompt", "inputText", "input", "text"):
            if key in request_body and request_body[key] is not None:
                return str(request_body[key])
        if "messages" in request_body and request_body["messages"] is not None:
            return str(request_body["messages"])

    return None


def extract_usage(result: Any, kwargs: Dict[str, Any], *, prompt: Optional[str] = None, response_text: Optional[str] = None) -> Optional[Dict[str, int]]:
    """Extract token usage from LLM response."""
    usage = {}

    # Check auto-captured Bedrock response data first
    if BEDROCK_INSTRUMENTATION_AVAILABLE and get_captured_model_data:
        captured = get_captured_model_data()
        if captured and isinstance(captured.get("response_body"), dict):
            resp = captured["response_body"]
            if "usage" in resp and isinstance(resp["usage"], dict):
                usage_data = resp["usage"]
                if "inputTokens" in usage_data:
                    usage["input_tokens"] = usage_data["inputTokens"]
                if "outputTokens" in usage_data:
                    usage["output_tokens"] = usage_data["outputTokens"]
                if "totalTokens" in usage_data:
                    usage["total_tokens"] = usage_data["totalTokens"]
                if usage:
                    return usage
    
    # Check if result has usage attribute (OpenAI, Anthropic)
    if hasattr(result, 'usage'):
        usage_obj = result.usage
        if hasattr(usage_obj, 'prompt_tokens'):
            usage['input_tokens'] = usage_obj.prompt_tokens
        if hasattr(usage_obj, 'completion_tokens'):
            usage['output_tokens'] = usage_obj.completion_tokens
        if hasattr(usage_obj, 'total_tokens'):
            usage['total_tokens'] = usage_obj.total_tokens
        return usage if usage else None
    
    # Check Bedrock response format
    if isinstance(result, dict):
        # Bedrock Converse API
        if 'usage' in result:
            usage_data = result['usage']
            if 'inputTokens' in usage_data:
                usage['input_tokens'] = usage_data['inputTokens']
            if 'outputTokens' in usage_data:
                usage['output_tokens'] = usage_data['outputTokens']
            if 'totalTokens' in usage_data:
                usage['total_tokens'] = usage_data['totalTokens']
            return usage if usage else None
    
    # Fallback estimate
    if prompt is not None or response_text is not None:
        inp = _estimate_tokens(prompt)
        out = _estimate_tokens(response_text)
        return {"input_tokens": inp, "output_tokens": out, "total_tokens": inp + out}
    return None


def extract_model_id(result: Any, kwargs: Dict[str, Any]) -> Optional[str]:
    """
    Extract model ID from LLM response or kwargs.
    
    Priority order:
    1. Auto-captured from Bedrock instrumentation (if enabled)
    2. Function kwargs (model, modelId, model_id)
    3. Result dict or attributes
    """
    # 1. Try auto-captured data from Bedrock instrumentation
    if BEDROCK_INSTRUMENTATION_AVAILABLE and get_captured_model_data:
        captured = get_captured_model_data()
        if captured and captured.get('model_id'):
            return captured['model_id']
    
    # 2. Check kwargs
    if 'model' in kwargs:
        return kwargs['model']
    if 'modelId' in kwargs:
        return kwargs['modelId']
    if 'model_id' in kwargs:
        return kwargs['model_id']
    
    # 3. Check result
    if isinstance(result, dict):
        if 'model' in result:
            return str(result['model'])
        if 'modelId' in result:
            return str(result['modelId'])
    
    if hasattr(result, 'model'):
        return str(getattr(result, 'model', None))
    
    return None


def track_llm_call(
    name: Optional[str] = None,
    *,
    model: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    capture_locals: Union[bool, List[str]] = False,
    capture_self: bool = False,
):
    """
    Decorator to track LLM calls.
    
    Usage:
        @track_llm_call()
        def call_llm(prompt):
            return response
            
        @track_llm_call(name="summarize", model="claude-3-sonnet", metadata={"version": "1.0"})
        async def summarize(text):
            return summary
        
        @track_llm_call(capture_locals=True)
        def track_with_locals(prompt, max_tokens):
            # capture_locals=True captures all local variables
            return response
    
    Args:
        name: Optional custom name
        model: Optional model ID (will be prioritized over auto-detection)
        metadata: Optional metadata
        capture_locals: Capture function local variables (bool or list of var names)
        capture_self: Capture 'self' parameter (for methods)
    """
    def decorator(func):
        # Auto-enable instrumentation on first use
        _ensure_instrumentation_enabled()
        
        span_name = name or func.__name__
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not TraceManager.has_active_trace():
                    # No trace - just execute function
                    return await func(*args, **kwargs)

                pending_added = TraceManager._increment_pending_if_active()
                
                span_id = str(uuid.uuid4())
                parent_span_id = TraceManager.get_current_parent_span_id()
                start_time = time.time()
                
                # Push span context for nesting
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
                    
                    # Pop span context
                    TraceManager.pop_span_context()
                    
                    # Extract LLM-specific data
                    prompt = None
                    response = None
                    usage = None
                    model_id_final = None
                    local_vars_for_prompt = None
                    
                    if not error and result:
                        try:
                            response = extract_text(result)

                            # Capture locals for prompt extraction (no logging unless capture_locals enabled)
                            try:
                                frame = inspect.currentframe()
                                if frame and frame.f_back:
                                    local_vars_for_prompt = frame.f_back.f_locals.copy()
                            except Exception:
                                local_vars_for_prompt = None

                            if BEDROCK_INSTRUMENTATION_AVAILABLE and get_captured_model_data:
                                prompt = _extract_prompt_from_captured(get_captured_model_data())
                            usage = extract_usage(result, kwargs, prompt=prompt, response_text=response)
                            # Prioritize: explicit model param > metadata['model'] > auto-extract
                            model_id_final = model or (metadata.get('model') if metadata and 'model' in metadata else None) or extract_model_id(result, kwargs)
                        except Exception:
                            pass
                    
                    # Create span data
                    # Capture local variables if needed
                    local_vars = {}
                    if capture_locals or capture_self:
                        try:
                            frame = inspect.currentframe()
                            if frame and frame.f_back:
                                local_vars = frame.f_back.f_locals.copy()
                        except Exception:
                            pass
                    
                    input_payload = {"input": prompt} if prompt else _build_input_data(
                        args, kwargs, local_vars, capture_locals, capture_self
                    )

                    span_data = SpanData(
                        span_id=span_id,
                        span_name=span_name,
                        span_type="generation",  # LLM calls are generations
                        parent_span_id=parent_span_id,
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                        input_data=input_payload,
                        output_data=serialize_value(result) if not error else None,
                        error=str(error) if error else None,
                        model_id=model_id_final,
                        metadata=metadata or {},
                        usage=usage,
                        prompt=prompt,
                        response=response,
                        status="error" if error else "success",
                        status_message=str(error) if error else None,
                    )
                    
                    # Add to trace
                    TraceManager.add_span(span_data)

                    if pending_added:
                        TraceManager._decrement_pending()
                    
                    # Clear auto-captured data after use
                    if BEDROCK_INSTRUMENTATION_AVAILABLE and clear_captured_model_data:
                        clear_captured_model_data()
            
            return async_wrapper
        
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not TraceManager.has_active_trace():
                    # No trace - just execute function
                    return func(*args, **kwargs)

                pending_added = TraceManager._increment_pending_if_active()
                
                span_id = str(uuid.uuid4())
                parent_span_id = TraceManager.get_current_parent_span_id()
                start_time = time.time()
                
                # Push span context for nesting
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
                    
                    # Pop span context
                    TraceManager.pop_span_context()
                    
                    # Extract LLM-specific data
                    prompt = None
                    response = None
                    usage = None
                    model_id_final = None
                    local_vars_for_prompt = None
                    
                    if not error and result:
                        try:
                            response = extract_text(result)

                            # Capture locals for prompt extraction (no logging unless capture_locals enabled)
                            try:
                                frame = inspect.currentframe()
                                if frame and frame.f_back:
                                    local_vars_for_prompt = frame.f_back.f_locals.copy()
                            except Exception:
                                local_vars_for_prompt = None

                            if BEDROCK_INSTRUMENTATION_AVAILABLE and get_captured_model_data:
                                prompt = _extract_prompt_from_captured(get_captured_model_data())
                            usage = extract_usage(result, kwargs, prompt=prompt, response_text=response)
                            model_id_final = model or (metadata.get('model') if metadata and 'model' in metadata else None) or extract_model_id(result, kwargs)
                        except Exception:
                            pass
                    
                    # Create span data
                    # Capture local variables if needed
                    local_vars = {}
                    if capture_locals or capture_self:
                        try:
                            frame = inspect.currentframe()
                            if frame and frame.f_back:
                                local_vars = frame.f_back.f_locals.copy()
                        except Exception:
                            pass
                    
                    input_payload = {"input": prompt} if prompt else _build_input_data(
                        args, kwargs, local_vars, capture_locals, capture_self
                    )

                    span_data = SpanData(
                        span_id=span_id,
                        span_name=span_name,
                        span_type="generation",  # LLM calls are generations
                        parent_span_id=parent_span_id,
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                        input_data=input_payload,
                        output_data=serialize_value(result) if not error else None,
                        error=str(error) if error else None,
                        model_id=model_id_final,
                        metadata=metadata or {},
                        usage=usage,
                        prompt=prompt,
                        response=response,
                        status="error" if error else "success",
                        status_message=str(error) if error else None,
                    )
                    
                    # Add to trace
                    TraceManager.add_span(span_data)

                    if pending_added:
                        TraceManager._decrement_pending()
                    
                    # Clear auto-captured data after use
                    if BEDROCK_INSTRUMENTATION_AVAILABLE and clear_captured_model_data:
                        clear_captured_model_data()
            
            return sync_wrapper
    
    return decorator
