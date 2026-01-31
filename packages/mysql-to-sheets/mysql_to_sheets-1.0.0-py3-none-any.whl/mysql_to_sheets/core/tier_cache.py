"""Backward compatibility shim - import from core.billing instead.

This module re-exports all public APIs from the billing package.
New code should import directly from mysql_to_sheets.core.billing.

Example (preferred):
    >>> from mysql_to_sheets.core.billing import get_tier_cache, TierCache

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.tier_cache import get_tier_cache, TierCache

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.billing.tier_cache instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.tier_cache",
    "mysql_to_sheets.core.billing.tier_cache",
)

from mysql_to_sheets.core.billing.tier_cache import (
    TierCache,
    get_tier_cache,
    is_tier_cache_enabled,
    reset_tier_cache,
)

__all__ = [
    "TierCache",
    "get_tier_cache",
    "reset_tier_cache",
    "is_tier_cache_enabled",
]
