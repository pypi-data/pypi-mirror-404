import time
import uuid
from collections.abc import Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .base import get_logger

# Context variable to store request ID across async calls
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses in FastAPI.

    Features:
    - Automatic request ID generation
    - Request/response timing
    - Configurable body logging
    - Context injection for request ID
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Process the request and log information."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra_data={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
            },
            extra={"request_id": request_id},
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra_data={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
                extra={"request_id": request_id},
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                extra_data={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2),
                },
                extra={"request_id": request_id},
            )

            # Re-raise the exception
            raise


def get_request_id() -> str:
    """
    Get the current request ID from context.

    Returns:
        Current request ID or empty string if not in request context

    Example:
        >>> from log2fast_fastapi.middleware import get_request_id
        >>> request_id = get_request_id()
    """
    return request_id_var.get()
