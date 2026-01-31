"""Tier management for subscription-based feature gating.

This module provides the tier system for monetization, including:
- Tier enum with FREE, PRO, BUSINESS, ENTERPRISE levels
- Tier limits configuration
- Feature-to-tier mapping
- Enforcement decorators and utilities

Example:
    >>> from mysql_to_sheets.core.tier import Tier, TIER_LIMITS, require_tier
    >>>
    >>> # Check tier limits
    >>> limits = TIER_LIMITS[Tier.PRO]
    >>> print(limits.max_configs)  # 10
    >>>
    >>> # Decorate a function to require a tier
    >>> @require_tier("reverse_sync")
    ... def reverse_sync(org_id: int):
    ...     pass
"""

import functools
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, TypeVar

from mysql_to_sheets.core.exceptions import TierError


class Tier(str, Enum):
    """Subscription tier levels.

    Each tier unlocks additional features and higher limits.
    Tiers are ordered: FREE < PRO < BUSINESS < ENTERPRISE.
    """

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

    def __lt__(self, other: object) -> bool:
        """Compare tiers by level."""
        if not isinstance(other, Tier):
            return NotImplemented
        order = [Tier.FREE, Tier.PRO, Tier.BUSINESS, Tier.ENTERPRISE]
        return order.index(self) < order.index(other)

    def __le__(self, other: object) -> bool:
        """Compare tiers by level."""
        if not isinstance(other, Tier):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        """Compare tiers by level."""
        if not isinstance(other, Tier):
            return NotImplemented
        return not self <= other

    def __ge__(self, other: object) -> bool:
        """Compare tiers by level."""
        if not isinstance(other, Tier):
            return NotImplemented
        return not self < other


@dataclass(frozen=True)
class TierLimits:
    """Resource limits for a subscription tier.

    Attributes:
        max_configs: Maximum number of sync configurations.
        max_users: Maximum number of users in the organization.
        history_days: Number of days to retain sync history.
        max_schedules: Maximum number of scheduled jobs.
        max_webhooks: Maximum number of webhook subscriptions.
        api_requests_per_minute: API rate limit (requests per minute).
        snapshot_retention_count: Maximum snapshots to retain.
        audit_retention_days: Days to retain audit logs.
    """

    max_configs: int | None  # None = unlimited
    max_users: int | None
    history_days: int | None
    max_schedules: int | None = None
    max_webhooks: int | None = None
    api_requests_per_minute: int = 60
    snapshot_retention_count: int | None = None
    audit_retention_days: int | None = None


# Tier limits configuration
TIER_LIMITS: dict[Tier, TierLimits] = {
    Tier.FREE: TierLimits(
        max_configs=1,
        max_users=1,
        history_days=7,
        max_schedules=0,  # No scheduling in free tier
        max_webhooks=0,
        api_requests_per_minute=10,
        snapshot_retention_count=0,
        audit_retention_days=0,
    ),
    Tier.PRO: TierLimits(
        max_configs=10,
        max_users=1,
        history_days=30,
        max_schedules=5,
        max_webhooks=3,
        api_requests_per_minute=60,
        snapshot_retention_count=5,
        audit_retention_days=30,
    ),
    Tier.BUSINESS: TierLimits(
        max_configs=50,
        max_users=5,
        history_days=90,
        max_schedules=25,
        max_webhooks=10,
        api_requests_per_minute=120,
        snapshot_retention_count=10,
        audit_retention_days=90,
    ),
    Tier.ENTERPRISE: TierLimits(
        max_configs=None,  # Unlimited
        max_users=None,
        history_days=None,
        max_schedules=None,
        max_webhooks=None,
        api_requests_per_minute=300,
        snapshot_retention_count=None,
        audit_retention_days=None,
    ),
}


# Feature-to-tier mapping
FEATURE_TIERS: dict[str, Tier] = {
    # Free tier features (available to all)
    "sync": Tier.FREE,
    "validate": Tier.FREE,
    "test_connection": Tier.FREE,
    "pii_detection": Tier.FREE,  # Basic PII detection for all tiers
    "pii_hash_transform": Tier.FREE,  # Basic hash transform for all tiers
    # Pro tier features
    "scheduler": Tier.PRO,
    "incremental_sync": Tier.PRO,
    "column_mapping": Tier.PRO,
    "notifications": Tier.PRO,
    "reverse_sync": Tier.PRO,
    "data_quality": Tier.PRO,
    "api_access": Tier.PRO,
    "streaming_sync": Tier.PRO,
    "schema_policy_additive": Tier.PRO,
    "schema_policy_flexible": Tier.PRO,
    "schema_policy_notify_only": Tier.PRO,
    "pii_redact_transform": Tier.PRO,  # Redact transform requires PRO
    "pii_partial_mask_transform": Tier.PRO,  # Partial mask requires PRO
    # Business tier features
    "multi_sheet": Tier.BUSINESS,
    "webhooks": Tier.BUSINESS,
    "snapshots": Tier.BUSINESS,
    "audit_logs": Tier.BUSINESS,
    "job_queue": Tier.BUSINESS,
    "freshness_sla": Tier.BUSINESS,
    "anomaly_detection": Tier.BUSINESS,
    "rbac": Tier.BUSINESS,
    "pii_org_policy": Tier.BUSINESS,  # Org-level PII policies
    "pii_audit_logging": Tier.BUSINESS,  # PII audit trail
    # Enterprise tier features
    "sso": Tier.ENTERPRISE,
    "saml": Tier.ENTERPRISE,
    "oidc": Tier.ENTERPRISE,
    "data_masking": Tier.ENTERPRISE,
    "custom_retention": Tier.ENTERPRISE,
    "api_versioning": Tier.ENTERPRISE,
    "white_labeling": Tier.ENTERPRISE,
    "unlimited_users": Tier.ENTERPRISE,
    "unlimited_configs": Tier.ENTERPRISE,
    "pii_block_unacknowledged": Tier.ENTERPRISE,  # Block sync without ack
}


def get_tier_limits(tier: Tier | str) -> TierLimits:
    """Get the resource limits for a tier.

    Args:
        tier: Tier enum value or string.

    Returns:
        TierLimits for the specified tier.

    Raises:
        ValueError: If tier is not recognized.
    """
    if isinstance(tier, str):
        try:
            tier = Tier(tier.lower())
        except ValueError:
            raise ValueError(f"Unknown tier: {tier}")
    return TIER_LIMITS[tier]


def get_feature_tier(feature: str) -> Tier:
    """Get the minimum tier required for a feature.

    Args:
        feature: Feature name.

    Returns:
        Minimum Tier required for the feature.

    Raises:
        ValueError: If feature is not recognized.
    """
    tier = FEATURE_TIERS.get(feature)
    if tier is None:
        raise ValueError(f"Unknown feature: {feature}")
    return tier


def tier_allows(current_tier: Tier | str, required_tier: Tier | str) -> bool:
    """Check if current tier allows access to a required tier level.

    Args:
        current_tier: The organization's current tier.
        required_tier: The tier required for the feature.

    Returns:
        True if current tier is equal to or higher than required tier.
    """
    if isinstance(current_tier, str):
        current_tier = Tier(current_tier.lower())
    if isinstance(required_tier, str):
        required_tier = Tier(required_tier.lower())
    return current_tier >= required_tier


def check_feature_access(current_tier: Tier | str, feature: str) -> bool:
    """Check if a tier has access to a feature.

    Args:
        current_tier: The organization's current tier.
        feature: Feature name to check.

    Returns:
        True if the tier has access to the feature.

    Raises:
        ValueError: If feature is not recognized.
    """
    required_tier = get_feature_tier(feature)
    return tier_allows(current_tier, required_tier)


def check_quota(
    current_tier: Tier | str,
    quota_type: str,
    current_count: int,
) -> tuple[bool, int | None]:
    """Check if an organization is within quota limits.

    Args:
        current_tier: The organization's current tier.
        quota_type: Type of quota to check (configs, users, schedules, webhooks).
        current_count: Current usage count.

    Returns:
        Tuple of (is_within_limit, limit_value).
        limit_value is None for unlimited quotas.

    Raises:
        ValueError: If quota_type is not recognized.
    """
    limits = get_tier_limits(current_tier)

    quota_map = {
        "configs": limits.max_configs,
        "users": limits.max_users,
        "schedules": limits.max_schedules,
        "webhooks": limits.max_webhooks,
    }

    if quota_type not in quota_map:
        raise ValueError(f"Unknown quota type: {quota_type}")

    limit = quota_map[quota_type]
    if limit is None:
        return True, None
    return current_count < limit, limit


def enforce_quota(
    current_tier: Tier | str,
    quota_type: str,
    current_count: int,
    organization_id: int | None = None,
) -> None:
    """Enforce quota limits, raising TierError if exceeded.

    Args:
        current_tier: The organization's current tier.
        quota_type: Type of quota to check.
        current_count: Current usage count.
        organization_id: Optional organization ID for error context.

    Raises:
        TierError: If quota is exceeded.
    """
    is_within, limit = check_quota(current_tier, quota_type, current_count)
    if not is_within:
        tier_str = current_tier.value if isinstance(current_tier, Tier) else current_tier
        raise TierError(
            message=f"Quota exceeded: {quota_type} limit is {limit} for {tier_str} tier",
            current_tier=tier_str,
            quota_type=quota_type,
            quota_limit=limit,
            quota_used=current_count,
        )


# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


def require_tier(feature: str) -> Callable[[F], F]:
    """Decorator to enforce tier requirements for a feature.

    The decorated function must accept an `org_id` keyword argument
    or positional argument that identifies the organization.

    Args:
        feature: Feature name that requires tier check.

    Returns:
        Decorator function.

    Example:
        >>> @require_tier("reverse_sync")
        ... def reverse_sync(data: dict, org_id: int) -> dict:
        ...     # This function requires PRO tier or higher
        ...     return {"synced": True}
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get organization ID from kwargs or positional args
            org_id = kwargs.get("org_id") or kwargs.get("organization_id")

            if org_id is None:
                # Try to find in positional args via function signature
                import inspect

                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                for i, param in enumerate(params):
                    if param in ("org_id", "organization_id") and i < len(args):
                        org_id = args[i]
                        break

            if org_id is None:
                raise TierError(
                    message="Organization ID required for tier check",
                    feature=feature,
                )

            # Get organization tier - must be provided via get_organization_tier callback
            tier = _get_organization_tier(org_id)
            required = get_feature_tier(feature)

            if not tier_allows(tier, required):
                raise TierError(
                    message=f"Feature '{feature}' requires {required.value} tier or higher",
                    required_tier=required.value,
                    current_tier=tier.value if isinstance(tier, Tier) else tier,
                    feature=feature,
                )

            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


# Callback for getting organization tier
# This should be set by the application to integrate with the organization repository
_tier_callback: Callable[[int], Tier] | None = None


def set_tier_callback(callback: Callable[[int], Tier]) -> None:
    """Set the callback function for getting organization tier.

    This allows the tier module to look up organization tiers without
    directly depending on the organization repository.

    Args:
        callback: Function that takes org_id and returns Tier.

    Example:
        >>> def get_org_tier(org_id: int) -> Tier:
        ...     org = org_repository.get_by_id(org_id)
        ...     return Tier(org.subscription_tier)
        >>> set_tier_callback(get_org_tier)
    """
    global _tier_callback
    _tier_callback = callback


def _get_organization_tier(org_id: int) -> Tier:
    """Get the tier for an organization.

    Uses the registered callback to look up the organization tier.
    Also checks for active trial periods, which grant PRO tier access.
    Results are cached in memory to reduce database lookups.

    Args:
        org_id: Organization ID.

    Returns:
        Tier for the organization.

    Raises:
        TierError: If no callback is registered.
    """
    from mysql_to_sheets.core.billing.tier_cache import get_tier_cache, is_tier_cache_enabled

    # Check cache first (if enabled)
    if is_tier_cache_enabled():
        cache = get_tier_cache()
        cached_tier = cache.get(org_id)
        if cached_tier is not None:
            return cached_tier

    # Lookup tier from callback or trial
    tier: Tier | None = None

    if _tier_callback is None:
        # Check for trial tier when no callback is set
        try:
            from mysql_to_sheets.core.billing.trial import get_trial_tier_for_feature_check

            tier_str = get_trial_tier_for_feature_check(org_id)
            tier = Tier(tier_str.lower())
        except (ImportError, OSError, RuntimeError, ValueError) as e:
            # Fail-closed: deny paid features when tier cannot be determined
            raise TierError(
                message=f"Unable to determine organization tier: {e}",
            ) from e
    else:
        tier = _tier_callback(org_id)

    # Cache the result (if enabled)
    if is_tier_cache_enabled() and tier is not None:
        cache = get_tier_cache()
        cache.set(org_id, tier)

    return tier


def get_tier_from_license() -> Tier:
    """Get subscription tier from license key.

    Reads the LICENSE_KEY from configuration and validates it to
    determine the subscription tier. If no license key is configured
    or the license is invalid/expired, returns FREE tier.

    This function enables offline tier validation without requiring
    a database lookup or network call.

    Returns:
        Tier based on license key, or FREE if no valid license.

    Example:
        >>> tier = get_tier_from_license()
        >>> if tier >= Tier.PRO:
        ...     print("PRO features enabled")
    """
    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.core.billing.license import get_effective_tier, validate_license

    config = get_config()
    if not config.license_key:
        return Tier.FREE

    license_info = validate_license(
        config.license_key,
        config.license_public_key or None,
        config.license_offline_grace_days,
    )
    return get_effective_tier(license_info)


def get_tier_display_info(tier: Tier) -> dict[str, Any]:
    """Get display information for a tier.

    Returns user-friendly information about a tier including
    its limits and available features.

    Args:
        tier: Tier to get information for.

    Returns:
        Dictionary with tier information.
    """
    limits = get_tier_limits(tier)
    features = [f for f, t in FEATURE_TIERS.items() if tier_allows(tier, t)]

    return {
        "name": tier.value.title(),
        "tier": tier.value,
        "limits": {
            "configs": limits.max_configs if limits.max_configs is not None else "Unlimited",
            "users": limits.max_users if limits.max_users is not None else "Unlimited",
            "history_days": limits.history_days if limits.history_days is not None else "Unlimited",
            "schedules": limits.max_schedules if limits.max_schedules is not None else "Unlimited",
            "webhooks": limits.max_webhooks if limits.max_webhooks is not None else "Unlimited",
            "api_requests_per_minute": limits.api_requests_per_minute,
        },
        "features": features,
    }


def get_upgrade_suggestions(current_tier: Tier, denied_feature: str) -> dict[str, Any]:
    """Get upgrade suggestions when a feature is denied.

    Args:
        current_tier: The organization's current tier.
        denied_feature: The feature that was denied.

    Returns:
        Dictionary with upgrade information.
    """
    required_tier = get_feature_tier(denied_feature)
    required_limits = get_tier_limits(required_tier)
    current_limits = get_tier_limits(current_tier)

    # Get additional features available in the required tier
    additional_features = [
        f
        for f, t in FEATURE_TIERS.items()
        if tier_allows(required_tier, t) and not tier_allows(current_tier, t)
    ]

    return {
        "current_tier": current_tier.value,
        "required_tier": required_tier.value,
        "denied_feature": denied_feature,
        "additional_features": additional_features,
        "limit_increases": {
            "configs": _format_limit_increase(
                current_limits.max_configs, required_limits.max_configs
            ),
            "users": _format_limit_increase(current_limits.max_users, required_limits.max_users),
            "history_days": _format_limit_increase(
                current_limits.history_days, required_limits.history_days
            ),
        },
    }


def _format_limit_increase(current: int | None, new: int | None) -> str:
    """Format a limit increase for display."""
    if current is None:
        return "Unlimited"
    if new is None:
        return f"{current} → Unlimited"
    if new > current:
        return f"{current} → {new}"
    return str(current)
