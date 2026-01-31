"""API key scope enforcement middleware.

Validates that API keys have sufficient scopes for the requested endpoint.
"""

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("mysql_to_sheets.api.middleware.scope")


# Endpoint scope requirements
# Format: (method, path_prefix) -> required_scope
# None means no scope required (public endpoint)
ENDPOINT_SCOPES: dict[tuple[str, str], str | None] = {
    # Health and docs - no auth required
    ("GET", "/api/v1/health"): None,
    ("GET", "/docs"): None,
    ("GET", "/redoc"): None,
    ("GET", "/openapi.json"): None,
    ("GET", "/metrics"): None,
    # Read-only endpoints
    ("GET", "/api/v1/history"): "read",
    ("GET", "/api/v1/configs"): "read",
    ("GET", "/api/v1/schedules"): "read",
    ("GET", "/api/v1/freshness"): "read",
    ("GET", "/api/v1/jobs"): "read",
    ("GET", "/api/v1/audit"): "read",
    ("GET", "/api/v1/usage"): "read",
    # Sync operations
    ("POST", "/api/v1/sync"): "sync",
    ("POST", "/api/v1/validate"): "sync",
    # Config management
    ("POST", "/api/v1/configs"): "config",
    ("PUT", "/api/v1/configs"): "config",
    ("DELETE", "/api/v1/configs"): "config",
    # Schedule management
    ("POST", "/api/v1/schedules"): "config",
    ("PUT", "/api/v1/schedules"): "config",
    ("DELETE", "/api/v1/schedules"): "config",
    # Admin operations
    ("POST", "/api/v1/organizations"): "admin",
    ("PUT", "/api/v1/organizations"): "admin",
    ("DELETE", "/api/v1/organizations"): "admin",
    ("POST", "/api/v1/users"): "admin",
    ("PUT", "/api/v1/users"): "admin",
    ("DELETE", "/api/v1/users"): "admin",
    ("POST", "/api/v1/webhooks"): "admin",
    ("PUT", "/api/v1/webhooks"): "admin",
    ("DELETE", "/api/v1/webhooks"): "admin",
}


def get_required_scope(method: str, path: str) -> str | None:
    """Get the required scope for an endpoint.

    Args:
        method: HTTP method (GET, POST, etc.).
        path: Request path.

    Returns:
        Required scope name, or None if no scope required.
    """
    # Exact match first
    scope = ENDPOINT_SCOPES.get((method, path))
    if scope is not None:
        return scope

    # Prefix match (for paths like /api/v1/configs/123)
    for (ep_method, ep_path), ep_scope in ENDPOINT_SCOPES.items():
        if method == ep_method and path.startswith(ep_path):
            return ep_scope

    # Default: require "read" for GET, "sync" for POST/PUT/DELETE
    if method == "GET":
        return "read"
    return "sync"


class ScopeMiddleware(BaseHTTPMiddleware):
    """API key scope enforcement middleware.

    Checks that the authenticated API key has sufficient scopes for the
    requested endpoint. Must be applied after AuthMiddleware.

    Attributes:
        enabled: Whether scope enforcement is enabled.
    """

    def __init__(
        self,
        app: Any,
        enabled: bool = True,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request through scope enforcement middleware."""
        if not self.enabled:
            return await call_next(request)

        # Get API key info from request state (set by AuthMiddleware)
        key_info = getattr(request.state, "api_key_info", None)

        # If no key info, auth middleware already handled it or path is exempt
        if not key_info:
            return await call_next(request)

        # Get required scope for this endpoint
        required_scope = get_required_scope(request.method, request.url.path)

        # No scope required for this endpoint
        if required_scope is None:
            return await call_next(request)

        # Check if key has the required scope
        has_scope_func = key_info.get("has_scope")
        if has_scope_func is None:
            # Legacy key info without scope support - allow for backwards compat
            return await call_next(request)

        if not has_scope_func(required_scope):
            logger.warning(
                "Scope check failed: key_id=%s required=%s available=%s path=%s",
                key_info.get("id"),
                required_scope,
                key_info.get("scopes", []),
                request.url.path,
            )
            return Response(
                content=json.dumps({
                    "error": "insufficient_scope",
                    "required": required_scope,
                    "available": key_info.get("scopes", []),
                    "hint": f"API key needs '{required_scope}' scope for this endpoint",
                }),
                status_code=403,
                media_type="application/json",
            )

        return await call_next(request)


__all__ = ["ScopeMiddleware", "get_required_scope", "ENDPOINT_SCOPES"]
