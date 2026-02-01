# LLMOps Observability SDK

A production-grade Python SDK for LLM observability with SQS-based event streaming for decoupled, scalable observability pipelines. Automatically captures traces, spans, token usage, costs, and metadata from your LLM applications.

## 🎯 Key Features

- ⚡ **SQS Event Streaming**: Batch events to AWS SQS with automatic spillover recovery
- 🎨 **Simple Decorators**: `@track_function` and `@track_llm_call` for instant instrumentation
- 🔄 **Sync & Async Support**: Works with both synchronous and asynchronous functions
- 🤖 **Provider Agnostic**: Compatible with any LLM provider (AWS Bedrock, OpenAI, Anthropic, etc.)
- 🪆 **Hierarchical Tracing**: Automatic parent-child span relationships with proper nesting
- 💰 **Cost Tracking**: Built-in token usage and cost calculation for AWS Bedrock models
- 🔍 **Smart Capture**: Optionally capture function locals and self for detailed debugging
- 📊 **Size Management**: Automatic truncation and compression (200KB limits) to prevent data issues
- 🛡️ **Production-Ready**: Daemon workers, batch processing, clean shutdown handling
- 🌍 **Auto-Injection**: Environment and project_id automatically added to every span

## 📦 Installation

```bash
# From source (development)
cd llmops-observability_sdk
pip install -e .

# Or with uv
uv sync
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in your application directory:

```bash
# Project Configuration (Required - Auto-injected into every span)
PROJECT_ID=my_project          # Your project identifier
ENV=uat                        # Environment: development, staging, uat, production

# AWS SQS Configuration (Required for trace streaming)
AWS_SQS_URL=https://sqs.us-east-1.amazonaws.com/123456789/my-queue
AWS_PROFILE=default            # AWS profile name
AWS_REGION=us-east-1           # AWS region

# Model Configuration (Optional)
MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0  # Default model for cost calculation
```

**Key Configuration Values:**
- **`PROJECT_ID`**: Unique identifier for your project. Auto-injected into every span's metadata.
- **`ENV`**: Environment name (development/staging/uat/production). Auto-injected into every span's metadata.
- **`AWS_SQS_URL`**: SQS queue URL for sending traces to Lambda processor.

> 💡 **Important**: `PROJECT_ID` and `ENV` are automatically injected into every span's metadata by the SDK. You don't need to manually add them to decorators.

## 🚀 Quick Start

### 1. Basic Usage with Auto-Configuration
```python
from llmops_observability import TraceManager, track_function, track_llm_call

# Start a trace - PROJECT_ID and ENV are auto-loaded from config.py
TraceManager.start_trace(
    name="rag_pipeline_example",
    user_id="user_123",
    session_id="session_456",
    metadata={"version": "1.0.0"},
    tags=["example", "rag"]
)

# Track regular functions
@track_function()
def process_input(user_query: str):
    return {"query": user_query, "processed": True}

# Track LLM calls with automatic cost calculation
@track_llm_call(model="anthropic.claude-3-sonnet-20240229-v1:0")
def call_llm(prompt: str):
    response = bedrock_client.invoke_model(...)  # Your LLM call
    return response

# Execute your workflow
result = process_input("What is Python?")
answer = call_llm("Context: ...\n\nQuestion: What is Python?")

# Finalize and send to SQS (optional parameters)
TraceManager.finalize_and_send(
    trace_name="rag_pipeline_example",
    trace_input={"user_msg": "What is Python?"},
    trace_output={"bot_response": answer}
)
```

### 2. Automatic Environment & Project Injection

**Every span automatically gets `environment` and `project_id` in metadata:**

```python
# Set environment variables
os.environ["PROJECT_ID"] = "new_test"
os.environ["ENV"] = "uat"

# Start trace
TraceManager.start_trace("my_operation")

# Every @track_function and @track_llm_call span will automatically have:
# span.metadata = {
#     "environment": "uat",
#     "project_id": "new_test",
#     # ... other metadata ...
# }
```

✅ **No manual injection needed!** The SDK automatically adds these to every span.

### 3. Nested Spans (Parent-Child Relationships)

```python
@track_function()
def parent_function():
    # This creates a parent span
    child_result = child_function()
    return child_result

@track_function()
def child_function():
    # This automatically becomes a child of parent_function
    grandchild_result = grandchild_function()
    return grandchild_result

@track_function()
def grandchild_function():
    # This becomes a child of child_function
    return "result"

# Proper hierarchy maintained in Langfuse/NewRelic/S3
```

## 📊 Data Flow Architecture

```
┌─────────────────────┐
│   Your LLM App      │
│  (with decorators)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  TraceManager       │
│  (collects spans)   │
│  + Auto-injects:    │
│    - environment    │
│    - project_id     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SQS Batch Workers  │
│  (compress & send)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  AWS SQS Queue      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Lambda Processor   │
│  (parallel routing) │
└─────┬──────┬────┬───┘
      │      │    │
      ▼      ▼    ▼
  Langfuse  S3  NewRelic
```

## 🎨 Decorator Reference

### @track_function - Complete Guide

#### Basic Usage (No Parameters)

```python
@track_function()
def process_data(input_data):
    # Automatically captures:
    # - Function name as span name
    # - Function arguments (args, kwargs)
    # - Return value
    # - Execution time
    # - Environment and project_id (auto-injected)
    return {"processed": input_data}
```

#### Parameter: `name` (Custom Span Name)

```python
@track_function(name="custom_span_name")
def my_function():
    # Span will appear as "custom_span_name" instead of "my_function"
    return result

# Use case: Make span names more descriptive in traces
@track_function(name="fetch_user_profile_from_db")
def get_user(user_id):
    return db.query(user_id)
```

#### Parameter: `metadata` (Add Custom Metadata)

```python
@track_function(metadata={"service": "auth", "priority": "high"})
def authenticate_user(username, password):
    # Span metadata will include:
    # {
    #     "service": "auth",
    #     "priority": "high",
    #     "environment": "uat",      # auto-injected
    #     "project_id": "new_test"   # auto-injected
    # }
    return auth_result

# Use case: Tag spans with business context
@track_function(metadata={
    "database": "postgres",
    "table": "users",
    "operation": "read"
})
def query_users(filters):
    return db.execute(query)
```

#### Parameter: `capture_locals=True` (Capture All Local Variables)

```python
@track_function(capture_locals=True)
def process_payment(amount, currency):
    user_id = "user_123"
    transaction_id = generate_id()
    tax = amount * 0.1
    total = amount + tax
    
    # All local variables captured in span.input_data.locals:
    # {
    #     "user_id": "user_123",
    #     "transaction_id": "txn_abc",
    #     "tax": 10.0,
    #     "total": 110.0,
    #     "amount": 100.0,
    #     "currency": "USD"
    # }
    
    return {"total": total}

# ⚠️ Warning: Can capture large amounts of data. Use for debugging only.
```

#### Parameter: `capture_locals=["var1", "var2"]` (Capture Specific Variables)

```python
@track_function(capture_locals=["user_id", "total"])
def process_payment(amount, currency):
    user_id = "user_123"
    transaction_id = generate_id()
    tax = amount * 0.1
    total = amount + tax
    
    # Only specified variables captured in span.input_data.locals:
    # {
    #     "user_id": "user_123",
    #     "total": 110.0
    # }
    # Note: transaction_id, tax, amount, currency are NOT captured
    
    return {"total": total}

# ✅ Recommended: Capture only what you need for debugging
```

#### Parameter: `capture_self=True` (Capture `self` in Class Methods)

```python
class PaymentProcessor:
    def __init__(self, merchant_id):
        self.merchant_id = merchant_id
        self.fee_rate = 0.029
    
    @track_function(capture_self=True)
    def process(self, amount):
        # Captures self attributes in span.input_data.self:
        # {
        #     "merchant_id": "merch_123",
        #     "fee_rate": 0.029
        # }
        fee = amount * self.fee_rate
        return amount - fee

# Use case: Debug class state during execution
class DatabaseConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connected = False
    
    @track_function(capture_self=True, capture_locals=["query"])
    def execute(self, query):
        # Captures both self and specific locals
        result = self._run_query(query)
        return result
```

#### Combined Parameters Example

```python
@track_function(
    name="complex_data_pipeline",
    metadata={"stage": "preprocessing", "version": "2.0"},
    capture_locals=["processed_count", "errors"],
    capture_self=False
)
def pipeline_stage(data):
    processed_count = 0
    errors = []
    temp_cache = {}  # Not captured
    
    for item in data:
        try:
            process_item(item)
            processed_count += 1
        except Exception as e:
            errors.append(str(e))
    
    return {"count": processed_count, "errors": errors}
```

---

### @track_llm_call - Complete Guide

#### Basic Usage (No Parameters)

```python
@track_llm_call()
def call_llm(prompt):
    # Automatically captures:
    # - Function arguments (prompt)
    # - LLM response
    # - Execution time
    # - Span type = "generation"
    # - Environment and project_id (auto-injected)
    response = bedrock_client.invoke_model(...)
    return response
```

#### Parameter: `name` (Custom Span Name)

```python
@track_llm_call(name="bedrock_claude_sonnet")
def call_llm(prompt):
    # Span appears as "bedrock_claude_sonnet" instead of "call_llm"
    response = bedrock_client.invoke_model(...)
    return response

# Use case: Distinguish between different LLM providers/models
@track_llm_call(name="openai_gpt4_turbo")
def call_openai(prompt):
    return openai.chat.completions.create(...)

@track_llm_call(name="anthropic_claude_opus")
def call_anthropic(prompt):
    return anthropic.messages.create(...)
```

#### Parameter: `model` (For Cost Calculation)

```python
@track_llm_call(model="anthropic.claude-3-sonnet-20240229-v1:0")
def call_bedrock(prompt):
    # SDK automatically calculates cost based on:
    # - Token usage from response
    # - Model pricing for Claude 3 Sonnet
    # 
    # Captured in span:
    # - usage.input_tokens
    # - usage.output_tokens
    # - cost.input_cost
    # - cost.output_cost
    # - cost.total_cost
    
    response = bedrock_client.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        body=json.dumps({"prompt": prompt})
    )
    return response

# Supported AWS Bedrock models (see pricing.py):
# - anthropic.claude-3-5-sonnet-20241022-v2:0
# - anthropic.claude-3-sonnet-20240229-v1:0
# - anthropic.claude-3-haiku-20240307-v1:0
# - anthropic.claude-3-opus-20240229-v1:0
# - And more...
```

#### Parameter: `metadata` (Add Custom Metadata)

```python
@track_llm_call(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    metadata={
        "temperature": 0.7,
        "max_tokens": 1000,
        "use_case": "code_generation"
    }
)
def generate_code(prompt):
    # Span metadata includes:
    # {
    #     "temperature": 0.7,
    #     "max_tokens": 1000,
    #     "use_case": "code_generation",
    #     "environment": "uat",      # auto-injected
    #     "project_id": "new_test"   # auto-injected
    # }
    return llm_response
```

#### Parameter: `capture_locals=True` (Capture All Locals)

```python
@track_llm_call(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    capture_locals=True
)
def enhanced_llm_call(user_query, context_docs):
    # Build prompt with context
    formatted_context = format_documents(context_docs)
    system_prompt = "You are a helpful assistant."
    final_prompt = f"{system_prompt}\n\nContext: {formatted_context}\n\nQuestion: {user_query}"
    
    # All locals captured:
    # {
    #     "user_query": "What is Python?",
    #     "context_docs": [...],
    #     "formatted_context": "...",
    #     "system_prompt": "You are a helpful assistant.",
    #     "final_prompt": "..."
    # }
    
    response = bedrock_client.invoke_model(...)
    return response
```

#### Parameter: `capture_locals=["prompt", "temperature"]` (Specific Variables)

```python
@track_llm_call(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    capture_locals=["final_prompt", "model_config"]
)
def call_with_config(user_input):
    model_config = {"temperature": 0.7, "max_tokens": 1000}
    system_message = "You are an AI assistant."  # NOT captured
    final_prompt = f"{system_message}\n\n{user_input}"
    temp_cache = {}  # NOT captured
    
    # Only captures:
    # {
    #     "final_prompt": "...",
    #     "model_config": {"temperature": 0.7, "max_tokens": 1000}
    # }
    
    response = call_llm(final_prompt, **model_config)
    return response
```

#### Parameter: `capture_self=True` (For Class Methods)

```python
class LLMOrchestrator:
    def __init__(self, model_id, api_key):
        self.model_id = model_id
        self.api_key = api_key
        self.request_count = 0
        self.total_cost = 0.0
    
    @track_llm_call(
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        capture_self=True
    )
    def call_llm(self, prompt):
        # Captures self attributes:
        # {
        #     "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
        #     "request_count": 5,
        #     "total_cost": 0.042
        # }
        # Note: api_key might be captured - be careful with secrets!
        
        self.request_count += 1
        response = self._invoke_model(prompt)
        return response
```

#### Combined Parameters Example (Production Pattern)

```python
class ChatbotService:
    def __init__(self, model_id):
        self.model_id = model_id
        self.system_prompt = "You are a helpful chatbot."
    
    @track_llm_call(
        name="chatbot_generation",
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        metadata={
            "service": "customer_support",
            "model_version": "v2.0",
            "priority": "high"
        },
        capture_locals=["full_prompt", "temperature"],
        capture_self=False  # Don't capture self to avoid secrets
    )
    def generate_response(self, user_message, conversation_history):
        temperature = 0.7
        full_prompt = self._build_prompt(user_message, conversation_history)
        cache_key = hash(full_prompt)  # Not captured
        
        response = bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "prompt": full_prompt,
                "temperature": temperature,
                "max_tokens": 1000
            })
        )
        return response
```

---

### Quick Reference Table

| Parameter | @track_function | @track_llm_call | Type | Description |
|-----------|----------------|-----------------|------|-------------|
| `name` | ✅ | ✅ | `str` | Custom span name |
| `metadata` | ✅ | ✅ | `Dict[str, Any]` | Additional metadata |
| `capture_locals` | ✅ | ✅ | `bool` or `List[str]` | Capture local variables |
| `capture_self` | ✅ | ✅ | `bool` | Capture `self` in methods |
| `model` | ❌ | ✅ | `str` | Model ID for cost calculation |

---

### Best Practices

#### ✅ DO

```python
# Capture specific variables for debugging
@track_function(capture_locals=["error_code", "retry_count"])

# Use metadata for business context
@track_function(metadata={"team": "payments", "priority": "critical"})

# Specify model for accurate cost tracking
@track_llm_call(model="anthropic.claude-3-sonnet-20240229-v1:0")

# Use descriptive names
@track_llm_call(name="rag_retrieval_claude")
```

#### ❌ DON'T

```python
# Don't capture all locals in production (too much data)
@track_function(capture_locals=True)  # Only for debugging!

# Don't capture self if it contains secrets
@track_function(capture_self=True)  # Check for API keys first!

# Don't use generic names
@track_function(name="function_1")  # Not helpful

# Don't forget model for LLM calls
@track_llm_call()  # Missing model = no cost calculation
```

---

## 📈 What Gets Captured

### Trace-Level Data
- `trace_id`, `trace_name`, `project_id`, `environment`
- `user_id`, `session_id`
- `start_time`, `end_time`, `duration_ms`
- `trace_input`, `trace_output`
- `metadata`, `tags`
- `total_spans`, `total_generations`
- `sdk_name`, `sdk_version`

### Span-Level Data (Auto-captured for every span)
- **Core**: `span_id`, `span_name`, `span_type`, `parent_span_id`
- **Timing**: `start_time`, `end_time`, `duration_ms`
- **I/O**: `input_data`, `output_data`
- **Status**: `status`, `status_message`, `error`
- **LLM**: `model_id`, `prompt`, `response`
- **Usage**: `usage.input_tokens`, `usage.output_tokens`, `usage.total_tokens`
- **Cost**: Calculated from model pricing
- **Metadata**: `environment`, `project_id` (auto-injected), custom metadata
- **Context**: `tags`, `level`

## 🔧 Configuration Reference

### Size Limits (in config.py)

```python
MAX_OUTPUT_SIZE = 200 * 1024      # 200 KB - max individual field
MAX_SPAN_IO_SIZE = 20_000          # 20 KB - span input/output
MAX_TRACE_IO_SIZE = 50_000         # 50 KB - trace input/output
MAX_SQS_SIZE = 200_000             # 200 KB - SQS message
PROMPT_RESPONSE_MAX_SIZE = 10_000  # 10 KB - prompt/response fields
```

### SQS Configuration

```python
SQS_WORKER_COUNT = 4           # Background worker threads
SQS_BATCH_SIZE = 10            # Batch size before flush
SQS_BATCH_TIMEOUT = 0.2        # Timeout in seconds
SQS_FLUSH_TIME_THRESHOLD = 0.15
SQS_SHUTDOWN_TIMEOUT = 1.0
```

## 🏭 Production Best Practices

### 1. Proper Trace Lifecycle

```python
try:
    # Start trace
    TraceManager.start_trace("operation_name")
    
    # Your application logic with decorators
    result = my_tracked_function()
    
    # Finalize with trace data
    TraceManager.finalize_and_send(
        trace_input={"request": "data"},
        trace_output={"response": result}
    )
except Exception as e:
    # Trace will still be sent with error information
    logger.error(f"Error: {e}")
```

### 2. Environment-Specific Configuration

```python
# production.env
PROJECT_ID=my_app
ENV=production
AWS_SQS_URL=https://sqs.us-east-1.amazonaws.com/123/prod-queue

# staging.env
PROJECT_ID=my_app
ENV=staging
AWS_SQS_URL=https://sqs.us-east-1.amazonaws.com/123/staging-queue
```

### 3. Async Support

```python
@track_function()
async def async_function():
    result = await some_async_operation()
    return result

@track_llm_call(model="...")
async def async_llm_call():
    response = await async_bedrock_call()
    return response
```

## 📝 Example: Complete RAG Pipeline

# Track LLM calls
@track_llm_call()
def call_bedrock(prompt):
    # Call your LLM
    response = bedrock_client.converse(
        modelId="anthropic.claude-3-sonnet",
        messages=[{"role": "user", "content": prompt}]
    )
    return response

# Use the functions
result = process_data("some data")
llm_response = call_bedrock("Hello, world!")

# End the trace (flushes to Langfuse)
TraceManager.end_trace()
```

**Method 2: Explicit Project and Environment Override**
```python
# Override PROJECT_ID and ENV from .env
TraceManager.start_trace(
    name="chat_message",  # Operation name
    project_id="custom_project",  # Override PROJECT_ID
    environment="staging",  # Override ENV
    metadata={"user_id": "123"},
)

# Your code...

TraceManager.end_trace()
```

**Method 3: Using `finalize_and_send()` (llmops-observability)**
```python
# Start trace
TraceManager.start_trace(name="chat_session")

# Your code
user_input = "What is machine learning?"
response = await llm.generate(user_input)

# Finalize with input/output in one call
TraceManager.finalize_and_send(
    user_id="user_123",
    session_id="session_456",
    trace_name="chat_message",
    trace_input={"user_msg": user_input},
    trace_output={"bot_response": str(response)}
)
```

### 3. Capture Local Variables (Debugging)

```python
@track_function(capture_locals=True)
def complex_calculation(x, y, z):
    intermediate = x + y
    result = intermediate * z
    final = result ** 2
    # All local variables are captured in Langfuse
    return final

# Capture specific variables only
@track_function(capture_locals=["important_var", "result"])
def selective_capture(data):
    important_var = process(data)
    temp_var = "not captured"
    result = transform(important_var)
    return result
```

### 4. Nested Spans (Parent-Child Tracking)

```python
@track_function(name="parent_task")
def parent_function():
    data = fetch_data()
    # Child spans are automatically nested
    processed = child_function(data)
    return processed

@track_function(name="child_task")
def child_function(data):
    return data.upper()

# Langfuse will show: parent_task → child_task
```

### 5. ASGI Middleware (FastAPI Auto-Tracing)

```python
from fastapi import FastAPI
from llmops_observability import LLMOpsASGIMiddleware

app = FastAPI()
app.add_middleware(LLMOpsASGIMiddleware, service_name="my_api")

@app.get("/")
async def root():
    # Request is automatically traced
    return {"message": "Hello World"}

@app.post("/generate")
async def generate(prompt: str):
    # All decorated functions within request are nested
    result = await generate_text(prompt)
    return result
```

### 6. SQS Event Streaming (Event-Driven Architecture)

For event-driven, scalable deployments, the SDK supports optional event streaming to AWS SQS. Trace events are published to SQS queues where Lambda functions (or other consumers) can process them asynchronously:

```
Application (sends trace events)
    ↓
SQS Queue (decoupled message broker)
    ↓
Lambda Consumers (process & forward)
    ↓ ↓ ↓
  S3  New Relic  Datadog  (etc.)
```

**Setup:**

```bash
# Enable SQS streaming by setting AWS_SQS_URL
export AWS_SQS_URL=https://sqs.us-east-1.amazonaws.com/123456789/my-queue
export AWS_PROFILE=default
export AWS_REGION=us-east-1
```

```python
from llmops_observability import TraceManager, track_function

# When AWS_SQS_URL is set, events are automatically streamed to SQS
TraceManager.start_trace(
    name="chat_message",
    metadata={"channel": "web"}
)

@track_function()
def process_message(msg):
    return process(msg)

# All trace events are batched and sent to SQS (non-blocking)
TraceManager.end_trace()
```

**Lambda Consumer Example:**

```python
import json
import boto3

s3_client = boto3.client('s3')
newrelic = boto3.client('cloudwatch')  # Or use New Relic SDK

def lambda_handler(event, context):
    """Process trace events from SQS"""
    for record in event['Records']:
        # Parse trace event from SQS message
        trace_event = json.loads(record['body'])
        
        # Store to S3
        s3_client.put_object(
            Bucket='trace-events',
            Key=f"{trace_event['trace_id']}.json",
            Body=json.dumps(trace_event)
        )
        
        # Send metrics to New Relic
        if trace_event['event_type'] == 'llm_call':
            newrelic.put_metric_data(
                Namespace='LLMOps',
                MetricData=[{
                    'MetricName': 'TokenUsage',
                    'Value': trace_event['tokens_used'],
                    'Unit': 'Count'
                }]
            )
```

**SQS Features:**
- ✅ **Automatic Batching**: Groups events for efficient SQS sending (batch size 1-10)
- ✅ **Spillover Recovery**: Saves messages to disk if SQS is unavailable, retries on restart
- ✅ **Daemon Workers**: 4 background threads handle async SQS operations
- ✅ **Clean Shutdown**: Graceful shutdown flushes pending messages
- ✅ **Resilient**: Auto-restart failed workers, exponential backoff
- ✅ **No Blocking**: SQS operations never block main application thread

**Events Streamed to SQS:**
- `trace_start`: Trace initialization with metadata
- `span_created`: Function execution tracking
- `llm_call`: LLM API calls with token usage
- `trace_end`: Trace completion with duration

**Configuration:**
```bash
# Required: SQS queue URL
export AWS_SQS_URL=https://sqs.us-east-1.amazonaws.com/123456789/llm-traces

# Optional: AWS authentication (defaults to IAM role if in Lambda/EC2)
export AWS_PROFILE=custom-profile  # Default: "default"
export AWS_REGION=eu-west-1        # Default: "us-east-1"
```

**Use Cases:**
- 📊 Send trace events to New Relic, Datadog, CloudWatch
- 💾 Archive all LLM interactions to S3 for compliance/audit
- 🔄 Post-processing: cost calculation, quality analysis, retraining data
- 🚀 Scale: decouple application from storage/monitoring infrastructure

### 📥 Incoming SDK Message Schema

When SQS streaming is enabled, the SDK sends trace data in a compressed SQS message format that Lambda consumers can decompress and process. This section documents the message format and decompressed payload structure.

#### SQS Message Wrapper Format

```json
{
  "compressed": true,
  "data": "H4sIANPGn2YC/...",
  "trace_id": "87a41b12-cc61-4fdf-9bf2-a50a369b4d30",
  "type": "SDKTraceData"
}
```

**Wrapper Fields:**
- **`compressed`** (boolean): Indicates Base64 + Gzip compression is applied
- **`data`** (string): Base64-encoded, Gzip-compressed JSON payload
- **`trace_id`** (string): Unique trace identifier for deduplication
- **`type`** (string): Message type identifier ("SDKTraceData")

#### Decompressed SDK Trace Data Schema

```json
{
  "trace_id": "87a41b12-cc61-4fdf-9bf2-a50a369b4d30",
  "trace_name": "rag_pipeline_example",
  "project_id": "new_test",
  "environment": "uat",
  "user_id": "user_123",
  "session_id": "session_456",
  
  "start_time": 1769446311.0,
  "end_time": 1769446318.021,
  "duration_ms": 7021,
  
  "trace_input": {
    "user_msg": "What is Android ????"
  },
  "trace_output": {
    "bot_response": "Android is a mobile operating system..."
  },
  
  "token_usage": {
    "total_input_tokens": 145,
    "total_output_tokens": 87,
    "total_tokens": 232
  },
  
  "cost": {
    "total_cost": 0.000456
  },
  
  "spans": [
    {
      "span_id": "87a41b12-cc61-4fdf-9bf2-a50a369b4d31",
      "span_name": "retrieve_context",
      "span_type": "span",
      "parent_span_id": null,
      
      "start_time": 1769446311.0,
      "end_time": 1769446313.0,
      "duration_ms": 2000,
      
      "input_data": {"args": [], "kwargs": {"query": "Android"}, "locals": {}},
      "output_data": {"output": ["Doc 1", "Doc 2"]},
      
      "error": null,
      "model_id": null,
      "status": "success",
      
      "metadata": {
        "environment": "uat",
        "project_id": "new_test"
      },
      "tags": []
    },
    {
      "span_id": "87a41b12-cc61-4fdf-9bf2-a50a369b4d32",
      "span_name": "call_llm",
      "span_type": "generation",
      "parent_span_id": "87a41b12-cc61-4fdf-9bf2-a50a369b4d31",
      
      "start_time": 1769446313.0,
      "end_time": 1769446318.021,
      "duration_ms": 5021,
      
      "input_data": {"args": [], "kwargs": {"prompt": "Context: Doc 1, Doc 2\n\nQuestion: What is Android ????"}, "locals": {}},
      "output_data": {"output": {"message": {"content": "Android is a mobile operating system..."}}},
      
      "error": null,
      "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
      
      "usage": {
        "input_tokens": 145,
        "output_tokens": 87,
        "total_tokens": 232
      },
      
      "prompt": "Context: Doc 1, Doc 2\n\nQuestion: What is Android ????",
      "response": "Android is a mobile operating system developed by Google...",
      
      "metadata": {
        "environment": "uat",
        "project_id": "new_test"
      },
      
      "status": "success",
      "tags": []
    }
  ],
  
  "metadata": {
    "version": "1.0.0"
  },
  "tags": ["example", "rag"],
  
  "total_spans": 2,
  "total_generations": 1,
  
  "sdk_name": "llmops-observability",
  "sdk_version": "2.0.0"
}
```

#### Key Fields Reference

| Field | Type | Description | Auto-Injected |
|-------|------|-------------|---|
| `trace_id` | string | Unique trace identifier | - |
| `trace_name` | string | Trace/operation name | - |
| `project_id` | string | Project identifier from `PROJECT_ID` env var | ✅ |
| `environment` | string | Environment from `ENV` env var | ✅ |
| `user_id` | string | User identifier (optional) | - |
| `session_id` | string | Session identifier (optional) | - |
| `start_time` | float | Unix timestamp (seconds) | - |
| `end_time` | float | Unix timestamp (seconds) | - |
| `duration_ms` | int | Trace duration in milliseconds | - |
| `spans[].metadata.environment` | string | Environment (auto-injected to every span) | ✅ |
| `spans[].metadata.project_id` | string | Project ID (auto-injected to every span) | ✅ |
| `spans[].token_usage` | object | Input/output token counts | - |
| `spans[].cost` | object | Token cost calculation (Bedrock models) | - |

#### Lambda Decompression Example

```python
import json
import gzip
import base64

def lambda_handler(event, context):
    """Decompress and process SDK trace messages from SQS"""
    for record in event['Records']:
        # Parse SQS message
        message = json.loads(record['body'])
        
        if message.get('compressed'):
            # Decode Base64
            compressed_data = base64.b64decode(message['data'])
            
            # Decompress Gzip
            decompressed_data = gzip.decompress(compressed_data)
            
            # Parse JSON
            trace_data = json.loads(decompressed_data)
        else:
            trace_data = message
        
        # Now trace_data contains the full SDK trace with spans
        print(f"Trace: {trace_data['trace_id']}")
        print(f"Project: {trace_data['project_id']}")
        print(f"Environment: {trace_data['environment']}")
        print(f"Spans: {len(trace_data['spans'])}")
        
        # Process further (send to Langfuse, S3, NewRelic, etc.)
        process_trace(trace_data)
```

#### Size Limits and Truncation

- **Max Message Size**: 256KB (SQS hard limit)
- **Auto-Truncation**: Fields > 200KB are automatically truncated
- **Fallback to Disk**: If SQS is unavailable, messages spill to disk and retry on restart
- **Compression**: Typical traces compress to 10-30% of original size

### 8. Token Pricing & Cost Calculation

The SDK includes built-in AWS Bedrock token pricing for cost analysis:

```python
from llmops_observability.pricing import calculate_cost

# Calculate cost for a single LLM call
cost = calculate_cost(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    input_tokens=1500,
    output_tokens=800
)

print(f"Cost: ${cost:.4f}")  # Output: Cost: $0.0075

# Analyze costs by model
models_used = {
    "anthropic.claude-3-sonnet-20240229-v1:0": {
        "input_tokens": 10000,
        "output_tokens": 5000
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "input_tokens": 20000,
        "output_tokens": 10000
    }
}

total_cost = sum(
    calculate_cost(model, data["input_tokens"], data["output_tokens"])
    for model, data in models_used.items()
)
print(f"Total cost: ${total_cost:.4f}")
```

**Supported Models:**
- Claude 3.5 Sonnet (all variants)
- Claude 3 Sonnet/Opus/Haiku
- Claude 2.1 & 2.0
- Amazon Titan Text (Express, Lite)
- Cohere Command
- AI21 Jurassic
- Meta Llama 2 & 3

**Pricing Reference:**
All prices are updated as of 2024 and reflect AWS Bedrock official pricing. Update the pricing table in [src/llmops_observability/pricing.py](src/llmops_observability/pricing.py) as needed.

### 9. Async Support

```python
@track_function()
async def async_process(data):
    return await some_async_operation(data)

@track_llm_call(name="summarize")
async def async_llm_call(text):
    return await chain.ainvoke({"text": text})

# Both sync and async work seamlessly
```

### Per-Application Configuration

Each Gen AI application using this SDK should have **its own Langfuse project and credentials**. This ensures proper isolation and organization.

#### Step 1: Create Langfuse Project
1. Go to your Langfuse instance
2. Create a new project for your application (e.g., "chatbot-api", "doc-analyzer")
3. Copy the project's public key, secret key, and base URL

#### Step 2: Configure in Your Application

**Method 1: Environment Variables** (Recommended for production)

```bash
# .env file in your application root
LANGFUSE_PUBLIC_KEY=pk-lf-abc123...
LANGFUSE_SECRET_KEY=sk-lf-xyz789...
LANGFUSE_BASE_URL=https://langfuse.company.com
LANGFUSE_VERIFY_SSL=false
```

```python
from llmops_observability import TraceManager
from dotenv import load_dotenv

load_dotenv()  # Loads .env from current directory
# SDK auto-configures from environment variables
```

**Method 2: Explicit Configuration** (Recommended for testing)

```python
from llmops_observability import configure
import os

# At application startup (e.g., main.py)
configure(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    base_url=os.getenv("LANGFUSE_BASE_URL"),
    verify_ssl=False
)
```

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LANGFUSE_PUBLIC_KEY` | Yes | None | Langfuse public key from your project |
| `LANGFUSE_SECRET_KEY` | Yes | None | Langfuse secret key from your project |
| `LANGFUSE_BASE_URL` | Yes | None | Langfuse instance URL |
| `LANGFUSE_VERIFY_SSL` | No | `false` | Whether to verify SSL certificates |
| `PROJECT_ID` | No | `unknown_project` | Project identifier (used as trace name in Langfuse) |
| `ENV` | No | `development` | Environment name (production, staging, development, etc.) - automatically mapped to `LANGFUSE_TRACING_ENVIRONMENT` |
| `MODEL_ID` | No | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Default model ID for cost calculation when not explicitly provided |
| `AWS_SQS_URL` | No | None | AWS SQS queue URL (when provided, enables SQS event streaming) |
| `AWS_PROFILE` | No | `default` | AWS profile name for SQS authentication |
| `AWS_REGION` | No | `us-east-1` | AWS region for SQS |
| `LANGFUSE_DEBUG` | No | `false` | Enable debug logging for Langfuse client |

**Environment Tracking:**
- The `ENV` variable is automatically mapped to Langfuse's `LANGFUSE_TRACING_ENVIRONMENT`
- This applies the environment as a top-level attribute to all traces and observations
- Allows easy filtering by environment in Langfuse UI
- Must follow regex: `^(?!langfuse)[a-z0-9-_]+$` with max 40 characters
Track regular function execution with optional local variable capture.

```python
@track_function()
def my_function(x, y):
    return x + y

@track_function(name="custom_name", tags={"version": "1.0"})
def another_function():
    pass

# Capture all local variables for debugging
@track_function(capture_locals=True)
def debug_function(data):
    step1 = process(data)
    step2 = transform(step1)
    return step2  # All locals captured in Langfuse

# Capture specific variables only
@track_function(capture_locals=["result", "important_var"])
def selective_function(input):
    temp = input * 2  # Not captured
    result = temp + 10  # Captured
    important_var = compute(result)  # Captured
    return important_var
```

**Parameters:**
- `name`: Custom span name (default: function name)
- `tags`: Dictionary of tags/metadata
- `capture_locals`: Capture local variables - `True` (all), `False` (none), or list of variable names
- `capture_self`: Whether to capture `self` in methods (default: `True`)

## API Reference

### TraceManager

#### `start_trace(name, project_id=None, environment=None, metadata=None, user_id=None, session_id=None, tags=None)`
Start a new trace with project and environment tracking.

```python
TraceManager.start_trace(
    name="chat_message",  # Operation name (required)
    project_id="my_project",  # Optional: defaults to PROJECT_ID env var
    environment="production",  # Optional: defaults to ENV env var
    metadata={"custom": "data"},
    user_id="user_123",
    session_id="session_456",
    tags=["experiment"]
)
```

**Parameters:**
- `name` (required): Operation/trace name (e.g., "chat_message", "document_analysis")
- `project_id` (optional): Project identifier. Defaults to `PROJECT_ID` from `.env`. Used as trace name in Langfuse.
- `environment` (optional): Environment name (e.g., "production", "staging"). Defaults to `ENV` from `.env`. Automatically mapped to `LANGFUSE_TRACING_ENVIRONMENT`.
- `metadata` (optional): Custom metadata dictionary
- `user_id` (optional): User identifier
- `session_id` (optional): Session identifier
- `tags` (optional): List of tags

**Returns:** Trace ID (string)

**Example with .env auto-loading:**
```bash
# .env file
PROJECT_ID=chatbot-api
ENV=production
```

```python
# Automatically uses PROJECT_ID and ENV from .env
TraceManager.start_trace(
    name="user_query",
    metadata={"version": "2.0"}
)
# Trace name in Langfuse: "chatbot-api"
# Environment in Langfuse: "production"
```

#### `end_trace()`
End the current trace and flush to Langfuse.

```python
TraceManager.end_trace()
```

#### `finalize_and_send(user_id, session_id, trace_name, trace_input, trace_output)`
Finalize and send the trace with input/output metadata.

This is a convenience method that combines setting trace metadata and ending the trace in one call.

```python
TraceManager.start_trace(name="chat_message")

# ... your code executes ...

# Finalize with input/output details
TraceManager.finalize_and_send(
    user_id="user_123",
    session_id="session_456",
    trace_name="bedrock_chat_message",
    trace_input={"user_msg": "What is Python?"},
    trace_output={"bot_response": "Python is a programming language..."}
)
```

**Parameters:**
- `user_id`: User identifier
- `session_id`: Session identifier
- `trace_name`: Name for the trace (can override the initial name)
- `trace_input`: Dictionary containing the input data
- `trace_output`: Dictionary containing the output/response data

#### `end_trace()` vs `finalize_and_send()` - When to Use?

| Method | Purpose | When to Use | Example |
|--------|---------|------------|---------|
| `end_trace()` | Simply close trace, flush to Langfuse | Simple operations without trace-level input/output | Process data, internal workflows |
| `finalize_and_send()` | Close trace + capture end-to-end input/output | When you want full conversation/request visibility | User query → Bot response, LLM interactions |

**Code Comparison:**

```python
# Simple: Just close the trace
TraceManager.start_trace(name="chat_message")
result = process_data("some data")
llm_response = call_bedrock("Hello, world!")
TraceManager.end_trace()
# → Individual spans are captured, but no trace-level input/output
```

```python
# Full Visibility: Capture entire flow
TraceManager.start_trace(name="chat_session")
user_input = "What is machine learning?"
response = await llm.generate(user_input)
TraceManager.finalize_and_send(
    user_id="user_123",
    session_id="session_456",
    trace_name="chat_message",
    trace_input={"user_msg": user_input},        # ← What went in
    trace_output={"bot_response": str(response)} # ← What came out
)
# → Both span-level AND trace-level input/output captured for complete visibility
```

**In Langfuse UI:**
- `end_trace()`: Shows individual function spans with their inputs/outputs
- `finalize_and_send()`: Shows complete conversation flow + individual spans

### Decorators

#### `@track_function(name=None, tags=None)`
Track regular function execution.

```python
@track_function()
def my_function(x, y):
    return x + y

@track_function(name="custom_name", tags={"version": "1.0"})
def another_function():
    pass
```

#### `@track_llm_call(name=None, tags=None, model=None)`
Track LLM generation calls with automatic model and cost tracking.

```python
@track_llm_call()
def call_bedrock(prompt):
    response = bedrock.converse(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        messages=[{"role": "user", "content": prompt}]
    )
    return response

# With explicit model for cost calculation
@track_llm_call(model="anthropic.claude-3-sonnet-20240229-v1:0")
def call_llm(prompt):
    response = llm.generate(prompt)
    return response
```

**Model ID Resolution (for cost calculation):**

The SDK automatically determines the model ID in this order:

1. **Explicit parameter**: `@track_llm_call(model="anthropic.claude-3-sonnet-20240229-v1:0")`
2. **Function arguments**: Auto-extracts from `modelId`, `model_id`, `model`, or `model_name` parameters
3. **Environment variable**: Falls back to `MODEL_ID` from `.env` file
4. **Default fallback**: `anthropic.claude-3-5-sonnet-20241022-v2:0` (Claude 3.5 Sonnet - most common/cost-effective)

This ensures **cost is always calculated**, even if model ID is not explicitly provided.

**Example:**
```bash
# .env
MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0  # Default for all LLM calls
```

```python
@track_llm_call()
def llm_task(prompt):
    # Uses MODEL_ID from .env automatically
    return call_model(prompt)
```

## Advanced Features

### Nested Spans & Parent-Child Relationships

The SDK automatically handles nested function calls, creating parent-child relationships in Langfuse:

```python
@track_function(name="orchestrator")
def main_workflow(user_query):
    # This is the parent span
    context = retrieve_documents(user_query)  # Child span 1
    answer = generate_response(user_query, context)  # Child span 2
    return answer

@track_function(name="retrieval")
def retrieve_documents(query):
    # This becomes a child of main_workflow
    return db.search(query)

@track_function(name="generation")
def generate_response(query, context):
    # This also becomes a child of main_workflow
    return llm.generate(query, context)
```

### Data Size Management

The SDK automatically limits output size to **200KB** to prevent issues with large data:

- Outputs larger than 200KB are truncated with metadata
- Preview of first ~1KB is included
- Prevents memory/network issues with large responses

### ASGI Middleware for FastAPI

Automatically trace all HTTP requests:

```python
from fastapi import FastAPI
from llmops_observability import LLMOpsASGIMiddleware, track_function

app = FastAPI()
app.add_middleware(LLMOpsASGIMiddleware, service_name="chatbot_api")

@app.post("/chat")
async def chat_endpoint(message: str):
    # Entire request is automatically traced
    response = process_message(message)
    return {"response": response}

@track_function()
def process_message(msg):
    # This becomes a child span of the HTTP request trace
    return "Response"
```

The middleware captures:
- Request method, path, headers
- Response status code
- Request duration
- User agent, client IP
- Automatic trace naming: `{project}_{hostname}`

## Project Structure

```
llmops-observability_sdk/
├── src/
│   └── llmops_observability/
│       ├── __init__.py                # Public API & exports
│       ├── config.py                  # Langfuse client + SQS configuration
│       ├── trace_manager.py           # Core TraceManager class & @track_function decorator
│       ├── llm.py                     # @track_llm_call decorator with LLM response parsing
│       ├── models.py                  # SpanContext, TraceConfig data models
│       ├── asgi_middleware.py         # FastAPI/Starlette ASGI middleware
│       ├── sqs.py                     # Production SQS sender with batching & spillover
│       └── pricing.py                 # AWS Bedrock token pricing calculator
├── pyproject.toml                     # Project metadata & dependencies
└── README.md                          # This file
```

**Module Details:**

- **config.py**: Manages Langfuse client initialization and SQS configuration
- **trace_manager.py**: Core orchestration - handles trace lifecycle, nested spans, Langfuse API calls
- **llm.py**: LLM call decorator with support for 10+ LLM provider response formats
- **sqs.py**: Production-grade SQS integration with 4 daemon workers, batching, spillover recovery
- **pricing.py**: Token cost calculator for 15+ AWS Bedrock model variants
- **asgi_middleware.py**: Automatic HTTP request tracing for FastAPI applications

## Architecture

### Direct Langfuse Mode (Default)

```
Application
    ↓
TraceManager
    ↓
Langfuse (Real-time)
```

Traces are sent immediately to Langfuse with no intermediate storage or batching.

### SQS Event Streaming Mode (Event-Driven)

```
Application
    ↓
TraceManager → SQS Events (Batched)
                    ↓
                Lambda Functions
                    ↓ ↓ ↓
                S3  NR  DW  (etc.)
```

When `AWS_SQS_URL` is set:
- Application sends trace events to SQS asynchronously
- Main application thread is never blocked
- Lambda functions or other services consume events from SQS
- Events forwarded to S3, New Relic, Datadog, or custom processors
- Failed sends are saved to spillover file on disk for recovery
- 4 daemon worker threads handle all SQS operations independently
- Automatic cleanup on application shutdown

## Best Practices

### 1. Configuration Management
- ✅ **Each application gets its own `.env` file** with unique Langfuse credentials
- ✅ Use `.gitignore` to exclude `.env` files from version control
- ✅ Call `configure()` at application startup before any tracing
- ❌ Never hardcode credentials in the SDK or application code

### 2. Trace Organization
```python
# Good: Descriptive trace names with context
TraceManager.start_trace(
    name="document_analysis_pipeline",
    user_id=user_id,
    session_id=session_id,
    metadata={"doc_type": "pdf", "version": "2.0"},
    tags=["production", "critical"]
)

# Bad: Generic names without context
TraceManager.start_trace(name="process")
```

### 3. Local Variables Capture
```python
# Use for debugging only - has performance impact
@track_function(capture_locals=True)  # Development
def debug_complex_logic(data):
    # All locals captured
    pass

# Production: Disable or be selective
@track_function(capture_locals=False)  # Production
@track_function(capture_locals=["final_result"])  # Selective
```

### 4. Always End Traces
```python
try:
    TraceManager.start_trace(name="workflow")
    result = process()
    return result
finally:
    TraceManager.end_trace()  # Always flush
```

### 5. Trace Naming Convention
- **Trace Name (in Langfuse)**: Uses `PROJECT_ID` for easy project identification
- **Operation Name**: The `name` parameter describes what operation is being traced
- **Environment**: Tracked automatically from `ENV` variable

```python
# Example:
# .env: PROJECT_ID=payment-service, ENV=production

TraceManager.start_trace(name="process_payment")
# In Langfuse UI:
#   - Trace Name: "payment-service"
#   - Environment: "production"
#   - Operation: "process_payment" (in metadata)
```

## 📦 SQS Message Schema

### Message Wrapper (What SDK Sends to SQS)

```json
{
  "compressed": true,
  "data": "H4sIAAAAAAAC/+1Y...",
  "trace_id": "87a41b12-cc61-4fdf-9bf2-a50a369b4d30",
  "type": "trace"
}
```

**Decompression Steps:**
1. Base64 decode the `data` field → binary gzip data
2. Gzip decompress → JSON string  
3. JSON parse → Complete trace data

### Complete Trace Data (Decompressed)

```json
{
  "trace_id": "87a41b12-cc61-4fdf-9bf2-a50a369b4d30",
  "trace_name": "rag_pipeline_example",
  "project_id": "new_test",
  "environment": "uat",
  "user_id": "user_123",
  "session_id": "session_456",
  
  "start_time": 1769446311.0,
  "end_time": 1769446318.021,
  "duration_ms": 7021,
  
  "trace_input": {"user_msg": "What is Android ????"},
  "trace_output": {"bot_response": "Android is a mobile operating system..."},
  
  "spans": [
    {
      "span_id": "64a2a265-017e-4af1-bf49-15c3dd51e2fd",
      "span_name": "retrieve_context",
      "span_type": "span",
      "parent_span_id": null,
      
      "start_time": 1769446311.0,
      "end_time": 1769446312.0,
      "duration_ms": 1000,
      
      "input_data": {
        "args": ["What is Android ????"],
        "kwargs": {},
        "locals": {}
      },
      
      "output_data": {"output": {"documents": ["Doc 1", "Doc 2"]}},
      
      "error": null,
      "model_id": null,
      
      "metadata": {
        "environment": "uat",
        "project_id": "new_test"
      },
      
      "tags": [],
      "usage": null,
      "prompt": null,
      "response": null,
      "status": "success",
      "status_message": null,
      "level": "DEFAULT"
    },
    {
      "span_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "span_name": "call_llm",
      "span_type": "generation",
      "parent_span_id": null,
      
      "start_time": 1769446312.0,
      "end_time": 1769446316.0,
      "duration_ms": 4000,
      
      "input_data": {
        "args": [],
        "kwargs": {"prompt": "Context: Doc 1, Doc 2\n\nQuestion: What is Android ????"},
        "locals": {}
      },
      
      "output_data": {"output": {"message": {"content": "Android is a mobile operating system..."}}},
      
      "error": null,
      "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
      
      "metadata": {
        "environment": "uat",
        "project_id": "new_test"
      },
      
      "tags": [],
      
      "usage": {
        "input_tokens": 145,
        "output_tokens": 87,
        "total_tokens": 232
      },
      
      "prompt": "Context: Doc 1, Doc 2\n\nQuestion: What is Android ????",
      "response": "Android is a mobile operating system developed by Google...",
      
      "status": "success",
      "status_message": null,
      "level": "DEFAULT"
    }
  ],
  
  "metadata": {"version": "1.0.0"},
  "tags": ["example", "rag"],
  
  "total_spans": 2,
  "total_generations": 1,
  
  "sdk_name": "llmops-observability",
  "sdk_version": "2.0.0"
}
```

### Field Reference

**Trace Level:**

| Field | Auto-Injected | Description |
|-------|:-------------:|-------------|
| `trace_id` | ✅ | UUID generated on `start_trace()` |
| `trace_name` | ✅ | Operation name from `start_trace()` |
| `project_id` | ✅ | From `PROJECT_ID` env var |
| `environment` | ✅ | From `ENV` env var |
| `user_id` | ❌ | From `start_trace()` or `finalize_and_send()` |
| `session_id` | ❌ | From `start_trace()` or `finalize_and_send()` |
| `start_time` | ✅ | Unix timestamp (seconds) |
| `end_time` | ✅ | Unix timestamp (seconds) |
| `duration_ms` | ✅ | Calculated: `(end_time - start_time) * 1000` |
| `trace_input` | ❌ | From `finalize_and_send()` |
| `trace_output` | ❌ | From `finalize_and_send()` |
| `spans` | ✅ | Array of span objects |
| `total_spans` | ✅ | Count of all spans |
| `total_generations` | ✅ | Count of spans with `span_type == "generation"` |

**Span Level:**

| Field | Auto-Injected | Description |
|-------|:-------------:|-------------|
| `span_id` | ✅ | UUID for span |
| `span_name` | ✅ | Function name or custom name |
| `span_type` | ✅ | "span" or "generation" |
| `parent_span_id` | ✅ | Parent span ID (null for root) |
| `duration_ms` | ✅ | Execution time |
| `input_data` | ✅ | Function args, kwargs, locals |
| `output_data` | ✅ | Return value |
| `model_id` | ❌ | From `@track_llm_call(model=...)` |
| `usage` | ✅ | Token counts (generation spans only) |
| `prompt` | ✅ | Prompt text (generation spans only) |
| `response` | ✅ | Response text (generation spans only) |
| `metadata.environment` | ✅ | **Auto-injected from ENV** |
| `metadata.project_id` | ✅ | **Auto-injected from PROJECT_ID** |
| `status` | ✅ | "success" or "error" |

### Size Limits & Truncation

| Field | Limit | Behavior |
|-------|-------|----------|
| `trace_input` | 50 KB | Truncated with preview if exceeded |
| `trace_output` | 50 KB | Truncated with preview if exceeded |
| `span.input_data` | 20 KB | Truncated with preview if exceeded |
| `span.output_data` | 20 KB | Truncated with preview if exceeded |
| `span.prompt` | 10 KB | Truncated with preview if exceeded |
| `span.response` | 10 KB | Truncated with preview if exceeded |
| **Total Message** | 200 KB | Aggressive truncation applied |

### Lambda Decompression (Reference)

```python
import json
import base64
import gzip

def decompress_sqs_message(message_body: str) -> dict:
    """Decompress SDK trace data from SQS message."""
    sqs_message = json.loads(message_body)
    
    if not sqs_message.get("compressed"):
        return sqs_message
    
    # Decompress
    compressed_data = base64.b64decode(sqs_message['data'])
    decompressed = gzip.decompress(compressed_data)
    trace_data = json.loads(decompressed)
    
    return trace_data
```

---

## When to Use This SDK

✅ **Use llmops-observability when:**

**Development & Testing:**
- Developing and testing LLM applications locally
- Need quick debugging with local variable capture
- Want instant trace visibility in Langfuse (no delays)
- Simple, straightforward tracing without infrastructure setup

**Production Deployments:**
- Small to medium-scale with direct Langfuse integration
- Enterprise event-driven architectures with SQS + Lambda + S3
- Multi-destination observability (S3, New Relic, Datadog, custom systems)
- Centralized observability across multiple LLM applications
- Token cost tracking and analysis
- Compliance/audit: archive all LLM interactions with full traceability

**Common Use Cases:**
- RAG (Retrieval Augmented Generation) systems
- LLM-powered APIs and microservices
- Chat applications and conversational AI
- Document analysis and processing pipelines
- Real-time LLM inference monitoring
- Multi-step LLM workflows with nested tracking

**Key Advantages:**
- ✨ No external dependencies for basic tracing (Direct Langfuse mode)
- 🚀 Optional SQS integration for enterprise deployments
- 🔄 Automatic nested span tracking for complex workflows
- 💰 Built-in token cost calculation
- 🛡️ Production-ready with daemon workers and spillover recovery


## Troubleshooting

### Configuration Errors

**Error: "Langfuse not configured"**
```python
# Solution: Ensure env vars are set or call configure()
from dotenv import load_dotenv
load_dotenv()  # Load .env file

# Or configure explicitly
from llmops_observability import configure
configure(public_key="...", secret_key="...", base_url="...")
```

### Trace Not Appearing in Langfuse

1. Check that `TraceManager.end_trace()` is called
2. Verify credentials are correct
3. Check Langfuse URL is accessible
4. Look for error messages in console output

### SSL Certificate Issues

```python
# Disable SSL verification if using self-signed certs
configure(
    public_key="...",
    secret_key="...",
    base_url="...",
    verify_ssl=False  # ← Disable SSL verification
)
```

## Version History

**v8.0.0** (Current) - Production-Ready Enterprise Release
- ✨ **Dual-Mode Tracing**: Direct Langfuse integration + optional SQS event streaming
- 🎯 **SQS Event Streaming**: Production-grade AWS SQS sender with:
  - Automatic batching for efficiency
  - Spillover recovery to disk
  - 4 daemon worker threads
  - Clean shutdown support
- 💰 **Token Pricing**: AWS Bedrock cost calculator for 15+ model variants
- 🪆 **Nested Spans**: Automatic parent-child relationship tracking
- 🔍 **Locals Capture**: Function local variable capture for debugging
- 🌐 **ASGI Middleware**: FastAPI/Starlette auto-tracing
- 📊 **Smart Serialization**: 200KB automatic data size limits
- 🔄 **Sync & Async**: Full async/await support
- 🛡️ **Resilient**: Auto-restart failed workers, graceful shutdown

## License

Proprietary - Verisk Analytics

## Contributing

Internal SDK - For questions or contributions, contact the LLMOps team.

## Example: Complete Workflow

```python
from llmops_observability import TraceManager, track_function, track_llm_call
import boto3

# Initialize Bedrock client
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

@track_function()
def retrieve_context(query):
    # Simulate RAG retrieval
    return {"documents": ["Context doc 1", "Context doc 2"]}

@track_llm_call()
def generate_answer(prompt, context):
    response = bedrock.converse(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        messages=[{
            "role": "user",
            "content": f"Context: {context}\n\nQuestion: {prompt}"
        }]
    )
    return response

# Start trace
TraceManager.start_trace(
    name="rag_pipeline",
    user_id="user_123",
    metadata={"pipeline": "v1"}
)

# Execute workflow
context = retrieve_context("What is Python?")
answer = generate_answer("What is Python?", context)

# End trace
TraceManager.end_trace()
```

## Thanks to
Verisk LLMOps Team ❤️