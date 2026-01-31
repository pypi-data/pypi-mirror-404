"""Backward compatibility utilities for deprecated imports.

This module provides utilities for emitting deprecation warnings when
code imports from legacy shim modules instead of their canonical locations.

Shim modules in core/ are deprecated and will be removed in a future release.
Use the canonical import paths instead:

    # Security (preferred):
    from mysql_to_sheets.core.security import auth, rbac
    from mysql_to_sheets.core.security.auth import hash_password
    from mysql_to_sheets.core.security.rbac import Permission

    # Billing (preferred):
    from mysql_to_sheets.core.billing import tier, license, trial
    from mysql_to_sheets.core.billing.tier import Tier, TIER_LIMITS

    # History (preferred):
    from mysql_to_sheets.core.history import history, snapshots, rollback
    from mysql_to_sheets.core.history.snapshots import create_snapshot

    # PII (preferred):
    from mysql_to_sheets.core.pii import types, detection, transform
    from mysql_to_sheets.core.pii.detection import detect_pii_in_columns

    # Extracted packages (preferred - install separately):
    # pip install tla-errors tla-incremental-sync tla-sql-guard tla-retry tla-gspread-utils
    from tla_errors import SyncError, ErrorCode, get_remediation_hint
    from tla_incremental_sync import IncrementalConfig, build_incremental_query
    from tla_sql_guard import validate_sql_query, generate_api_key, RateLimiter
    from tla_retry import retry, CircuitBreaker, RetryConfig
    from tla_gspread_utils import parse_sheet_id, create_worksheet
"""

import warnings
from typing import Any


def emit_deprecation_warning(
    old_module: str,
    new_module: str,
    stacklevel: int = 3,
) -> None:
    """Emit a deprecation warning for a legacy import.

    Args:
        old_module: The deprecated module path (e.g., "mysql_to_sheets.core.auth").
        new_module: The new canonical module path (e.g., "mysql_to_sheets.core.security.auth").
        stacklevel: Stack level for the warning (default 3 to point at the user's import).
    """
    warnings.warn(
        f"Importing from '{old_module}' is deprecated and will be removed in a future release. "
        f"Use '{new_module}' instead.",
        DeprecationWarning,
        stacklevel=stacklevel,
    )


# Mapping of deprecated shim modules to their canonical locations
SHIM_MODULES: dict[str, str] = {
    "mysql_to_sheets.core.auth": "mysql_to_sheets.core.security.auth",
    "mysql_to_sheets.core.rbac": "mysql_to_sheets.core.security.rbac",
    "mysql_to_sheets.core.security": "mysql_to_sheets.core.security.sql_validation",
    "mysql_to_sheets.core.tier": "mysql_to_sheets.core.billing.tier",
    "mysql_to_sheets.core.license": "mysql_to_sheets.core.billing.license",
    "mysql_to_sheets.core.trial": "mysql_to_sheets.core.billing.trial",
    "mysql_to_sheets.core.tier_cache": "mysql_to_sheets.core.billing.tier_cache",
    "mysql_to_sheets.core.usage_tracking": "mysql_to_sheets.core.billing.usage_tracking",
    "mysql_to_sheets.core.history": "mysql_to_sheets.core.history.history",
    "mysql_to_sheets.core.snapshots": "mysql_to_sheets.core.history.snapshots",
    "mysql_to_sheets.core.rollback": "mysql_to_sheets.core.history.rollback",
    "mysql_to_sheets.core.pii": "mysql_to_sheets.core.pii.types",
    "mysql_to_sheets.core.pii_detection": "mysql_to_sheets.core.pii.detection",
    "mysql_to_sheets.core.pii_transform": "mysql_to_sheets.core.pii.transform",
}

# Mapping of modules to their extracted standalone packages
# These modules are still available in mysql_to_sheets.core for backward
# compatibility, but users can install the standalone packages instead.
EXTRACTED_PACKAGES: dict[str, str] = {
    "mysql_to_sheets.core.exceptions": "tla_errors",
    "mysql_to_sheets.core.incremental": "tla_incremental_sync",
    "mysql_to_sheets.core.security.sql_validation": "tla_sql_guard",
    "mysql_to_sheets.core.retry": "tla_retry",
    "mysql_to_sheets.core.sheets_utils": "tla_gspread_utils",
}


def get_canonical_module(deprecated_module: str) -> str | None:
    """Get the canonical module path for a deprecated shim module.

    Args:
        deprecated_module: The deprecated module path.

    Returns:
        The canonical module path, or None if not a known shim.
    """
    return SHIM_MODULES.get(deprecated_module)
