"""Rate limiting middleware."""

import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("mysql_to_sheets.api.middleware.rate_limit")

# Maximum number of buckets to keep in memory before triggering cleanup
_MAX_BUCKETS = 10000
# Cleanup interval in seconds (5 minutes)
_CLEANUP_INTERVAL = 300


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple sliding window rate limiter per client IP.

    Includes automatic cleanup of stale buckets to prevent memory leaks
    in long-running processes with many unique client IPs.

    Attributes:
        enabled: Whether rate limiting is enabled.
        requests_per_minute: Maximum requests per minute per client.
    """

    def __init__(
        self,
        app: Any,
        enabled: bool = False,
        requests_per_minute: int = 60,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.requests_per_minute = requests_per_minute
        self._buckets: dict[str, list[float]] = {}
        self._last_cleanup = time.time()

    def _get_client_key(self, request: Request) -> str:
        """Get rate limit key for the client.

        Uses the rightmost IP from X-Forwarded-For header because reverse proxies
        APPEND the real client IP. Taking the first IP allows spoofing.
        This is Edge Case 29: X-Forwarded-For IP spoofing prevention.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take rightmost IP - it's the one added by the trusted proxy
            ips = [ip.strip() for ip in forwarded.split(",")]
            return ips[-1] if ips else "unknown"
        return request.client.host if request.client else "unknown"

    def _cleanup_stale_buckets(self, now: float, window_start: float) -> None:
        """Remove empty buckets and buckets with only stale timestamps.

        This prevents unbounded memory growth when many unique IPs make requests.
        Called periodically based on _CLEANUP_INTERVAL or when bucket count exceeds _MAX_BUCKETS.
        """
        # Find and remove empty or stale buckets
        stale_keys = [
            key for key, timestamps in self._buckets.items()
            if not timestamps or all(ts <= window_start for ts in timestamps)
        ]
        for key in stale_keys:
            del self._buckets[key]

        if stale_keys:
            logger.debug(
                "Rate limiter cleanup: removed %d stale buckets, %d remaining",
                len(stale_keys),
                len(self._buckets),
            )

        self._last_cleanup = now

    def _allow(self, key: str) -> bool:
        """Check if request is allowed under the rate limit."""
        now = time.time()
        window_start = now - 60

        # Periodic cleanup or emergency cleanup if too many buckets
        if (now - self._last_cleanup > _CLEANUP_INTERVAL) or (len(self._buckets) > _MAX_BUCKETS):
            self._cleanup_stale_buckets(now, window_start)

        if key not in self._buckets:
            self._buckets[key] = []

        self._buckets[key] = [ts for ts in self._buckets[key] if ts > window_start]

        if len(self._buckets[key]) < self.requests_per_minute:
            self._buckets[key].append(now)
            return True

        return False

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request through rate limiting middleware."""
        if not self.enabled:
            return await call_next(request)

        client_key = self._get_client_key(request)

        if not self._allow(client_key):
            return Response(
                content=json.dumps(
                    {
                        "error": "Rate limit exceeded",
                        "details": {"limit": self.requests_per_minute, "window": "60s"},
                    }
                ),
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        return await call_next(request)


__all__ = ["RateLimitMiddleware"]
