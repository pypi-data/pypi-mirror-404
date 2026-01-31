"""Role-based access control middleware.

Enforces permission checks on API endpoints based on user role.
Follows a fail-closed model: unknown permissions deny access.
"""

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("mysql_to_sheets.api.middleware.rbac")

# Map (method, path_prefix) to required permission name
ENDPOINT_PERMISSIONS: dict[tuple[str, str], str] = {
    ("GET", "/api/v1/configs"): "VIEW_CONFIGS",
    ("POST", "/api/v1/configs"): "EDIT_CONFIGS",
    ("PUT", "/api/v1/configs"): "EDIT_CONFIGS",
    ("DELETE", "/api/v1/configs"): "DELETE_CONFIGS",
    ("POST", "/api/v1/sync"): "RUN_SYNC",
    ("GET", "/api/v1/history"): "VIEW_HISTORY",
    ("GET", "/api/v1/users"): "VIEW_USERS",
    ("POST", "/api/v1/users"): "MANAGE_USERS",
    ("PUT", "/api/v1/users"): "MANAGE_USERS",
    ("DELETE", "/api/v1/users"): "MANAGE_USERS",
    ("GET", "/api/v1/schedules"): "VIEW_SCHEDULES",
    ("POST", "/api/v1/schedules"): "MANAGE_SCHEDULES",
    ("PUT", "/api/v1/schedules"): "MANAGE_SCHEDULES",
    ("DELETE", "/api/v1/schedules"): "MANAGE_SCHEDULES",
    ("GET", "/api/v1/webhooks"): "VIEW_WEBHOOKS",
    ("POST", "/api/v1/webhooks"): "MANAGE_WEBHOOKS",
    ("PUT", "/api/v1/webhooks"): "MANAGE_WEBHOOKS",
    ("DELETE", "/api/v1/webhooks"): "MANAGE_WEBHOOKS",
    ("GET", "/api/v1/api-keys"): "VIEW_API_KEYS",
    ("POST", "/api/v1/api-keys"): "MANAGE_API_KEYS",
    ("DELETE", "/api/v1/api-keys"): "MANAGE_API_KEYS",
    ("GET", "/api/v1/audit"): "VIEW_CONFIGS",
    ("GET", "/api/v1/notifications"): "VIEW_NOTIFICATIONS",
    ("POST", "/api/v1/notifications"): "MANAGE_NOTIFICATIONS",
    # Freshness / SLA monitoring
    ("GET", "/api/v1/freshness"): "VIEW_CONFIGS",
    ("PUT", "/api/v1/freshness"): "EDIT_CONFIGS",
    ("POST", "/api/v1/freshness"): "EDIT_CONFIGS",
    # Job queue
    ("GET", "/api/v1/jobs"): "VIEW_CONFIGS",
    ("POST", "/api/v1/jobs"): "RUN_SYNC",
    # Usage metering
    ("GET", "/api/v1/usage"): "VIEW_CONFIGS",
    # Organization management
    ("GET", "/api/v1/organizations"): "VIEW_ORGANIZATION",
    ("POST", "/api/v1/organizations"): "MANAGE_ORGANIZATION",
    ("PUT", "/api/v1/organizations"): "MANAGE_ORGANIZATION",
    ("DELETE", "/api/v1/organizations"): "MANAGE_ORGANIZATION",
    # Billing webhook uses signature-based auth, not RBAC
    # (handled separately in billing_webhook_routes.py)
}


class RBACMiddleware(BaseHTTPMiddleware):
    """Role-based access control middleware.

    Checks user permissions against endpoint requirements.
    Follows fail-closed model: unknown permissions deny access.

    Attributes:
        enabled: Whether RBAC enforcement is enabled.
    """

    def __init__(self, app: Any, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled

    def _get_required_permission(self, method: str, path: str) -> str | None:
        """Get the required permission for a request."""
        # Exact match
        key = (method, path)
        if key in ENDPOINT_PERMISSIONS:
            return ENDPOINT_PERMISSIONS[key]

        # Prefix match (e.g., /api/v1/configs/123)
        for (m, prefix), perm in ENDPOINT_PERMISSIONS.items():
            if m == method and path.startswith(prefix):
                return perm

        return None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request through RBAC middleware."""
        if not self.enabled:
            return await call_next(request)

        # Only enforce RBAC if a user is attached (from UserAuthMiddleware)
        user = getattr(request.state, "user", None)
        if user is None:
            return await call_next(request)

        permission_name = self._get_required_permission(request.method, request.url.path)
        if permission_name is None:
            return await call_next(request)

        try:
            from mysql_to_sheets.core.rbac import Permission, has_permission

            permission = Permission[permission_name]
            if not has_permission(user, permission):
                return Response(
                    content=json.dumps(
                        {
                            "error": "Forbidden",
                            "required_permission": permission_name,
                            "user_role": user.role,
                        }
                    ),
                    status_code=403,
                    media_type="application/json",
                )
        except KeyError:
            # Fail-closed: unknown permission denies access
            logger.error("Unknown permission '%s' - denying access", permission_name)
            return Response(
                content=json.dumps({"error": "Forbidden", "details": "Unknown permission"}),
                status_code=403,
                media_type="application/json",
            )

        return await call_next(request)


__all__ = ["RBACMiddleware"]
