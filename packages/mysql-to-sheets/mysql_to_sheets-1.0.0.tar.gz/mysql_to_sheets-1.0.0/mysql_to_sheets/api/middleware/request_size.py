"""Request size limit middleware.

Prevents DoS attacks via excessively large request payloads.
"""

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("mysql_to_sheets.api.middleware.request_size")


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that limits request body size.

    Rejects requests with Content-Length exceeding the configured maximum.

    Attributes:
        max_body_size: Maximum allowed body size in bytes.
    """

    def __init__(self, app: Any, max_body_size: int = 10 * 1024 * 1024) -> None:
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and check body size."""
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > self.max_body_size:
            max_mb = self.max_body_size / (1024 * 1024)
            return Response(
                content=json.dumps(
                    {
                        "error": "Request too large",
                        "details": {"max_size_mb": max_mb},
                    }
                ),
                status_code=413,
                media_type="application/json",
            )

        return await call_next(request)


__all__ = ["RequestSizeLimitMiddleware"]
