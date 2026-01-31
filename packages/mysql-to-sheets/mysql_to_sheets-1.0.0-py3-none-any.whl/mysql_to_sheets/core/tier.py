"""Backward compatibility shim - import from core.billing instead.

This module re-exports all public APIs from the billing package.
New code should import directly from mysql_to_sheets.core.billing.

Example (preferred):
    >>> from mysql_to_sheets.core.billing import Tier, TIER_LIMITS

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.tier import Tier, TIER_LIMITS

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.billing.tier instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.tier",
    "mysql_to_sheets.core.billing.tier",
)

from mysql_to_sheets.core.billing.tier import (
    FEATURE_TIERS,
    TIER_LIMITS,
    Tier,
    TierLimits,
    _get_organization_tier,
    check_feature_access,
    check_quota,
    enforce_quota,
    get_feature_tier,
    get_tier_display_info,
    get_tier_from_license,
    get_tier_limits,
    get_upgrade_suggestions,
    require_tier,
    set_tier_callback,
    tier_allows,
)

# Re-export TierError from exceptions for backward compatibility
from mysql_to_sheets.core.exceptions import TierError

__all__ = [
    "Tier",
    "TierLimits",
    "TierError",
    "TIER_LIMITS",
    "FEATURE_TIERS",
    "get_tier_limits",
    "get_feature_tier",
    "tier_allows",
    "check_feature_access",
    "check_quota",
    "enforce_quota",
    "require_tier",
    "set_tier_callback",
    "get_tier_from_license",
    "get_tier_display_info",
    "get_upgrade_suggestions",
    "_get_organization_tier",
]
