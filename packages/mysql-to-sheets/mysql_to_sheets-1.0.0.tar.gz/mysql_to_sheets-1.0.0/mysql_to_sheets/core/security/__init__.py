"""Security, authentication, and authorization management.

This package consolidates security-related functionality:
- JWT authentication and token management
- Password hashing and validation
- Role-based access control (RBAC)
- Credential encryption (Fernet)
- SQL query validation and API key management

Example:
    >>> from mysql_to_sheets.core.security import (
    ...     hash_password, verify_password,
    ...     Permission, has_permission,
    ...     encrypt_credentials, decrypt_credentials,
    ... )
"""

# Re-export from auth module
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

# Re-export from rbac module
from mysql_to_sheets.core.security.rbac import (
    Permission,
    can_manage_role,
    get_assignable_roles,
    get_permissions,
    get_role_hierarchy,
    has_all_permissions,
    has_any_permission,
    has_permission,
    has_permission_group,
    is_higher_role,
    validate_role,
)

# Re-export from encryption module
from mysql_to_sheets.core.security.encryption import (
    decrypt_credentials,
    decrypt_value,
    encrypt_credentials,
    encrypt_value,
    generate_encryption_key,
    is_encryption_available,
    reset_encryption,
    rotate_credentials_key,
)

# Re-export from sql_validation module
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
    # Auth
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
    # RBAC
    "Permission",
    "has_permission",
    "get_permissions",
    "has_any_permission",
    "has_all_permissions",
    "get_role_hierarchy",
    "is_higher_role",
    "can_manage_role",
    "get_assignable_roles",
    "validate_role",
    "has_permission_group",
    # Encryption
    "is_encryption_available",
    "encrypt_credentials",
    "decrypt_credentials",
    "encrypt_value",
    "decrypt_value",
    "generate_encryption_key",
    "rotate_credentials_key",
    "reset_encryption",
    # SQL Validation & API Keys
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
