"""API key authentication middleware.

Validates API keys from the X-API-Key header against stored keys.
Supports exempt paths that don't require authentication.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("mysql_to_sheets.api.middleware.auth")


def _mask_key(key: str) -> str:
    """Mask an API key for logging."""
    if len(key) > 8:
        return f"{key[:4]}****{key[-4:]}"
    return "****"


class AuthMiddleware(BaseHTTPMiddleware):
    """API key authentication middleware.

    Validates requests using the X-API-Key header against stored API keys.
    Unauthenticated requests to non-exempt paths receive a 401 response.

    Attributes:
        enabled: Whether authentication is enabled.
        db_path: Path to the API keys database.
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
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
        ]

    def _is_exempt(self, path: str) -> bool:
        """Check if a path is exempt from authentication."""
        for exempt in self.exempt_paths:
            if path == exempt or path.startswith(exempt + "/"):
                return True
        return False

    def _validate_api_key(self, api_key: str) -> dict[str, Any] | None:
        """Validate an API key against stored keys.

        Uses prefix-based O(1) lookup to avoid iterating all keys.
        Falls back to full scan for legacy keys without prefixes.

        Args:
            api_key: The API key to validate.

        Returns:
            Key info dict if valid, None otherwise.
        """
        if not self.db_path:
            return None

        try:
            from mysql_to_sheets.core.security import verify_api_key
            from mysql_to_sheets.models.api_keys import get_api_key_repository

            repo = get_api_key_repository(self.db_path)

            # Extract prefix from incoming key (first 8 chars, e.g., "mts_a1b2")
            incoming_prefix = api_key[:8] if len(api_key) >= 8 else api_key

            # O(1) lookup: Filter by prefix first (indexed column)
            candidate_keys = repo.get_by_prefix(incoming_prefix, include_revoked=False)

            # If we found candidates by prefix, only check those
            if candidate_keys:
                for key_model in candidate_keys:
                    if not key_model.is_active:
                        continue
                    if verify_api_key(api_key, key_model.key_hash, key_model.key_salt):
                        repo.update_last_used(key_model.key_hash)
                        return {
                            "id": key_model.id,
                            "name": key_model.name,
                            "scopes": key_model.scopes or ["*"],
                            "has_scope": key_model.has_scope,
                        }
                # Prefix matched but hash didn't - key is invalid
                return None

            # Fallback: Legacy keys without prefix stored need full scan
            # This path is only hit for old keys created before prefix storage
            active_keys = repo.get_all(include_revoked=False, limit=1000)
            for key_model in active_keys:
                if not key_model.is_active:
                    continue
                # Only check keys without prefix (legacy keys)
                if key_model.key_prefix is not None:
                    continue
                if verify_api_key(api_key, key_model.key_hash, key_model.key_salt):
                    repo.update_last_used(key_model.key_hash)
                    logger.info(
                        "Legacy API key matched (no prefix): id=%s. Consider regenerating.",
                        key_model.id,
                    )
                    return {
                        "id": key_model.id,
                        "name": key_model.name,
                        "scopes": key_model.scopes or ["*"],
                        "has_scope": key_model.has_scope,
                    }
            return None
        except Exception as e:
            logger.warning("API key validation error: %s", e)
            return None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request through authentication middleware."""
        if not self.enabled or self._is_exempt(request.url.path):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                content={
                    "error": "API key required",
                    "message": "Include X-API-Key header with your request",
                    "code": "AUTH_501",
                    "hint": "Create key: mysql-to-sheets api-key create --name=default",
                },
                status_code=401,
            )

        key_info = self._validate_api_key(api_key)
        if key_info is None:
            logger.warning("Invalid API key: %s", _mask_key(api_key))
            return JSONResponse(
                content={
                    "error": "Invalid API key",
                    "message": "The provided API key is not valid or has been revoked",
                    "code": "AUTH_502",
                    "hint": "Check your key or create a new one: mysql-to-sheets api-key create --name=default",
                },
                status_code=401,
            )

        request.state.api_key = api_key
        request.state.api_key_info = key_info

        # Record API key usage for analytics
        self._record_usage(key_info["id"])

        return await call_next(request)

    def _record_usage(self, api_key_id: int) -> None:
        """Record API key usage for analytics.

        Called after successful authentication. Non-blocking - errors are logged
        but don't affect request processing.

        Args:
            api_key_id: ID of the authenticated API key.
        """
        if not self.db_path:
            return

        try:
            from mysql_to_sheets.models.api_key_usage import get_api_key_usage_repository

            usage_repo = get_api_key_usage_repository(self.db_path)
            usage_repo.record_request(api_key_id)
        except Exception as e:
            # Don't let usage tracking failures affect request processing
            logger.debug("Failed to record API key usage: %s", e)


__all__ = ["AuthMiddleware"]
