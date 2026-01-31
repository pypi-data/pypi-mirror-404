"""Backward compatibility shim - import from core.billing instead.

This module re-exports all public APIs from the billing package.
New code should import directly from mysql_to_sheets.core.billing.

Example (preferred):
    >>> from mysql_to_sheets.core.billing import start_trial, TrialStatus

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.trial import start_trial, TrialStatus

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.billing.trial instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.trial",
    "mysql_to_sheets.core.billing.trial",
)

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

__all__ = [
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
]
