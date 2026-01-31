"""Backward compatibility shim - import from core.security instead.

This module re-exports all public APIs from the security package.
New code should import directly from mysql_to_sheets.core.security.

Example (preferred):
    >>> from mysql_to_sheets.core.security import encrypt_credentials

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.encryption import encrypt_credentials
"""

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

__all__ = [
    "is_encryption_available",
    "encrypt_credentials",
    "decrypt_credentials",
    "encrypt_value",
    "decrypt_value",
    "generate_encryption_key",
    "rotate_credentials_key",
    "reset_encryption",
]
