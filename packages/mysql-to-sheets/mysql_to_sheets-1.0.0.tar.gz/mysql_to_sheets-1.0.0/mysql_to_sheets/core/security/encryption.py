"""Fernet encryption helpers for secure credential storage.

Provides encryption/decryption functions for sensitive data like
database passwords and API keys stored in the integrations table.

Key Management:
- Encryption key is loaded from INTEGRATION_ENCRYPTION_KEY environment variable
- Key must be a 32-byte URL-safe base64 encoded string (Fernet standard)
- Generate a new key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Security:
- Uses Fernet (AES-128-CBC + HMAC-SHA256)
- Authenticated encryption (integrity + confidentiality)
- Each encryption includes timestamp for freshness
"""

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Lazy import to make cryptography optional
_fernet: Any = None
_fernet_checked = False


def _get_fernet() -> Any:
    """Get or create Fernet instance with lazy import.

    Returns:
        Fernet instance or None if unavailable.

    Raises:
        ImportError: If cryptography package is not installed.
        ValueError: If INTEGRATION_ENCRYPTION_KEY is not set or invalid.
    """
    global _fernet, _fernet_checked

    if _fernet_checked:
        return _fernet

    try:
        from cryptography.fernet import Fernet, InvalidToken  # noqa: F401
    except ImportError as e:
        _fernet_checked = True
        raise ImportError(
            "cryptography package is required for integration encryption. "
            "Install with: pip install cryptography>=42.0"
        ) from e

    key = os.getenv("INTEGRATION_ENCRYPTION_KEY")
    if not key:
        _fernet_checked = True
        raise ValueError(
            "INTEGRATION_ENCRYPTION_KEY environment variable is required "
            "for credential encryption. Generate a key with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    try:
        _fernet = Fernet(key.encode())
    except Exception as e:
        _fernet_checked = True
        raise ValueError(
            f"Invalid INTEGRATION_ENCRYPTION_KEY: {e}. "
            "Key must be a 32-byte URL-safe base64 encoded string."
        ) from e

    _fernet_checked = True
    return _fernet


def is_encryption_available() -> bool:
    """Check if encryption is available and properly configured.

    Returns:
        True if encryption can be used, False otherwise.
    """
    try:
        _get_fernet()
        return True
    except (ImportError, ValueError):
        return False


def encrypt_credentials(credentials: dict[str, Any]) -> str:
    """Encrypt credentials dictionary to a secure string.

    Args:
        credentials: Dictionary of sensitive values to encrypt.
            Typical keys: user, password, api_key, service_account_json

    Returns:
        Base64-encoded encrypted string.

    Raises:
        ImportError: If cryptography is not installed.
        ValueError: If encryption key is not configured.

    Example::

        credentials = {
            "user": "dbuser",
            "password": "secret123",
        }
        encrypted = encrypt_credentials(credentials)
        # Store encrypted string in database
    """
    fernet = _get_fernet()

    # Serialize to JSON with sorted keys for consistency
    plaintext = json.dumps(credentials, sort_keys=True, separators=(",", ":"))

    # Encrypt and return as string
    encrypted = fernet.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_credentials(encrypted_data: str) -> dict[str, Any]:
    """Decrypt credentials from encrypted string.

    Args:
        encrypted_data: Base64-encoded encrypted string from encrypt_credentials().

    Returns:
        Decrypted credentials dictionary.

    Raises:
        ImportError: If cryptography is not installed.
        ValueError: If encryption key is not configured or decryption fails.

    Example::

        encrypted = "gAAAAABn..."  # From database
        credentials = decrypt_credentials(encrypted)
        password = credentials.get("password")
    """
    fernet = _get_fernet()

    try:
        decrypted = fernet.decrypt(encrypted_data.encode("utf-8"))
        return json.loads(decrypted.decode("utf-8"))
    except Exception as e:
        # Don't expose details about decryption failures
        logger.warning(f"Failed to decrypt credentials: {type(e).__name__}")
        raise ValueError("Failed to decrypt credentials. Key may have changed.") from e


def encrypt_value(value: str) -> str:
    """Encrypt a single string value.

    Args:
        value: String to encrypt.

    Returns:
        Base64-encoded encrypted string.
    """
    fernet = _get_fernet()
    encrypted = fernet.encrypt(value.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_value(encrypted_data: str) -> str:
    """Decrypt a single string value.

    Args:
        encrypted_data: Base64-encoded encrypted string.

    Returns:
        Decrypted string.

    Raises:
        ValueError: If decryption fails.
    """
    fernet = _get_fernet()

    try:
        decrypted = fernet.decrypt(encrypted_data.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception as e:
        logger.warning(f"Failed to decrypt value: {type(e).__name__}")
        raise ValueError("Failed to decrypt value. Key may have changed.") from e


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key.

    Returns:
        URL-safe base64 encoded key string.

    Raises:
        ImportError: If cryptography is not installed.
    """
    try:
        from cryptography.fernet import Fernet
    except ImportError as e:
        raise ImportError(
            "cryptography package is required. Install with: pip install cryptography>=42.0"
        ) from e

    return Fernet.generate_key().decode("utf-8")


def rotate_credentials_key(
    encrypted_data: str,
    old_key: str,
    new_key: str,
) -> str:
    """Re-encrypt credentials with a new key.

    Used for key rotation. Decrypts with old key and encrypts with new key.

    Args:
        encrypted_data: Currently encrypted credentials.
        old_key: Current encryption key.
        new_key: New encryption key to use.

    Returns:
        Credentials encrypted with new key.

    Raises:
        ValueError: If decryption with old key fails.
    """
    try:
        from cryptography.fernet import Fernet
    except ImportError as e:
        raise ImportError(
            "cryptography package is required. Install with: pip install cryptography>=42.0"
        ) from e

    # Decrypt with old key
    old_fernet = Fernet(old_key.encode())
    try:
        decrypted = old_fernet.decrypt(encrypted_data.encode("utf-8"))
    except Exception as e:
        raise ValueError(f"Failed to decrypt with old key: {e}") from e

    # Encrypt with new key
    new_fernet = Fernet(new_key.encode())
    encrypted = new_fernet.encrypt(decrypted)
    return encrypted.decode("utf-8")


def reset_encryption() -> None:
    """Reset encryption state. For testing."""
    global _fernet, _fernet_checked
    _fernet = None
    _fernet_checked = False
