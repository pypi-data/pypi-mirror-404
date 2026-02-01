"""
ASGI Middleware for FastAPI/Starlette Applications
Automatically traces all HTTP requests with full observability.
"""
import uuid
import time
import os
import socket
from typing import Optional

from .trace_manager import TraceManager


class LLMOpsASGIMiddleware:
    """
    ASGI middleware for automatic HTTP request tracing.
    
    Captures:
    - Request method, path, headers
    - User and session identifiers
    - Response body and status
    - Request latency
    - Automatic trace lifecycle management
    
    Usage:
        from fastapi import FastAPI
        from llmops_observability import LLMOpsASGIMiddleware
        
        app = FastAPI()
        app.add_middleware(LLMOpsASGIMiddleware, service_name="my_api")
    """

    def __init__(self, app, service_name: Optional[str] = None):
        """
        Initialize ASGI middleware.
        
        Args:
            app: ASGI application instance
            service_name: Custom service name for traces. 
                         If None, uses "{project}_{hostname}" format.
        """
        self.app = app
        self.service_name = service_name

    def get_trace_name(self) -> str:
        """
        Generate trace name from project and hostname.
        
        Returns:
            Trace name in format: "{project}_{hostname}"
        """
        if self.service_name:
            return self.service_name
        
        project = os.path.basename(os.getcwd())
        hostname = socket.gethostname()
        return f"{project}_{hostname}"

    async def __call__(self, scope, receive, send):
        """
        ASGI middleware entry point.
        
        Args:
            scope: ASGI connection scope
            receive: ASGI receive channel
            send: ASGI send channel
        """
        # Only trace HTTP requests (not WebSocket, lifespan, etc.)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request details
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "UNKNOWN")
        query_string = scope.get("query_string", b"").decode()
        
        # Parse headers
        headers = {
            k.decode(): v.decode() 
            for k, v in scope.get("headers", [])
        }
        
        # Extract user/session from headers or generate defaults
        user_id = headers.get("x-user-id", "anonymous")
        session_id = headers.get("x-session-id", str(uuid.uuid4()))
        user_agent = headers.get("user-agent", "unknown")
        
        # Get client IP
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        
        trace_name = self.get_trace_name()
        
        # Start trace with comprehensive metadata
        TraceManager.start_trace(
            trace_name,
            user_id=user_id,
            session_id=session_id,
            metadata={
                "http.method": method,
                "http.path": path,
                "http.query_string": query_string,
                "http.user_agent": user_agent,
                "http.client_ip": client_ip,
                "service.name": self.service_name or trace_name,
            },
        )

        start_time = time.time()
        response_status = None
        response_body = None
        
        async def send_wrapper(message):
            """Intercept response to capture status and body."""
            nonlocal response_status, response_body
            
            # Capture status code
            if message["type"] == "http.response.start":
                response_status = message.get("status", 500)
            
            # Capture response body
            if message["type"] == "http.response.body":
                body = message.get("body")
                if body:
                    try:
                        # Try to decode as string
                        response_body = body.decode("utf-8")
                        # Try to parse as JSON for better formatting
                        try:
                            response_body = body.decode("utf-8")
                        except:
                            pass
                    except Exception:
                        # If decode fails, use repr
                        response_body = f"<binary data: {len(body)} bytes>"
            
            await send(message)

        try:
            # Execute the application
            await self.app(scope, receive, send_wrapper)
            
        except Exception as exc:
            # Capture exception and finalize trace with error
            latency_ms = int((time.time() - start_time) * 1000)
            
            TraceManager.finalize_and_send(
                user_id=user_id,
                session_id=session_id,
                trace_name=trace_name,
                trace_input={
                    "http.method": method,
                    "http.path": path,
                    "http.query_string": query_string,
                },
                trace_output={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "http.status_code": 500,
                    "http.latency_ms": latency_ms,
                },
            )
            raise
        
        # Normal completion - finalize trace with response data
        latency_ms = int((time.time() - start_time) * 1000)
        
        TraceManager.finalize_and_send(
            user_id=user_id,
            session_id=session_id,
            trace_name=trace_name,
            trace_input={
                "http.method": method,
                "http.path": path,
                "http.query_string": query_string,
            },
            trace_output={
                "http.status_code": response_status or 200,
                "http.latency_ms": latency_ms,
                "response_body": response_body,
            },
        )
