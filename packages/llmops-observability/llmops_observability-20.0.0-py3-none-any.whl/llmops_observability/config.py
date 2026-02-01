"""
Configuration management for LLMOps Observability SDK
- Environment loading
- SQS configuration
- Default model resolution
- Size and performance limits
"""
import os
import logging
import tempfile
from typing import Dict, Any
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[llmops_observability] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Try to load .env if it exists, but don't require it
# This allows users to set env vars before or after importing the SDK
try:
    load_dotenv()
except Exception:
    pass  # Silently continue if no .env file


# ============================================================
# SIZE LIMITS & CONSTRAINTS
# ============================================================

# Serialization limits
MAX_OUTPUT_SIZE = 200 * 1024  # 200 KB - max size for individual field serialization
MAX_SPAN_IO_SIZE = 20_000     # 20 KB - max size for span input/output data
MAX_TRACE_IO_SIZE = 50_000    # 50 KB - max size for trace-level input/output
MAX_SQS_SIZE = 200_000        # 200 KB - max SQS message size (with compression)

# Truncation thresholds
TRUNCATION_PREVIEW_SIZE = 1000  # Preview size when truncating
PROMPT_RESPONSE_MAX_SIZE = 10_000  # Max size for prompt/response fields


# ============================================================
# SQS CONFIGURATION & BATCHING
# ============================================================

# Spillover file for failed SQS sends
SPILLOVER_FILE = os.path.join(
    tempfile.gettempdir(), 
    "llmops_observability_spillover_queue.jsonl"
)

# Worker configuration
SQS_WORKER_COUNT = 4        # Number of background worker threads
SQS_BATCH_SIZE = 10         # Flush batch when reaching this count
SQS_BATCH_TIMEOUT = 0.2     # Timeout for queue.get() in seconds
SQS_FLUSH_TIME_THRESHOLD = 0.15  # Time-based flush threshold (every ~1s)
SQS_SHUTDOWN_TIMEOUT = 1.0  # Timeout for worker shutdown


def get_sqs_config() -> Dict[str, Any]:
    """
    Get SQS configuration from environment variables.
    
    Environment variables:
        - AWS_SQS_URL: SQS queue URL (required to enable SQS)
        - AWS_PROFILE: AWS profile name (default: "default")
        - AWS_REGION: AWS region (default: "us-east-1")
    
    Returns:
        Dict with SQS configuration
    """
    return {
        "aws_sqs_url": os.getenv("AWS_SQS_URL"),
        "aws_profile": os.getenv("AWS_PROFILE", "default"),
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),
    }


# ============================================================
# PROJECT & ENVIRONMENT CONFIGURATION
# ============================================================

def get_project_id() -> str:
    """
    Get project ID from environment variables.
    Auto-injected into every span's metadata.
    
    Environment variables:
        - PROJECT_ID: Project identifier (default: "unknown_project")
    
    Returns:
        str: Project ID
    """
    return os.getenv("PROJECT_ID", "unknown_project").strip()


def get_environment() -> str:
    """
    Get environment from environment variables.
    Auto-injected into every span's metadata.
    
    Environment variables:
        - ENV: Environment (e.g., "development", "staging", "uat", "production")
        - Default: "development"
    
    Returns:
        str: Environment name
    """
    return os.getenv("ENV", "development").strip()


def get_trace_context() -> Dict[str, str]:
    """
    Get trace context (project_id and environment) from environment.
    This is injected into all spans automatically.
    
    Returns:
        Dict with project_id and environment
    """
    return {
        "project_id": get_project_id(),
        "environment": get_environment(),
    }


# ============================================================
# MODEL CONFIGURATION
# ============================================================

def get_default_model() -> str:
    """
    Get default model ID for cost calculation.
    
    Resolution order:
        1. MODEL_ID environment variable (if set)
        2. Default: anthropic.claude-3-5-sonnet-20241022-v2:0 (Claude 3.5 Sonnet - most common, cost-effective)
    
    Environment variables:
        - MODEL_ID: Default model ID for cost calculation (e.g., "anthropic.claude-3-sonnet-20240229-v1:0")
    
    Returns:
        str: Default model ID for cost calculation
    """
    # Most popular and cost-effective model as fallback
    DEFAULT_FALLBACK = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    model_id = os.getenv("MODEL_ID", DEFAULT_FALLBACK).strip()
    
    if not model_id:
        model_id = DEFAULT_FALLBACK
    
    logger.debug(f"Default model for cost calculation: {model_id}")
    return model_id
