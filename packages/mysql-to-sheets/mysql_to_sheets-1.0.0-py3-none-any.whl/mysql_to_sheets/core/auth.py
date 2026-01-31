"""Backward compatibility shim - import from core.security instead.

This module re-exports all public APIs from the security package.
New code should import directly from mysql_to_sheets.core.security.

Example (preferred):
    >>> from mysql_to_sheets.core.security import hash_password, verify_token

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.auth import hash_password, verify_token

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.security.auth instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.auth",
    "mysql_to_sheets.core.security.auth",
)

from mysql_to_sheets.core.security.auth import (
    AuthConfig,
    TokenPayload,
    authenticate_user,
    blacklist_token,
    check_account_locked,
    cleanup_expired_tokens,
    clear_account_lockout,
    clear_token_blacklist,
    create_access_token,
    create_refresh_token,
    generate_password_reset_token,
    get_auth_config,
    hash_password,
    is_token_blacklisted,
    record_login_attempt,
    reset_auth_config,
    validate_password_strength,
    verify_password,
    verify_password_reset_token,
    verify_token,
)

__all__ = [
    "TokenPayload",
    "AuthConfig",
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "check_account_locked",
    "record_login_attempt",
    "clear_account_lockout",
    "authenticate_user",
    "generate_password_reset_token",
    "verify_password_reset_token",
    "blacklist_token",
    "is_token_blacklisted",
    "cleanup_expired_tokens",
    "clear_token_blacklist",
    "get_auth_config",
    "reset_auth_config",
]
