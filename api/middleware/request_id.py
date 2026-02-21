"""Request ID middleware for request tracing."""
import uuid
from collections.abc import Callable
from typing import Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for tracing.

    - Generates 8-char ID if not provided
    - Adds X-Request-ID to response headers
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Use existing ID or generate new one (8 chars for readability)
        # Use or to handle both missing header and empty string
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:8]

        # Process request
        response = await call_next(request)

        # Add ID to response
        response.headers["X-Request-ID"] = request_id

        return response
