"""Prometheus metrics endpoint for monitoring.

Exposes application metrics in Prometheus format at /metrics.
Enable with METRICS_ENABLED=true environment variable.
"""

import time
from typing import Any, Callable

from fastapi import APIRouter, Request, Response
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.metrics import get_registry

router = APIRouter(tags=["monitoring"])


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus metrics",
    description="Returns application metrics in Prometheus text format.",
)
async def metrics() -> str:
    """Export metrics in Prometheus format.

    Returns:
        Prometheus-formatted metrics string.
    """
    config = get_config()
    if not config.metrics_enabled:
        return (
            "# Metrics disabled. Set METRICS_ENABLED=true to enable.\n"
            "# See documentation for available metrics.\n"
        )
    return get_registry().to_prometheus()


class HTTPMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request metrics.

    Records request counts and durations for all API endpoints.
    Metrics are only recorded when METRICS_ENABLED=true.

    Metrics exposed:
    - mysql_to_sheets_http_requests_total{method, path, status}
    - mysql_to_sheets_http_request_duration_seconds{method, path}
    """

    # Paths to exclude from metrics (high-cardinality or internal)
    EXCLUDED_PATHS = {"/metrics", "/health", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app: Any, enabled: bool = True) -> None:
        """Initialize HTTP metrics middleware.

        Args:
            app: ASGI application.
            enabled: Whether metrics collection is enabled.
        """
        super().__init__(app)
        self._enabled = enabled

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """Process request and record metrics.

        Args:
            request: HTTP request.
            call_next: Next middleware/handler.

        Returns:
            HTTP response.
        """
        # Skip if metrics disabled or path excluded
        if not self._enabled or request.url.path in self.EXCLUDED_PATHS:
            result: Response = await call_next(request)
            return result

        # Normalize path to reduce cardinality (replace IDs with placeholders)
        path = self._normalize_path(request.url.path)
        method = request.method

        # Record request timing
        start_time = time.time()
        response: Response = await call_next(request)
        duration = time.time() - start_time

        # Record metrics
        registry = get_registry()

        # Request counter
        request_counter = registry.counter(
            "mysql_to_sheets_http_requests_total",
            "Total number of HTTP requests",
            labels={"method": method, "path": path, "status": str(response.status_code)},
        )
        request_counter.inc()

        # Duration histogram
        duration_histogram = registry.histogram(
            "mysql_to_sheets_http_request_duration_seconds",
            "HTTP request duration in seconds",
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            labels={"method": method, "path": path},
        )
        duration_histogram.observe(duration)

        return response

    def _normalize_path(self, path: str) -> str:
        """Normalize path to reduce metric cardinality.

        Replaces numeric IDs with {id} placeholder.

        Args:
            path: Original request path.

        Returns:
            Normalized path.
        """
        parts = path.split("/")
        normalized = []
        for part in parts:
            # Replace numeric IDs with placeholder
            if part.isdigit():
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized)
