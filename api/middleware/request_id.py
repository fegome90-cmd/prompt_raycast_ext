"""Request ID middleware for request tracing."""
import re
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Pattern for validating client-provided request IDs
# Allow alphanumeric characters and hyphens, max 36 chars (UUID length)
REQUEST_ID_PATTERN = re.compile(r"^[a-zA-Z0-9-]{1,36}$")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for tracing.

    - Generates 8-char ID if not provided
    - Validates client-provided IDs (alphanumeric + hyphens only, max 36 chars)
    - Adds X-Request-ID to response headers
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Use existing ID if valid, otherwise generate new one (8 chars for readability)
        client_id = request.headers.get("X-Request-ID")
        if client_id and REQUEST_ID_PATTERN.match(client_id):
            request_id = client_id
        else:
            request_id = uuid.uuid4().hex[:8]

        # Make request ID available to downstream handlers.
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add ID to response
        response.headers["X-Request-ID"] = request_id

        return response
