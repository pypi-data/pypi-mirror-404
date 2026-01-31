"""Organization context middleware for multi-tenant isolation.

Sets the tenant context at the start of each request so that all
downstream repository operations are automatically scoped to the
correct organization.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from mysql_to_sheets.models.repository import clear_tenant, set_tenant

logger = logging.getLogger("mysql_to_sheets.api.middleware.organization")


class OrganizationContextMiddleware(BaseHTTPMiddleware):
    """Extract organization_id from request state and set TenantContext.

    Must run AFTER authentication middleware (AuthMiddleware / UserAuthMiddleware)
    which populates ``request.state.organization_id`` from JWT claims or API key.

    If no organization_id is found on the request state, the middleware
    lets the request proceed without setting a tenant context. Downstream
    repositories that require tenant context will fail-closed (raise
    RuntimeError) if they are accessed without a context.
    """

    def __init__(self, app: Any, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not self.enabled:
            return await call_next(request)

        # Skip tenant context for public endpoints
        path = request.url.path
        if path in ("/api/v1/health", "/docs", "/redoc", "/openapi.json", "/metrics"):
            return await call_next(request)

        org_id = getattr(request.state, "organization_id", None)
        token = None

        if org_id is not None:
            try:
                token = set_tenant(org_id)
            except (ValueError, TypeError):
                logger.warning("Invalid organization_id on request state: %r", org_id)

        try:
            response = await call_next(request)
        finally:
            clear_tenant(token)

        return response


__all__ = ["OrganizationContextMiddleware"]
