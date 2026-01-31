"""Backward compatibility shim - import from core.security instead.

This module re-exports SQL validation and API key functions.
New code should import directly from mysql_to_sheets.core.security.

Example (preferred):
    >>> from mysql_to_sheets.core.security import validate_sql_query

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.security import validate_sql_query

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.security.sql_validation instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.security",
    "mysql_to_sheets.core.security.sql_validation",
)

from mysql_to_sheets.core.security.sql_validation import (
    RateLimiter,
    SQLValidationResult,
    TokenBucket,
    generate_api_key,
    generate_api_key_salt,
    hash_api_key,
    hash_api_key_legacy,
    needs_rehash,
    sanitize_query_for_logging,
    validate_sql_query,
    verify_api_key,
)

__all__ = [
    "generate_api_key",
    "generate_api_key_salt",
    "hash_api_key",
    "hash_api_key_legacy",
    "verify_api_key",
    "needs_rehash",
    "SQLValidationResult",
    "validate_sql_query",
    "sanitize_query_for_logging",
    "TokenBucket",
    "RateLimiter",
]
