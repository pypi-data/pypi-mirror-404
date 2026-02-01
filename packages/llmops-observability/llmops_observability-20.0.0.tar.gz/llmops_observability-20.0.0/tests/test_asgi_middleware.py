import asyncio

import pytest

import llmops_observability.asgi_middleware as asgi_middleware
from llmops_observability.asgi_middleware import LLMOpsASGIMiddleware


async def _dummy_app(scope, receive, send):
    assert scope["type"] == "http"
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": b'{"message": "ok"}',
        }
    )


async def _error_app(scope, receive, send):
    raise RuntimeError("boom")


def _make_http_scope(path: str = "/"):
    return {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [(b"user-agent", b"pytest")],
        "query_string": b"q=1",
        "client": ("127.0.0.1", 1234),
    }


def test_get_trace_name_uses_service_name():
    app = LLMOpsASGIMiddleware(_dummy_app, service_name="svc")
    assert app.get_trace_name() == "svc"


def test_get_trace_name_default(monkeypatch):
    monkeypatch.setattr(asgi_middleware.os, "getcwd", lambda: "/tmp/myproj")
    monkeypatch.setattr(asgi_middleware.socket, "gethostname", lambda: "host")
    app = LLMOpsASGIMiddleware(_dummy_app)
    assert app.get_trace_name() == "myproj_host"


def test_asgi_middleware_traces_request(monkeypatch):
    calls = []

    def _start_trace(*args, **kwargs):
        calls.append(("start", args, kwargs))

    def _finalize_and_send(**kwargs):
        calls.append(("finalize", kwargs))
        return True

    monkeypatch.setattr(asgi_middleware.TraceManager, "start_trace", _start_trace)
    monkeypatch.setattr(asgi_middleware.TraceManager, "finalize_and_send", _finalize_and_send)

    app = LLMOpsASGIMiddleware(_dummy_app, service_name="svc")

    async def runner():
        messages = []

        async def receive():
            return {"type": "http.request"}

        async def send(message):
            messages.append(message)

        scope = _make_http_scope("/")
        await app(scope, receive, send)
        return messages

    messages = asyncio.run(runner())
    types = [m["type"] for m in messages]
    assert "http.response.start" in types
    assert "http.response.body" in types

    assert calls[0][0] == "start"
    assert calls[-1][0] == "finalize"
    trace_output = calls[-1][1]["trace_output"]
    assert trace_output["http.status_code"] == 200
    assert trace_output["response_body"] == '{"message": "ok"}'


def test_asgi_middleware_traces_exception(monkeypatch):
    calls = []

    def _start_trace(*args, **kwargs):
        calls.append(("start", args, kwargs))

    def _finalize_and_send(**kwargs):
        calls.append(("finalize", kwargs))
        return True

    monkeypatch.setattr(asgi_middleware.TraceManager, "start_trace", _start_trace)
    monkeypatch.setattr(asgi_middleware.TraceManager, "finalize_and_send", _finalize_and_send)

    app = LLMOpsASGIMiddleware(_error_app, service_name="svc")

    async def runner():
        async def receive():
            return {"type": "http.request"}

        async def send(message):
            pass

        scope = _make_http_scope("/")
        await app(scope, receive, send)

    with pytest.raises(RuntimeError):
        asyncio.run(runner())

    assert calls[-1][0] == "finalize"
    trace_output = calls[-1][1]["trace_output"]
    assert trace_output["error_type"] == "RuntimeError"


# ============================================================
# Additional tests for improved coverage
# ============================================================

def test_asgi_middleware_skips_non_http_scope():
    """Middleware passes through non-HTTP scopes (WebSocket, lifespan)."""
    app_called = {"count": 0}
    
    async def passthrough_app(scope, receive, send):
        app_called["count"] += 1
    
    middleware = LLMOpsASGIMiddleware(passthrough_app, service_name="svc")
    
    async def runner():
        # WebSocket scope
        ws_scope = {"type": "websocket", "path": "/ws"}
        await middleware(ws_scope, None, None)
        
        # Lifespan scope
        lifespan_scope = {"type": "lifespan"}
        await middleware(lifespan_scope, None, None)
    
    asyncio.run(runner())
    assert app_called["count"] == 2


def test_asgi_middleware_handles_binary_response_body(monkeypatch):
    """Middleware handles non-UTF8 response body."""
    calls = []

    def _start_trace(*args, **kwargs):
        calls.append(("start", args, kwargs))

    def _finalize_and_send(**kwargs):
        calls.append(("finalize", kwargs))
        return True

    monkeypatch.setattr(asgi_middleware.TraceManager, "start_trace", _start_trace)
    monkeypatch.setattr(asgi_middleware.TraceManager, "finalize_and_send", _finalize_and_send)

    async def binary_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        # Send binary data that can't be decoded as UTF-8
        await send({"type": "http.response.body", "body": b'\x80\x81\x82\x83'})

    app = LLMOpsASGIMiddleware(binary_app, service_name="svc")

    async def runner():
        async def receive():
            return {"type": "http.request"}

        messages = []
        async def send(message):
            messages.append(message)

        scope = _make_http_scope("/")
        await app(scope, receive, send)
        return messages

    asyncio.run(runner())

    assert calls[-1][0] == "finalize"
    trace_output = calls[-1][1]["trace_output"]
    # Should contain binary data indication
    assert "binary data" in str(trace_output.get("response_body", ""))


def test_asgi_middleware_handles_empty_response_body(monkeypatch):
    """Middleware handles empty response body."""
    calls = []

    def _start_trace(*args, **kwargs):
        calls.append(("start", args, kwargs))

    def _finalize_and_send(**kwargs):
        calls.append(("finalize", kwargs))
        return True

    monkeypatch.setattr(asgi_middleware.TraceManager, "start_trace", _start_trace)
    monkeypatch.setattr(asgi_middleware.TraceManager, "finalize_and_send", _finalize_and_send)

    async def empty_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b''})

    app = LLMOpsASGIMiddleware(empty_app, service_name="svc")

    async def runner():
        async def receive():
            return {"type": "http.request"}

        messages = []
        async def send(message):
            messages.append(message)

        scope = _make_http_scope("/")
        await app(scope, receive, send)

    asyncio.run(runner())
    assert calls[-1][0] == "finalize"


def test_asgi_middleware_handles_no_body_key(monkeypatch):
    """Middleware handles response body message without 'body' key."""
    calls = []

    def _start_trace(*args, **kwargs):
        calls.append(("start", args, kwargs))

    def _finalize_and_send(**kwargs):
        calls.append(("finalize", kwargs))
        return True

    monkeypatch.setattr(asgi_middleware.TraceManager, "start_trace", _start_trace)
    monkeypatch.setattr(asgi_middleware.TraceManager, "finalize_and_send", _finalize_and_send)

    async def no_body_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        # Send response body message without body key
        await send({"type": "http.response.body"})

    app = LLMOpsASGIMiddleware(no_body_app, service_name="svc")

    async def runner():
        async def receive():
            return {"type": "http.request"}

        messages = []
        async def send(message):
            messages.append(message)

        scope = _make_http_scope("/")
        await app(scope, receive, send)

    asyncio.run(runner())
    assert calls[-1][0] == "finalize"


def test_asgi_middleware_with_custom_headers(monkeypatch):
    """Middleware extracts x-user-id and x-session-id from headers."""
    calls = []

    def _start_trace(*args, **kwargs):
        calls.append(("start", args, kwargs))

    def _finalize_and_send(**kwargs):
        calls.append(("finalize", kwargs))
        return True

    monkeypatch.setattr(asgi_middleware.TraceManager, "start_trace", _start_trace)
    monkeypatch.setattr(asgi_middleware.TraceManager, "finalize_and_send", _finalize_and_send)

    app = LLMOpsASGIMiddleware(_dummy_app, service_name="svc")

    async def runner():
        async def receive():
            return {"type": "http.request"}

        async def send(message):
            pass

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/test",
            "headers": [
                (b"x-user-id", b"user123"),
                (b"x-session-id", b"session456"),
                (b"user-agent", b"test-agent"),
            ],
            "query_string": b"",
            "client": None,  # Test with no client
        }
        await app(scope, receive, send)

    asyncio.run(runner())

    # Check start_trace was called with correct user_id and session_id
    start_call = calls[0]
    assert start_call[2]["user_id"] == "user123"
    assert start_call[2]["session_id"] == "session456"


def test_asgi_middleware_default_values(monkeypatch):
    """Middleware uses default values when headers missing."""
    calls = []

    def _start_trace(*args, **kwargs):
        calls.append(("start", args, kwargs))

    def _finalize_and_send(**kwargs):
        calls.append(("finalize", kwargs))
        return True

    monkeypatch.setattr(asgi_middleware.TraceManager, "start_trace", _start_trace)
    monkeypatch.setattr(asgi_middleware.TraceManager, "finalize_and_send", _finalize_and_send)

    app = LLMOpsASGIMiddleware(_dummy_app, service_name="svc")

    async def runner():
        async def receive():
            return {"type": "http.request"}

        async def send(message):
            pass

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],  # No headers
            "query_string": b"",
            "client": ("10.0.0.1", 8080),
        }
        await app(scope, receive, send)

    asyncio.run(runner())

    start_call = calls[0]
    assert start_call[2]["user_id"] == "anonymous"
    # session_id should be a UUID string
    assert len(start_call[2]["session_id"]) == 36

