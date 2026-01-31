"""Request ID middleware for request tracing and correlation.

P1 FIX: Adds request ID correlation for debugging and log tracing.
"""

from collections.abc import Callable
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from identity_plan_kit.shared.logging import bind_context, clear_context, get_logger

logger = get_logger(__name__)

# Header names for request ID
REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates/propagates request IDs for tracing.

    Features:
    - Generates a unique request ID if not provided in headers
    - Binds request ID to structlog context for all logs in the request
    - Returns request ID in response headers
    - Supports correlation ID for distributed tracing

    Usage:
        ```python
        from identity_plan_kit.shared.request_id import RequestIDMiddleware

        app.add_middleware(RequestIDMiddleware)

        # All logs will automatically include request_id
        logger.info("processing_request")  # {"request_id": "abc-123", ...}
        ```

    Headers:
        - X-Request-ID: Unique ID for this specific request
        - X-Correlation-ID: ID that spans multiple services (optional)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with request ID tracking."""
        # Get or generate request ID
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = str(uuid4())

        # Get correlation ID if provided (for distributed tracing)
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)

        # Build context for logging
        log_context = {"request_id": request_id}
        if correlation_id:
            log_context["correlation_id"] = correlation_id

        # Add request metadata to context
        log_context["path"] = request.url.path
        log_context["method"] = request.method

        # Bind to structlog context for all logs in this request
        bind_context(**log_context)

        try:
            # Store request ID on request state for access in handlers
            request.state.request_id = request_id
            if correlation_id:
                request.state.correlation_id = correlation_id

            # Process request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers[REQUEST_ID_HEADER] = request_id
            if correlation_id:
                response.headers[CORRELATION_ID_HEADER] = correlation_id

            return response

        finally:
            # Clear context after request completes
            clear_context()


def get_request_id(request: Request) -> str | None:
    """
    Get the request ID from a request.

    Args:
        request: FastAPI/Starlette request

    Returns:
        Request ID or None if not available

    Example:
        ```python
        @app.get("/items")
        async def get_items(request: Request):
            request_id = get_request_id(request)
            # Use request_id for tracing
        ```
    """
    return getattr(request.state, "request_id", None)


def get_correlation_id(request: Request) -> str | None:
    """
    Get the correlation ID from a request.

    Args:
        request: FastAPI/Starlette request

    Returns:
        Correlation ID or None if not provided
    """
    return getattr(request.state, "correlation_id", None)
