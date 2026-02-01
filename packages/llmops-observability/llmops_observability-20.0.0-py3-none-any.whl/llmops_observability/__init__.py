"""
LLMOps Observability SDK - Public API
Minimal SDK focused on:
- Trace collection via decorators (@track_function, @track_llm_call)
- Single-message SQS dispatch with compression
- ASGI middleware for FastAPI/Starlette auto-tracing
- Automatic Bedrock model_id capture (optional)
"""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("llmops-observability")
except PackageNotFoundError:
    __version__ = "0.0.0"

# Core components
from .trace_manager import TraceManager, track_function
from .llm import track_llm_call
from .sqs import send_to_sqs, send_to_sqs_immediate, flush_sqs, is_sqs_enabled
from .asgi_middleware import LLMOpsASGIMiddleware

# Bedrock auto-instrumentation (optional - requires boto3)
try:
    from .bedrock_instrumentation import (
        enable_bedrock_instrumentation,
        disable_bedrock_instrumentation,
        is_instrumentation_enabled,
    )
    BEDROCK_INSTRUMENTATION_AVAILABLE = True
except ImportError:
    BEDROCK_INSTRUMENTATION_AVAILABLE = False
    enable_bedrock_instrumentation = None
    disable_bedrock_instrumentation = None
    is_instrumentation_enabled = None

__all__ = [
    "TraceManager",
    "track_function",
    "track_llm_call",
    "send_to_sqs",
    "send_to_sqs_immediate",
    "flush_sqs",
    "is_sqs_enabled",
    "LLMOpsASGIMiddleware",
    "enable_bedrock_instrumentation",
    "disable_bedrock_instrumentation",
    "is_instrumentation_enabled",
    "__version__",
]
