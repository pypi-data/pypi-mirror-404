"""Tier enforcement middleware for API endpoints.

This middleware checks tier requirements and quotas for API requests,
ensuring organizations can only access features available in their tier.

Example:
    >>> from mysql_to_sheets.api.middleware.tier import TierMiddleware
    >>>
    >>> app.add_middleware(
    ...     TierMiddleware,
    ...     enabled=True,
    ...     db_path="./data/tenant.db",
    ... )
"""

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from mysql_to_sheets.core.tier import (
    FEATURE_TIERS,
    Tier,
    get_tier_limits,
    get_upgrade_suggestions,
    tier_allows,
)

logger = logging.getLogger("mysql_to_sheets.api")


# Map API paths to feature requirements
PATH_FEATURE_MAP: dict[str, str] = {
    # Pro tier features
    "/api/v1/schedules": "scheduler",
    "/api/v1/sync/streaming": "streaming_sync",
    "/api/v1/reverse-sync": "reverse_sync",
    "/api/v1/quality": "data_quality",
    # Business tier features
    "/api/v1/webhooks": "webhooks",
    "/api/v1/snapshots": "snapshots",
    "/api/v1/rollback": "snapshots",
    "/api/v1/audit": "audit_logs",
    "/api/v1/jobs": "job_queue",
    "/api/v1/freshness": "freshness_sla",
    "/api/v1/multi-sheet": "multi_sheet",
    # Enterprise tier features
    "/api/v1/sso": "sso",
    "/api/v1/masking": "data_masking",
}


class TierMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce tier requirements on API endpoints.

    Checks if the organization's tier allows access to the requested
    feature and returns a 403 error with upgrade information if not.

    Attributes:
        enabled: Whether tier enforcement is enabled.
        db_path: Path to the tenant database.
        exempt_paths: Paths that don't require tier checks.
    """

    def __init__(
        self,
        app: Any,
        enabled: bool = True,
        db_path: str | None = None,
        exempt_paths: list[str] | None = None,
    ) -> None:
        """Initialize TierMiddleware.

        Args:
            app: ASGI application.
            enabled: Whether tier enforcement is enabled.
            db_path: Path to tenant database for organization lookups.
            exempt_paths: Paths that don't require tier checks.
        """
        super().__init__(app)
        self.enabled = enabled
        self.db_path = db_path
        self.exempt_paths = exempt_paths or [
            "/api/v1/health",
            "/api/v1/metrics",
            "/api/v1/sync",  # Basic sync is always allowed
            "/api/v1/validate",
            "/api/v1/test",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    def _get_organization_tier(self, org_id: int) -> Tier:
        """Get the tier for an organization.

        Args:
            org_id: Organization ID.

        Returns:
            Tier for the organization.
        """
        if not self.db_path:
            return Tier.FREE

        try:
            from mysql_to_sheets.models.organizations import get_organization_repository

            repo = get_organization_repository(self.db_path)
            org = repo.get_by_id(org_id)
            if org:
                return org.tier
        except Exception as e:
            logger.warning(f"Failed to get organization tier: {e}")

        return Tier.FREE

    def _get_required_feature(self, path: str, method: str) -> str | None:
        """Get the required feature for an API path.

        Args:
            path: API path.
            method: HTTP method.

        Returns:
            Feature name if path requires a specific tier, None otherwise.
        """
        # Check exact matches first
        if path in PATH_FEATURE_MAP:
            return PATH_FEATURE_MAP[path]

        # Check prefix matches
        for prefix, feature in PATH_FEATURE_MAP.items():
            if path.startswith(prefix):
                return feature

        return None

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request through tier middleware.

        Args:
            request: Incoming request.
            call_next: Next middleware or route handler.

        Returns:
            Response from downstream handler or 403 error.
        """
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)

        path = request.url.path

        # Skip exempt paths
        if path in self.exempt_paths:
            return await call_next(request)

        for exempt in self.exempt_paths:
            if path.startswith(exempt):
                return await call_next(request)

        # Get required feature for this path
        required_feature = self._get_required_feature(path, request.method)
        if not required_feature:
            return await call_next(request)

        # Get organization ID from request state (set by OrganizationContextMiddleware)
        org_id = getattr(request.state, "organization_id", None)
        if org_id is None:
            # No org context, let the request proceed (will fail in route handler)
            return await call_next(request)

        # Get organization tier
        org_tier = self._get_organization_tier(org_id)

        # Check tier access
        required_tier = FEATURE_TIERS.get(required_feature, Tier.FREE)
        if not tier_allows(org_tier, required_tier):
            logger.info(
                f"Tier check failed for org {org_id}: "
                f"requires {required_tier.value}, has {org_tier.value}"
            )

            # Get upgrade suggestions
            suggestions = get_upgrade_suggestions(org_tier, required_feature)

            return Response(
                content=json.dumps(
                    {
                        "error": "TierError",
                        "message": f"Feature '{required_feature}' requires {required_tier.value} tier or higher",
                        "details": {
                            "current_tier": org_tier.value,
                            "required_tier": required_tier.value,
                            "feature": required_feature,
                        },
                        "upgrade_info": suggestions,
                    }
                ),
                status_code=403,
                media_type="application/json",
            )

        # Store tier in request state for downstream use
        request.state.organization_tier = org_tier

        return await call_next(request)


def require_feature(feature: str) -> Callable[..., Awaitable[None]]:
    """FastAPI dependency to require a specific feature tier.

    Use this as a route dependency to enforce tier requirements
    at the route level.

    Args:
        feature: Feature name that requires tier check.

    Returns:
        Dependency function.

    Example:
        >>> from fastapi import Depends
        >>>
        >>> @app.post("/reverse-sync")
        ... async def reverse_sync(
        ...     _: None = Depends(require_feature("reverse_sync")),
        ... ):
        ...     pass
    """
    from fastapi import HTTPException, Request

    async def dependency(request: Request) -> None:
        org_tier = getattr(request.state, "organization_tier", Tier.FREE)
        required_tier = FEATURE_TIERS.get(feature, Tier.FREE)

        if not tier_allows(org_tier, required_tier):
            suggestions = get_upgrade_suggestions(org_tier, feature)
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "TierError",
                    "message": f"Feature '{feature}' requires {required_tier.value} tier",
                    "current_tier": org_tier.value,
                    "required_tier": required_tier.value,
                    "upgrade_info": suggestions,
                },
            )

    return dependency


def get_tier_rate_limit(tier: Tier | str) -> int:
    """Get the API rate limit for a tier.

    Args:
        tier: Tier enum or string.

    Returns:
        Requests per minute limit.
    """
    limits = get_tier_limits(tier)
    return limits.api_requests_per_minute


class TierRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware that respects tier limits.

    Applies different rate limits based on the organization's tier.

    Attributes:
        enabled: Whether rate limiting is enabled.
        db_path: Path to tenant database.
    """

    def __init__(
        self,
        app: Any,
        enabled: bool = True,
        db_path: str | None = None,
    ) -> None:
        """Initialize TierRateLimitMiddleware.

        Args:
            app: ASGI application.
            enabled: Whether rate limiting is enabled.
            db_path: Path to tenant database.
        """
        super().__init__(app)
        self.enabled = enabled
        self.db_path = db_path
        self._limiters: dict[str, TierRateLimiter] = {}

    def _get_limiter(self, tier: Tier) -> "TierRateLimiter":
        """Get or create rate limiter for a tier.

        Args:
            tier: Tier to get limiter for.

        Returns:
            Rate limiter instance.
        """
        key = tier.value
        if key not in self._limiters:
            rpm = get_tier_rate_limit(tier)
            self._limiters[key] = TierRateLimiter(requests_per_minute=rpm)
        return self._limiters[key]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request through tier-aware rate limiting.

        Args:
            request: Incoming request.
            call_next: Next middleware or route handler.

        Returns:
            Response from downstream handler or 429 error.
        """
        if not self.enabled:
            return await call_next(request)

        # Get tier from request state
        tier = getattr(request.state, "organization_tier", Tier.FREE)
        org_id = getattr(request.state, "organization_id", None)

        if org_id is not None:
            limiter = self._get_limiter(tier)
            key = f"org:{org_id}"

            if not limiter.allow(key):
                return Response(
                    content=json.dumps(
                        {
                            "error": "RateLimitExceeded",
                            "message": f"Rate limit exceeded ({limiter.requests_per_minute} requests/minute)",
                            "details": {
                                "tier": tier.value,
                                "limit": limiter.requests_per_minute,
                            },
                        }
                    ),
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": "60"},
                )

        return await call_next(request)


class TierRateLimiter:
    """Simple token bucket rate limiter.

    Implements a sliding window rate limit with per-key tracking.
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute.
        """
        self.requests_per_minute = requests_per_minute
        self._buckets: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        """Check if a request is allowed.

        Args:
            key: Unique key for rate limiting (e.g., "org:123").

        Returns:
            True if request is allowed, False if rate limited.
        """
        import time

        now = time.time()
        window_start = now - 60  # 1 minute window

        # Initialize bucket if needed
        if key not in self._buckets:
            self._buckets[key] = []

        # Remove old timestamps
        self._buckets[key] = [ts for ts in self._buckets[key] if ts > window_start]

        # Check if under limit
        if len(self._buckets[key]) < self.requests_per_minute:
            self._buckets[key].append(now)
            return True

        return False

    def reset(self, key: str) -> None:
        """Reset rate limit for a key.

        Args:
            key: Key to reset.
        """
        if key in self._buckets:
            del self._buckets[key]
