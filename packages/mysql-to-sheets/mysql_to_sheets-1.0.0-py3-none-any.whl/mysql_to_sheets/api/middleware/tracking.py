"""Usage tracking middleware.

Records API request counts for usage metering and billing.
"""

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("mysql_to_sheets.api.middleware.tracking")


class UsageTrackerMiddleware(BaseHTTPMiddleware):
    """Middleware that tracks API usage for billing and analytics.

    Records request counts per organization for usage metering.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and record usage."""
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Track usage if organization context is available
        org_id = getattr(request.state, "organization_id", None)
        if org_id is not None:
            try:
                from mysql_to_sheets.core.usage_tracking import record_api_call

                # record_api_call only takes organization_id and count
                record_api_call(organization_id=org_id, count=1)
            except Exception:
                # Usage tracking should never break requests
                pass

        return response


__all__ = ["UsageTrackerMiddleware"]
