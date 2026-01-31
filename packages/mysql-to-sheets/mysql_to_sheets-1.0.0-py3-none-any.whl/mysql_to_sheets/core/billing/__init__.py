"""Billing, tier, license, and usage management.

This package consolidates all billing-related functionality:
- Subscription tier management and limits
- License key validation (RS256 JWT)
- Trial period management
- Usage tracking and metering
- Tier caching for performance

Example:
    >>> from mysql_to_sheets.core.billing import Tier, TIER_LIMITS, validate_license
    >>>
    >>> # Check tier limits
    >>> limits = TIER_LIMITS[Tier.PRO]
    >>> print(limits.max_configs)  # 10
    >>>
    >>> # Validate a license key
    >>> info = validate_license("eyJhbGciOiJSUzI1NiI...")
    >>> print(info.tier)  # Tier.PRO
"""

# Re-export from tier module
from mysql_to_sheets.core.billing.tier import (
    FEATURE_TIERS,
    TIER_LIMITS,
    Tier,
    TierLimits,
    check_feature_access,
    check_quota,
    enforce_quota,
    get_feature_tier,
    get_tier_display_info,
    get_tier_from_license,
    get_tier_limits,
    get_upgrade_suggestions,
    require_tier as require_tier_decorator,
    set_tier_callback,
    tier_allows,
)

# Re-export from license module
from mysql_to_sheets.core.billing.license import (
    DEFAULT_LICENSE_PUBLIC_KEY,
    LICENSE_JWT_ALGORITHM,
    LicenseInfo,
    LicenseKeyRegistry,
    LicensePublicKey,
    LicenseStatus,
    fetch_remote_keys,
    get_effective_tier,
    get_key_registry,
    get_license_info_from_config,
    is_license_valid,
    require_tier,
    require_valid_license,
    reset_key_registry,
    validate_license,
)

# Re-export from trial module
from mysql_to_sheets.core.billing.trial import (
    TrialInfo,
    TrialStatus,
    check_expiring_trials,
    check_trial_status,
    convert_trial,
    expire_trial,
    get_trial_days_remaining,
    get_trial_tier_for_feature_check,
    is_trial_active,
    start_trial,
)

# Re-export from usage_tracking module
from mysql_to_sheets.core.billing.usage_tracking import (
    check_usage_threshold,
    get_current_usage,
    get_usage_history,
    get_usage_summary,
    record_api_call,
    record_sync_usage,
)

# Re-export from tier_cache module
from mysql_to_sheets.core.billing.tier_cache import (
    TierCache,
    get_tier_cache,
    is_tier_cache_enabled,
    reset_tier_cache,
)

__all__ = [
    # Tier
    "Tier",
    "TierLimits",
    "TIER_LIMITS",
    "FEATURE_TIERS",
    "get_tier_limits",
    "get_feature_tier",
    "tier_allows",
    "check_feature_access",
    "check_quota",
    "enforce_quota",
    "require_tier_decorator",
    "set_tier_callback",
    "get_tier_from_license",
    "get_tier_display_info",
    "get_upgrade_suggestions",
    # License
    "LicenseStatus",
    "LicenseInfo",
    "LicensePublicKey",
    "LicenseKeyRegistry",
    "DEFAULT_LICENSE_PUBLIC_KEY",
    "LICENSE_JWT_ALGORITHM",
    "validate_license",
    "get_effective_tier",
    "is_license_valid",
    "get_license_info_from_config",
    "require_valid_license",
    "require_tier",
    "get_key_registry",
    "reset_key_registry",
    "fetch_remote_keys",
    # Trial
    "TrialStatus",
    "TrialInfo",
    "start_trial",
    "check_trial_status",
    "get_trial_days_remaining",
    "is_trial_active",
    "expire_trial",
    "convert_trial",
    "check_expiring_trials",
    "get_trial_tier_for_feature_check",
    # Usage
    "record_sync_usage",
    "record_api_call",
    "get_usage_summary",
    "get_current_usage",
    "get_usage_history",
    "check_usage_threshold",
    # Tier Cache
    "TierCache",
    "get_tier_cache",
    "reset_tier_cache",
    "is_tier_cache_enabled",
]
