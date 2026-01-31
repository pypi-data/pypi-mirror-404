"""JWT user authentication middleware.

Validates Bearer tokens from the Authorization header and attaches
user and organization context to the request state.
"""

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("mysql_to_sheets.api.middleware.user_auth")


class UserAuthMiddleware(BaseHTTPMiddleware):
    """JWT Bearer token authentication middleware.

    Validates JWT access tokens and attaches user info to request state.

    Attributes:
        enabled: Whether JWT authentication is enabled.
        db_path: Path to the tenant database for user lookups.
        exempt_paths: Paths that don't require authentication.
    """

    def __init__(
        self,
        app: Any,
        enabled: bool = False,
        db_path: str | None = None,
        exempt_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.db_path = db_path
        self.exempt_paths = exempt_paths or [
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/password/reset",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
            "/api/v1/billing/webhook",
        ]

    def _is_exempt(self, path: str) -> bool:
        """Check if a path is exempt from authentication."""
        for exempt in self.exempt_paths:
            if path == exempt or path.startswith(exempt + "/"):
                return True
        return False

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request through JWT authentication middleware."""
        if not self.enabled or self._is_exempt(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                content=json.dumps(
                    {
                        "error": "Bearer token required",
                        "details": {"header": "Authorization: Bearer <token>"},
                    }
                ),
                status_code=401,
                media_type="application/json",
            )

        token = auth_header[7:]  # Remove "Bearer "

        try:
            from mysql_to_sheets.core.auth import AuthConfig, is_token_blacklisted, verify_token
            from mysql_to_sheets.core.config import get_config

            config = get_config()
            # Create AuthConfig from Config
            auth_config = AuthConfig(jwt_secret_key=config.jwt_secret_key)
            payload = verify_token(token, auth_config, expected_type="access")

            if payload is None:
                return Response(
                    content=json.dumps({"error": "Invalid or expired token"}),
                    status_code=401,
                    media_type="application/json",
                )

            jti = getattr(payload, "jti", None)
            if jti is not None and is_token_blacklisted(jti):
                return Response(
                    content=json.dumps({"error": "Token is blacklisted"}),
                    status_code=401,
                    media_type="application/json",
                )

            # Look up user
            if self.db_path:
                from mysql_to_sheets.models.users import get_user_repository

                user_repo = get_user_repository(self.db_path)
                user = user_repo.get_by_id(payload.user_id, payload.organization_id)

                if user is None or not user.is_active:
                    return Response(
                        content=json.dumps({"error": "User not found or inactive"}),
                        status_code=401,
                        media_type="application/json",
                    )

                request.state.user = user

            request.state.organization_id = payload.organization_id
            request.state.user_id = payload.user_id

        except Exception as e:
            logger.debug("JWT validation failed: %s", e)
            return Response(
                content=json.dumps({"error": "Invalid or expired token"}),
                status_code=401,
                media_type="application/json",
            )

        return await call_next(request)


__all__ = ["UserAuthMiddleware"]
