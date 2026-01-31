"""Secure credential storage using OS keychain.

This module provides cross-platform secure credential storage using
the OS native keychain:
    - macOS: Keychain
    - Windows: Credential Manager
    - Linux: Secret Service (GNOME Keyring, KWallet)

Security note:
    Credentials stored via this module are protected by the OS keychain,
    which encrypts them and ties access to the user's login session.
    This is more secure than storing credentials in plain text .env files.

Example:
    >>> from mysql_to_sheets.desktop.credentials import CredentialManager
    >>>
    >>> # Store credentials
    >>> CredentialManager.store_db_credentials(
    ...     host="localhost",
    ...     port=3306,
    ...     user="admin",
    ...     password="secret",
    ...     database="mydb",
    ... )
    >>>
    >>> # Retrieve a credential
    >>> password = CredentialManager.retrieve("db_password")
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Service name used for keyring storage
SERVICE_NAME = "MySQLToSheets"

# Credential keys for database configuration
DB_CREDENTIAL_KEYS = [
    "db_type",
    "db_host",
    "db_port",
    "db_user",
    "db_password",
    "db_name",
]

# Credential keys for Google Sheets configuration
SHEETS_CREDENTIAL_KEYS = [
    "google_sheet_id",
    "google_worksheet_name",
    "service_account_json",  # Stores the entire JSON content
]


def _check_keyring_available() -> bool:
    """Check if keyring is available on this system.

    Returns:
        True if keyring is available and functional.
    """
    try:
        import keyring

        # Try a test operation to verify the backend works
        keyring.get_keyring()
        return True
    except ImportError:
        logger.warning("keyring not installed. Install with: pip install keyring")
        return False
    except Exception as e:
        logger.warning(f"keyring backend unavailable: {e}")
        return False


class CredentialManager:
    """Secure credential storage using OS keychain.

    Provides static methods for storing and retrieving credentials
    from the OS native keychain. All operations are fail-safe - if
    the keychain is unavailable, operations return None/False rather
    than raising exceptions.
    """

    _keyring_available: bool | None = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if keychain storage is available.

        Returns:
            True if the OS keychain is available and functional.
        """
        if cls._keyring_available is None:
            cls._keyring_available = _check_keyring_available()
        return cls._keyring_available

    @staticmethod
    def store(key: str, value: str) -> bool:
        """Store a credential in the OS keychain.

        Args:
            key: Credential key name (e.g., "db_password").
            value: Credential value to store.

        Returns:
            True if stored successfully, False otherwise.
        """
        if not CredentialManager.is_available():
            return False

        try:
            import keyring

            keyring.set_password(SERVICE_NAME, key, value)
            logger.debug(f"Stored credential: {key}")
            return True
        except Exception as e:
            logger.warning(f"Failed to store credential {key}: {e}")
            return False

    @staticmethod
    def retrieve(key: str) -> str | None:
        """Retrieve a credential from the OS keychain.

        Args:
            key: Credential key name (e.g., "db_password").

        Returns:
            Credential value if found, None otherwise.
        """
        if not CredentialManager.is_available():
            return None

        try:
            import keyring

            value = keyring.get_password(SERVICE_NAME, key)
            if value:
                logger.debug(f"Retrieved credential: {key}")
            return value
        except Exception as e:
            logger.warning(f"Failed to retrieve credential {key}: {e}")
            return None

    @staticmethod
    def delete(key: str) -> bool:
        """Remove a credential from the OS keychain.

        Args:
            key: Credential key name to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        if not CredentialManager.is_available():
            return False

        try:
            import keyring

            keyring.delete_password(SERVICE_NAME, key)
            logger.debug(f"Deleted credential: {key}")
            return True
        except keyring.errors.PasswordDeleteError:
            # Credential didn't exist, which is fine
            return True
        except Exception as e:
            logger.warning(f"Failed to delete credential {key}: {e}")
            return False

    @staticmethod
    def store_db_credentials(
        host: str | None = None,
        port: int | str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
        db_type: str = "mysql",
    ) -> bool:
        """Store database credentials securely.

        Stores each credential field separately in the keychain.
        Only non-None values are stored.

        Args:
            host: Database hostname.
            port: Database port number.
            user: Database username.
            password: Database password.
            database: Database name.
            db_type: Database type (mysql, postgres, sqlite, mssql).

        Returns:
            True if all provided credentials were stored.
        """
        credentials: dict[str, Any] = {
            "db_type": db_type,
            "db_host": host,
            "db_port": str(port) if port is not None else None,
            "db_user": user,
            "db_password": password,
            "db_name": database,
        }

        success = True
        for key, value in credentials.items():
            if value is not None:
                if not CredentialManager.store(key, str(value)):
                    success = False

        return success

    @staticmethod
    def get_db_credentials() -> dict[str, str | None]:
        """Retrieve all database credentials.

        Returns:
            Dictionary with database credentials.
            Keys: db_type, db_host, db_port, db_user, db_password, db_name
        """
        return {key: CredentialManager.retrieve(key) for key in DB_CREDENTIAL_KEYS}

    @staticmethod
    def store_sheets_credentials(
        sheet_id: str | None = None,
        worksheet_name: str | None = None,
        service_account_json: str | None = None,
    ) -> bool:
        """Store Google Sheets credentials securely.

        Args:
            sheet_id: Google Sheet ID.
            worksheet_name: Target worksheet name.
            service_account_json: Complete service account JSON content.

        Returns:
            True if all provided credentials were stored.
        """
        credentials: dict[str, Any] = {
            "google_sheet_id": sheet_id,
            "google_worksheet_name": worksheet_name,
            "service_account_json": service_account_json,
        }

        success = True
        for key, value in credentials.items():
            if value is not None:
                if not CredentialManager.store(key, value):
                    success = False

        return success

    @staticmethod
    def get_sheets_credentials() -> dict[str, str | None]:
        """Retrieve all Google Sheets credentials.

        Returns:
            Dictionary with sheets credentials.
            Keys: google_sheet_id, google_worksheet_name, service_account_json
        """
        return {key: CredentialManager.retrieve(key) for key in SHEETS_CREDENTIAL_KEYS}

    @staticmethod
    def clear_all() -> bool:
        """Remove all stored credentials.

        Returns:
            True if all credentials were deleted.
        """
        success = True
        all_keys = DB_CREDENTIAL_KEYS + SHEETS_CREDENTIAL_KEYS

        for key in all_keys:
            if not CredentialManager.delete(key):
                success = False

        return success

    @staticmethod
    def has_db_credentials() -> bool:
        """Check if database credentials are stored.

        Returns:
            True if at least db_user and db_password are stored.
        """
        user = CredentialManager.retrieve("db_user")
        password = CredentialManager.retrieve("db_password")
        return bool(user and password)

    @staticmethod
    def has_sheets_credentials() -> bool:
        """Check if Google Sheets credentials are stored.

        Returns:
            True if at least google_sheet_id is stored.
        """
        sheet_id = CredentialManager.retrieve("google_sheet_id")
        return bool(sheet_id)


def is_desktop_mode() -> bool:
    """Check if the application is running in desktop mode.

    Desktop mode is indicated by:
    1. Running as a PyInstaller bundle
    2. Environment variable MYSQL_TO_SHEETS_DESKTOP=true

    Returns:
        True if running in desktop mode.
    """
    import os
    import sys

    # Check for PyInstaller bundle
    if getattr(sys, "frozen", False):
        return True

    # Check environment variable
    return os.environ.get("MYSQL_TO_SHEETS_DESKTOP", "").lower() == "true"


def get_config_with_keychain_fallback() -> dict[str, str | None]:
    """Get configuration with keychain fallback for missing values.

    First tries environment variables, then falls back to keychain
    for any missing database or sheets credentials.

    Returns:
        Dictionary with configuration values.
    """
    import os

    config: dict[str, str | None] = {}

    # Get from environment first
    env_mapping = {
        "db_type": "DB_TYPE",
        "db_host": "DB_HOST",
        "db_port": "DB_PORT",
        "db_user": "DB_USER",
        "db_password": "DB_PASSWORD",
        "db_name": "DB_NAME",
        "google_sheet_id": "GOOGLE_SHEET_ID",
        "google_worksheet_name": "GOOGLE_WORKSHEET_NAME",
    }

    for key, env_var in env_mapping.items():
        config[key] = os.environ.get(env_var)

    # Fall back to keychain for missing values (only in desktop mode)
    if is_desktop_mode() and CredentialManager.is_available():
        for key in env_mapping:
            if not config.get(key):
                keychain_value = CredentialManager.retrieve(key)
                if keychain_value:
                    config[key] = keychain_value
                    logger.debug(f"Using keychain value for {key}")

    return config
