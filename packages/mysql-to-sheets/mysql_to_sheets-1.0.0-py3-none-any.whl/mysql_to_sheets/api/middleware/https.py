"""HTTPS enforcement middleware.

Redirects HTTP requests to HTTPS and adds security headers.
"""

import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

logger = logging.getLogger("mysql_to_sheets.api.middleware.https")


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces HTTPS connections.

    When enabled, redirects HTTP requests to HTTPS and adds security headers
    including Strict-Transport-Security (HSTS).

    Configuration via environment variables:
        HTTPS_REQUIRED: Enable HTTPS enforcement (default: false)
        HSTS_MAX_AGE: HSTS max-age in seconds (default: 31536000 = 1 year)
        HSTS_INCLUDE_SUBDOMAINS: Include subdomains in HSTS (default: true)
        HSTS_PRELOAD: Enable HSTS preload (default: false)

    Attributes:
        enabled: Whether HTTPS enforcement is enabled.
        hsts_max_age: HSTS max-age header value.
        include_subdomains: Whether to include subdomains in HSTS.
        preload: Whether to include preload directive in HSTS.
    """

    def __init__(
        self,
        app: Any,
        enabled: bool | None = None,
        hsts_max_age: int | None = None,
        include_subdomains: bool | None = None,
        preload: bool | None = None,
    ) -> None:
        super().__init__(app)

        # Read configuration from env or use provided values
        if enabled is not None:
            self.enabled = enabled
        else:
            self.enabled = os.getenv("HTTPS_REQUIRED", "false").lower() == "true"

        if hsts_max_age is not None:
            self.hsts_max_age = hsts_max_age
        else:
            self.hsts_max_age = int(os.getenv("HSTS_MAX_AGE", "31536000"))

        if include_subdomains is not None:
            self.include_subdomains = include_subdomains
        else:
            self.include_subdomains = (
                os.getenv("HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true"
            )

        if preload is not None:
            self.preload = preload
        else:
            self.preload = os.getenv("HSTS_PRELOAD", "false").lower() == "true"

        if self.enabled:
            logger.info(
                f"HTTPS enforcement enabled. HSTS max-age: {self.hsts_max_age}s, "
                f"includeSubDomains: {self.include_subdomains}, preload: {self.preload}"
            )

    def _get_hsts_header(self) -> str:
        """Build the Strict-Transport-Security header value."""
        parts = [f"max-age={self.hsts_max_age}"]
        if self.include_subdomains:
            parts.append("includeSubDomains")
        if self.preload:
            parts.append("preload")
        return "; ".join(parts)

    def _is_https(self, request: Request) -> bool:
        """Check if the request is using HTTPS.

        Handles both direct connections and proxy forwarding.
        """
        # Direct HTTPS connection
        if request.url.scheme == "https":
            return True

        # Check forwarded headers (from reverse proxy)
        x_forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
        if x_forwarded_proto == "https":
            return True

        # AWS ALB / Cloudflare / other proxy headers
        if request.headers.get("X-Forwarded-Ssl") == "on":
            return True

        return False

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and enforce HTTPS."""
        if not self.enabled:
            return await call_next(request)

        # Check if request is already HTTPS
        if not self._is_https(request):
            # Build HTTPS URL
            https_url = request.url.replace(scheme="https")
            logger.debug(f"Redirecting HTTP request to HTTPS: {https_url}")
            return RedirectResponse(url=str(https_url), status_code=301)

        # Process the request
        response = await call_next(request)

        # Add HSTS header to all HTTPS responses
        response.headers["Strict-Transport-Security"] = self._get_hsts_header()

        # Add additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response


__all__ = ["HTTPSRedirectMiddleware"]
