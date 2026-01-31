"""Audit context middleware.

Captures request information for audit logging, attaching
correlation IDs and request metadata to the audit context.
"""

import logging
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("mysql_to_sheets.api.middleware.audit")


class AuditContextMiddleware(BaseHTTPMiddleware):
    """Middleware that sets up audit context for each request.

    Generates a correlation ID and attaches request metadata
    for downstream audit logging.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and set up audit context."""
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        # Store request metadata for audit
        request.state.client_ip = request.headers.get("X-Forwarded-For", "").split(",")[
            0
        ].strip() or (request.client.host if request.client else "unknown")
        request.state.user_agent = request.headers.get("User-Agent", "")

        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


__all__ = ["AuditContextMiddleware"]
