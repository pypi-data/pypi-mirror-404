"""Backward compatibility shim - import from core.billing instead.

This module re-exports all public APIs from the billing package.
New code should import directly from mysql_to_sheets.core.billing.

Example (preferred):
    >>> from mysql_to_sheets.core.billing import record_sync_usage

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.usage_tracking import record_sync_usage

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.billing.usage_tracking instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.usage_tracking",
    "mysql_to_sheets.core.billing.usage_tracking",
)

from mysql_to_sheets.core.billing.usage_tracking import (
    _get_operations_limit,
    _get_rows_limit,
    check_usage_threshold,
    get_current_usage,
    get_usage_history,
    get_usage_summary,
    record_api_call,
    record_sync_usage,
)

__all__ = [
    "record_sync_usage",
    "record_api_call",
    "get_usage_summary",
    "get_current_usage",
    "get_usage_history",
    "check_usage_threshold",
    "_get_rows_limit",
    "_get_operations_limit",
]
