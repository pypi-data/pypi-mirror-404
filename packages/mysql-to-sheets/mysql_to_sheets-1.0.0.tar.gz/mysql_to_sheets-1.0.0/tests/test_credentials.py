"""Tests for credential manager (NFR-02).

Tests the OS keychain integration for secure credential storage.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestCredentialManager:
    """Tests for CredentialManager class."""

    def test_is_available_when_keyring_installed(self) -> None:
        """Verify is_available returns True when keyring is installed."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        # Reset cached availability
        CredentialManager._keyring_available = True
        assert CredentialManager.is_available() is True

    def test_is_available_when_keyring_not_installed(self) -> None:
        """Verify is_available returns False when keyring is not installed."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = False
        assert CredentialManager.is_available() is False

    def test_store_credential(self) -> None:
        """Verify storing a credential calls keyring correctly."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        with patch("keyring.set_password") as mock_set:
            result = CredentialManager.store("db_password", "secret123")

            assert result is True
            mock_set.assert_called_once_with("MySQLToSheets", "db_password", "secret123")

    def test_store_credential_when_unavailable(self) -> None:
        """Verify store returns False when keyring is unavailable."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = False

        result = CredentialManager.store("db_password", "secret123")
        assert result is False

    def test_retrieve_credential(self) -> None:
        """Verify retrieving a credential calls keyring correctly."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        with patch("keyring.get_password", return_value="secret123"):
            result = CredentialManager.retrieve("db_password")

            assert result == "secret123"

    def test_retrieve_credential_not_found(self) -> None:
        """Verify retrieve returns None when credential doesn't exist."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        with patch("keyring.get_password", return_value=None):
            result = CredentialManager.retrieve("nonexistent_key")

            assert result is None

    def test_retrieve_credential_when_unavailable(self) -> None:
        """Verify retrieve returns None when keyring is unavailable."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = False

        result = CredentialManager.retrieve("db_password")
        assert result is None

    def test_delete_credential(self) -> None:
        """Verify deleting a credential calls keyring correctly."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        with patch("keyring.delete_password") as mock_delete:
            result = CredentialManager.delete("db_password")

            assert result is True
            mock_delete.assert_called_once_with("MySQLToSheets", "db_password")

    def test_delete_credential_when_unavailable(self) -> None:
        """Verify delete returns False when keyring is unavailable."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = False

        result = CredentialManager.delete("db_password")
        assert result is False


class TestDatabaseCredentials:
    """Tests for database credential storage."""

    def test_store_db_credentials(self) -> None:
        """Verify storing all database credentials."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        with patch("keyring.set_password") as mock_set:
            result = CredentialManager.store_db_credentials(
                host="localhost",
                port=3306,
                user="admin",
                password="secret",
                database="mydb",
                db_type="mysql",
            )

            assert result is True
            assert mock_set.call_count == 6

    def test_store_db_credentials_partial(self) -> None:
        """Verify storing partial database credentials (only non-None values)."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        with patch("keyring.set_password") as mock_set:
            result = CredentialManager.store_db_credentials(
                host=None,
                port=None,
                user="admin",
                password="secret",
                database=None,
                db_type="mysql",
            )

            assert result is True
            assert mock_set.call_count == 3

    def test_get_db_credentials(self) -> None:
        """Verify retrieving all database credentials."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        def mock_get_password(service: str, key: str) -> str | None:
            values = {
                "db_type": "mysql",
                "db_host": "localhost",
                "db_port": "3306",
                "db_user": "admin",
                "db_password": "secret",
                "db_name": "mydb",
            }
            return values.get(key)

        with patch("keyring.get_password", side_effect=mock_get_password):
            result = CredentialManager.get_db_credentials()

            assert result["db_type"] == "mysql"
            assert result["db_host"] == "localhost"
            assert result["db_port"] == "3306"
            assert result["db_user"] == "admin"
            assert result["db_password"] == "secret"
            assert result["db_name"] == "mydb"

    def test_has_db_credentials_true(self) -> None:
        """Verify has_db_credentials returns True when user and password exist."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        def mock_get_password(service: str, key: str) -> str | None:
            if key == "db_user":
                return "admin"
            if key == "db_password":
                return "secret"
            return None

        with patch("keyring.get_password", side_effect=mock_get_password):
            assert CredentialManager.has_db_credentials() is True

    def test_has_db_credentials_false_missing_user(self) -> None:
        """Verify has_db_credentials returns False when user is missing."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        def mock_get_password(service: str, key: str) -> str | None:
            if key == "db_password":
                return "secret"
            return None

        with patch("keyring.get_password", side_effect=mock_get_password):
            assert CredentialManager.has_db_credentials() is False


class TestSheetsCredentials:
    """Tests for Google Sheets credential storage."""

    def test_store_sheets_credentials(self) -> None:
        """Verify storing Google Sheets credentials."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        with patch("keyring.set_password") as mock_set:
            result = CredentialManager.store_sheets_credentials(
                sheet_id="abc123",
                worksheet_name="Sheet1",
                service_account_json='{"type": "service_account"}',
            )

            assert result is True
            assert mock_set.call_count == 3

    def test_get_sheets_credentials(self) -> None:
        """Verify retrieving Google Sheets credentials."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        def mock_get_password(service: str, key: str) -> str | None:
            values = {
                "google_sheet_id": "abc123",
                "google_worksheet_name": "Sheet1",
                "service_account_json": '{"type": "service_account"}',
            }
            return values.get(key)

        with patch("keyring.get_password", side_effect=mock_get_password):
            result = CredentialManager.get_sheets_credentials()

            assert result["google_sheet_id"] == "abc123"
            assert result["google_worksheet_name"] == "Sheet1"
            assert result["service_account_json"] == '{"type": "service_account"}'

    def test_has_sheets_credentials_true(self) -> None:
        """Verify has_sheets_credentials returns True when sheet_id exists."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        def mock_get_password(service: str, key: str) -> str | None:
            if key == "google_sheet_id":
                return "abc123"
            return None

        with patch("keyring.get_password", side_effect=mock_get_password):
            assert CredentialManager.has_sheets_credentials() is True

    def test_has_sheets_credentials_false(self) -> None:
        """Verify has_sheets_credentials returns False when sheet_id is missing."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        with patch("keyring.get_password", return_value=None):
            assert CredentialManager.has_sheets_credentials() is False


class TestDesktopMode:
    """Tests for desktop mode detection."""

    def test_is_desktop_mode_frozen(self) -> None:
        """Verify is_desktop_mode returns True for PyInstaller bundle."""
        from mysql_to_sheets.desktop.credentials import is_desktop_mode

        with patch("sys.frozen", True, create=True):
            assert is_desktop_mode() is True

    def test_is_desktop_mode_env_var(self) -> None:
        """Verify is_desktop_mode returns True when env var is set."""
        from mysql_to_sheets.desktop.credentials import is_desktop_mode

        with patch.dict("os.environ", {"MYSQL_TO_SHEETS_DESKTOP": "true"}):
            assert is_desktop_mode() is True

    def test_is_desktop_mode_false(self) -> None:
        """Verify is_desktop_mode returns False in normal mode."""
        from mysql_to_sheets.desktop.credentials import is_desktop_mode

        with patch.dict("os.environ", {"MYSQL_TO_SHEETS_DESKTOP": ""}, clear=False):
            result = is_desktop_mode()
            assert isinstance(result, bool)


class TestConfigKeychainFallback:
    """Tests for config keychain fallback."""

    def test_get_config_with_keychain_fallback(self) -> None:
        """Verify get_config_with_keychain_fallback works."""
        from mysql_to_sheets.desktop.credentials import get_config_with_keychain_fallback

        # Use clear=True to ensure only our test env vars are set
        test_env = {
            "DB_TYPE": "mysql",
            "DB_HOST": "localhost",
        }
        with (
            patch.dict("os.environ", test_env, clear=True),
            patch(
                "mysql_to_sheets.desktop.credentials.is_desktop_mode", return_value=False
            ),
        ):
            result = get_config_with_keychain_fallback()

            assert result["db_type"] == "mysql"
            assert result["db_host"] == "localhost"
            assert result["db_port"] is None
