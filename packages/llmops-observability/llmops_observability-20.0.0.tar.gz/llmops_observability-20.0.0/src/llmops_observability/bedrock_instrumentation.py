"""
Bedrock Auto-Instrumentation - Automatically capture model_id, prompts, and responses
Uses wrapt to patch botocore at the lowest level for automatic tracking
"""
import json
import io
import logging
import wrapt
from typing import Optional, Dict, Any
from contextvars import ContextVar
from botocore.response import StreamingBody

logger = logging.getLogger(__name__)

# Context variable to store captured model data for the current call
_bedrock_call_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('bedrock_call_context', default=None)

# Global flag to track if instrumentation is enabled
_instrumentation_enabled = False


def get_captured_model_data() -> Optional[Dict[str, Any]]:
    """
    Get the auto-captured model data from the current context.
    
    Returns:
        Dict with 'model_id', 'request_body', 'response_body' or None
    """
    return _bedrock_call_context.get()


def clear_captured_model_data():
    """Clear the captured model data from context."""
    _bedrock_call_context.set(None)


def _instrument_bedrock_call(wrapped, instance, args, kwargs):
    """
    Wrapper function that intercepts botocore._make_api_call
    Automatically captures model_id, request body, and response body
    """
    # Only process if instrumentation is enabled
    if not _instrumentation_enabled:
        return wrapped(*args, **kwargs)
    
    operation_name = args[0] if args else None
    
    # Only intercept Bedrock Runtime operations
    if instance.meta.service_model.service_name != 'bedrock-runtime':
        return wrapped(*args, **kwargs)
    
    # Only track InvokeModel operations (not streaming for now)
    if operation_name not in ['InvokeModel', 'Converse']:
        return wrapped(*args, **kwargs)
    
    try:
        # Extract request parameters
        params = kwargs.get('api_params', args[1] if len(args) > 1 else {})
        model_id = params.get('modelId')
        
        # Capture request body
        request_body = params.get('body')
        request_payload = None
        
        if request_body:
            if isinstance(request_body, bytes):
                try:
                    request_payload = json.loads(request_body.decode('utf-8'))
                except Exception as e:
                    logger.debug(f"Failed to decode request body: {e}")
            elif isinstance(request_body, str):
                try:
                    request_payload = json.loads(request_body)
                except Exception as e:
                    logger.debug(f"Failed to parse request body: {e}")
        
        # Capture messages for Converse API
        messages = params.get('messages')
        system_prompts = params.get('system')
        
        logger.debug(f"[Bedrock Instrumentation] Captured modelId: {model_id}")
        
        # Execute the actual API call
        response = wrapped(*args, **kwargs)
        
        # Capture response body
        response_payload = None
        
        if operation_name == 'InvokeModel' and 'body' in response:
            # Read the StreamingBody
            original_body_stream = response['body']
            response_content = original_body_stream.read()
            
            try:
                response_payload = json.loads(response_content)
            except Exception as e:
                logger.debug(f"Failed to parse response body: {e}")
            
            # Restore the body stream so downstream code can read it
            response['body'] = StreamingBody(
                raw_stream=io.BytesIO(response_content),
                content_length=len(response_content)
            )
        elif operation_name == 'Converse':
            # Converse API returns dict directly
            response_payload = response.copy() if isinstance(response, dict) else None
        
        # Store captured data in context variable
        captured_data = {
            'model_id': model_id,
            'operation': operation_name,
            'request_body': request_payload,
            'response_body': response_payload,
            'messages': messages,
            'system': system_prompts,
        }
        
        _bedrock_call_context.set(captured_data)
        logger.debug(f"[Bedrock Instrumentation] Stored captured data in context")
        
        return response
        
    except Exception as e:
        logger.error(f"[Bedrock Instrumentation] Error during interception: {e}", exc_info=True)
        # If anything fails, just execute the original call
        return wrapped(*args, **kwargs)


def enable_bedrock_instrumentation():
    """
    Enable automatic Bedrock instrumentation.
    Must be called before making any Bedrock API calls.
    """
    global _instrumentation_enabled
    
    if _instrumentation_enabled:
        logger.info("[Bedrock Instrumentation] Already enabled")
        return
    
    try:
        import botocore.client
        
        logger.info("[Bedrock Instrumentation] Enabling automatic model_id capture...")
        
        wrapt.wrap_function_wrapper(
            'botocore.client',
            'BaseClient._make_api_call',
            _instrument_bedrock_call
        )
        
        _instrumentation_enabled = True
        logger.info("[Bedrock Instrumentation] ✓ Enabled successfully")
        
    except Exception as e:
        logger.error(f"[Bedrock Instrumentation] Failed to enable: {e}", exc_info=True)
        raise


def disable_bedrock_instrumentation():
    """
    Disable automatic Bedrock instrumentation.
    Note: Once wrapt patches are applied, they cannot be easily removed.
    This just sets the flag to stop processing in the wrapper.
    """
    global _instrumentation_enabled
    _instrumentation_enabled = False
    logger.info("[Bedrock Instrumentation] Disabled")


def is_instrumentation_enabled() -> bool:
    """Check if Bedrock instrumentation is enabled."""
    return _instrumentation_enabled
