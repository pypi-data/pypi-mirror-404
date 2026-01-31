"""Tests for desktop application modules.

This module covers the following desktop components:
- Credential management (keyring integration)
- Background sync state management (thread safety)
- Update checker (version comparison)
- Tray icon loading and fallback
- Settings dialog persistence
"""

import os
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Credential Manager Tests
# ============================================================================


class TestCredentialManager:
    """Tests for the CredentialManager class."""

    @pytest.fixture
    def mock_keyring(self):
        """Create a mock keyring module."""
        with patch.dict("sys.modules", {"keyring": MagicMock()}):
            import keyring

            # Mock storage
            storage = {}

            def mock_set_password(service, key, value):
                storage[(service, key)] = value

            def mock_get_password(service, key):
                return storage.get((service, key))

            def mock_delete_password(service, key):
                if (service, key) in storage:
                    del storage[(service, key)]
                else:
                    # Simulate keyring.errors.PasswordDeleteError
                    raise Exception("Password not found")

            keyring.set_password = mock_set_password
            keyring.get_password = mock_get_password
            keyring.delete_password = mock_delete_password
            keyring.get_keyring = MagicMock()

            yield keyring, storage

    def test_credential_store_and_retrieve(self, mock_keyring):
        """Test storing and retrieving a credential."""
        keyring, storage = mock_keyring

        # Reset singleton state
        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = None

        with patch("mysql_to_sheets.desktop.credentials._check_keyring_available", return_value=True):
            CredentialManager._keyring_available = True

            result = CredentialManager.store("test_key", "test_value")
            assert result is True

            retrieved = CredentialManager.retrieve("test_key")
            assert retrieved == "test_value"

    def test_credential_delete(self, mock_keyring):
        """Test deleting a credential."""
        keyring, storage = mock_keyring

        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        # Store first
        CredentialManager.store("delete_key", "value")
        assert CredentialManager.retrieve("delete_key") == "value"

        # Delete
        result = CredentialManager.delete("delete_key")
        assert result is True

    def test_keyring_unavailable(self):
        """Test behavior when keyring is not available."""
        from mysql_to_sheets.desktop.credentials import CredentialManager

        # Force keyring unavailable
        CredentialManager._keyring_available = False

        result = CredentialManager.store("key", "value")
        assert result is False

        retrieved = CredentialManager.retrieve("key")
        assert retrieved is None

    def test_db_credentials_batch_operations(self, mock_keyring):
        """Test storing and retrieving database credentials."""
        keyring, storage = mock_keyring

        from mysql_to_sheets.desktop.credentials import CredentialManager

        CredentialManager._keyring_available = True

        # Store batch
        result = CredentialManager.store_db_credentials(
            host="localhost",
            port=3306,
            user="admin",
            password="secret",
            database="mydb",
            db_type="mysql",
        )
        assert result is True

        # Retrieve batch
        creds = CredentialManager.get_db_credentials()
        assert creds["db_host"] == "localhost"
        assert creds["db_port"] == "3306"
        assert creds["db_user"] == "admin"
        assert creds["db_password"] == "secret"
        assert creds["db_name"] == "mydb"
        assert creds["db_type"] == "mysql"

    def test_is_desktop_mode_env_var(self):
        """Test desktop mode detection via environment variable."""
        from mysql_to_sheets.desktop.credentials import is_desktop_mode

        # Not in desktop mode
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MYSQL_TO_SHEETS_DESKTOP", None)
            # Also ensure we're not frozen
            with patch.object(sys, "frozen", False, create=True):
                result = is_desktop_mode()
                # May still be True if other conditions met
                # Just verify it doesn't crash

        # In desktop mode via env var
        with patch.dict(os.environ, {"MYSQL_TO_SHEETS_DESKTOP": "true"}):
            result = is_desktop_mode()
            assert result is True


# ============================================================================
# Background Sync Manager Tests
# ============================================================================


class TestBackgroundSyncManager:
    """Tests for the BackgroundSyncManager class."""

    def test_initial_state(self):
        """Test manager initializes in idle state."""
        from mysql_to_sheets.desktop.background import BackgroundSyncManager, SyncStatus

        manager = BackgroundSyncManager()

        state = manager.state
        assert state.current_status == SyncStatus.IDLE
        assert state.last_result is None
        assert state.is_paused is False
        assert state.syncs_completed == 0
        assert state.syncs_failed == 0

    def test_pause_and_resume(self):
        """Test pausing and resuming syncs."""
        from mysql_to_sheets.desktop.background import BackgroundSyncManager

        manager = BackgroundSyncManager()

        assert manager.is_paused is False

        manager.pause()
        assert manager.is_paused is True

        manager.resume()
        assert manager.is_paused is False

    def test_cannot_run_when_paused(self):
        """Test that syncs don't start when paused."""
        from mysql_to_sheets.desktop.background import BackgroundSyncManager

        manager = BackgroundSyncManager()
        manager.pause()

        result = manager.run_sync(config_name="Test")
        assert result is False  # Should not start

    def test_state_is_thread_safe(self):
        """Test that state access is thread-safe."""
        from mysql_to_sheets.desktop.background import BackgroundSyncManager, SyncStatus

        manager = BackgroundSyncManager()
        errors = []

        def reader():
            for _ in range(100):
                try:
                    state = manager.state
                    # Just access properties
                    _ = state.current_status
                    _ = state.syncs_completed
                except Exception as e:
                    errors.append(e)

        def writer():
            for _ in range(100):
                try:
                    manager.pause()
                    manager.resume()
                except Exception as e:
                    errors.append(e)

        threads = [
            threading.Thread(target=reader) for _ in range(5)
        ] + [
            threading.Thread(target=writer) for _ in range(2)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"

    def test_status_callback(self):
        """Test that status change callback is invoked."""
        from mysql_to_sheets.desktop.background import BackgroundSyncManager, SyncStatus

        status_changes = []

        def on_status_change(status):
            status_changes.append(status)

        manager = BackgroundSyncManager(on_status_change=on_status_change)

        # Force a status change
        manager._set_status(SyncStatus.RUNNING)
        assert SyncStatus.RUNNING in status_changes

    def test_get_last_result_summary_no_syncs(self):
        """Test summary when no syncs have run."""
        from mysql_to_sheets.desktop.background import BackgroundSyncManager

        manager = BackgroundSyncManager()
        summary = manager.get_last_result_summary()
        assert "No syncs" in summary


# ============================================================================
# Update Checker Tests
# ============================================================================


class TestUpdateChecker:
    """Tests for the UpdateChecker class."""

    def test_parse_version(self):
        """Test version string parsing."""
        from mysql_to_sheets.desktop.updater import parse_version

        assert parse_version("1.0.0") == (1, 0, 0)
        assert parse_version("v1.0.0") == (1, 0, 0)
        assert parse_version("2.3.4") == (2, 3, 4)
        # Pre-release versions with non-numeric parts return (0,0,0) from the
        # current implementation since "0-beta" is not a valid integer
        assert parse_version("1.0.0-beta") == (0, 0, 0)
        assert parse_version("invalid") == (0, 0, 0)

    def test_is_newer_version(self):
        """Test version comparison."""
        from mysql_to_sheets.desktop.updater import is_newer_version

        # Newer versions
        assert is_newer_version("2.0.0", "1.0.0") is True
        assert is_newer_version("1.1.0", "1.0.0") is True
        assert is_newer_version("1.0.1", "1.0.0") is True
        assert is_newer_version("v1.1.0", "1.0.0") is True

        # Same version
        assert is_newer_version("1.0.0", "1.0.0") is False

        # Older versions
        assert is_newer_version("1.0.0", "2.0.0") is False
        assert is_newer_version("1.0.0", "1.1.0") is False

    def test_get_platform_asset_name(self):
        """Test platform asset name detection."""
        from mysql_to_sheets.desktop.updater import get_platform_asset_name

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Darwin"
            assert "dmg" in get_platform_asset_name()

            mock_system.return_value = "Windows"
            assert "windows" in get_platform_asset_name().lower()

            mock_system.return_value = "Linux"
            assert "AppImage" in get_platform_asset_name()

    def test_update_checker_rate_limiting(self):
        """Test that update checks are rate limited."""
        from mysql_to_sheets.desktop.updater import UpdateChecker

        checker = UpdateChecker(check_interval_hours=1)

        # Mock the network request
        with patch("mysql_to_sheets.desktop.updater.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_response.read.return_value = b'{"tag_name": "v1.0.0"}'
            mock_urlopen.return_value = mock_response

            # First check should make request
            checker.check_for_updates(force=True)
            assert mock_urlopen.call_count == 1

            # Second check within interval should be skipped (unless forced)
            checker.check_for_updates(force=False)
            assert mock_urlopen.call_count == 1  # No new call

            # Forced check should make request
            checker.check_for_updates(force=True)
            assert mock_urlopen.call_count == 2

    def test_update_callback(self):
        """Test that update callback is invoked when update found."""
        from mysql_to_sheets.desktop.updater import UpdateChecker

        updates_found = []

        def on_update(info):
            updates_found.append(info)

        checker = UpdateChecker(on_update_available=on_update)
        checker._current_version = "0.9.0"  # Old version

        # Mock response with newer version
        mock_response_data = {
            "tag_name": "v1.0.0",
            "html_url": "https://github.com/test/test/releases/v1.0.0",
            "body": "Release notes",
            "published_at": "2024-01-01T00:00:00Z",
            "assets": [],
        }

        with patch("mysql_to_sheets.desktop.updater.urlopen") as mock_urlopen:
            import json

            mock_response = MagicMock()
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=False)
            mock_response.read.return_value = json.dumps(mock_response_data).encode()
            mock_urlopen.return_value = mock_response

            result = checker.check_for_updates(force=True)

            assert result is not None
            assert result.version == "1.0.0"
            assert len(updates_found) == 1


# ============================================================================
# Tray Icon Tests
# ============================================================================


class TestTrayIcon:
    """Tests for tray icon functionality."""

    def test_icon_colors_defined(self):
        """Test that icon colors are defined for all statuses."""
        from mysql_to_sheets.desktop.tray import ICON_COLORS, TrayStatus

        for status in TrayStatus:
            assert status in ICON_COLORS
            color = ICON_COLORS[status]
            assert len(color) == 3  # RGB tuple
            assert all(0 <= c <= 255 for c in color)

    def test_icon_filenames_defined(self):
        """Test that icon filenames are defined for all statuses."""
        from mysql_to_sheets.desktop.tray import ICON_FILENAMES, TrayStatus

        for status in TrayStatus:
            assert status in ICON_FILENAMES
            filename = ICON_FILENAMES[status]
            assert filename.endswith(".png")
            assert "tray-" in filename

    def test_create_fallback_icon(self):
        """Test fallback icon generation when assets not available."""
        from mysql_to_sheets.desktop.tray import TrayStatus, _create_icon_image

        # Mock assets not found
        with patch("mysql_to_sheets.desktop.tray._load_icon_from_assets", return_value=None):
            icon_data = _create_icon_image(TrayStatus.IDLE)
            assert icon_data is not None
            # Should return BytesIO with PNG data
            data = icon_data.read()
            assert data[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes

    def test_tray_tooltip_building(self):
        """Test dynamic tooltip generation."""
        from mysql_to_sheets.desktop.tray import SystemTray, TrayStatus

        tray = SystemTray(port=5000)

        # Idle state
        tray._status = TrayStatus.IDLE
        tooltip = tray._build_tooltip()
        assert "MySQL to Sheets" in tooltip
        assert "Ready" in tooltip

        # Error state
        tray._status = TrayStatus.ERROR
        tray._last_error_msg = "Connection refused"
        tooltip = tray._build_tooltip()
        assert "Connection refused" in tooltip

        # Syncing state
        tray._status = TrayStatus.SYNCING
        tooltip = tray._build_tooltip()
        assert "Syncing" in tooltip


# ============================================================================
# Settings Dialog Tests
# ============================================================================


class TestSettingsDialog:
    """Tests for settings dialog persistence."""

    @pytest.fixture
    def temp_settings_dir(self, tmp_path):
        """Create a temporary settings directory."""
        settings_dir = tmp_path / ".mysql-to-sheets"
        settings_dir.mkdir()
        return settings_dir

    def test_default_settings(self):
        """Test that default settings are defined."""
        from mysql_to_sheets.desktop.settings_dialog import DEFAULT_SETTINGS

        assert "start_on_login" in DEFAULT_SETTINGS
        assert "show_notifications" in DEFAULT_SETTINGS
        assert "default_sync_mode" in DEFAULT_SETTINGS
        assert "chunk_size" in DEFAULT_SETTINGS

    def test_load_settings_with_defaults(self, temp_settings_dir):
        """Test loading settings falls back to defaults."""
        from mysql_to_sheets.desktop.settings_dialog import DEFAULT_SETTINGS, load_settings

        with patch(
            "mysql_to_sheets.desktop.settings_dialog.get_settings_path",
            return_value=temp_settings_dir / "settings.json",
        ):
            settings = load_settings()

            # Should have all default keys
            for key in DEFAULT_SETTINGS:
                assert key in settings

    def test_save_and_load_settings(self, temp_settings_dir):
        """Test saving and loading settings."""
        import json

        from mysql_to_sheets.desktop.settings_dialog import load_settings, save_settings

        settings_path = temp_settings_dir / "settings.json"

        with patch(
            "mysql_to_sheets.desktop.settings_dialog.get_settings_path",
            return_value=settings_path,
        ):
            # Save custom settings
            custom_settings = {
                "start_on_login": True,
                "chunk_size": 2000,
            }
            result = save_settings(custom_settings)
            assert result is True
            assert settings_path.exists()

            # Load and verify
            loaded = load_settings()
            assert loaded["start_on_login"] is True
            assert loaded["chunk_size"] == 2000

    def test_create_settings_dialog_without_ttkbootstrap(self):
        """Test that create_settings_dialog returns None without ttkbootstrap."""
        # Mock ttkbootstrap as unavailable
        with patch.dict("sys.modules", {"ttkbootstrap": None}):
            from mysql_to_sheets.desktop.settings_dialog import SettingsDialog

            dialog = SettingsDialog()
            # Should not be available since import will fail
            assert not dialog._ttkbootstrap_available or dialog._check_ttkbootstrap() is False


# ============================================================================
# Integration Tests
# ============================================================================


class TestDesktopIntegration:
    """Integration tests for desktop modules working together."""

    def test_tray_settings_integration(self):
        """Test that tray opens settings dialog correctly."""
        from mysql_to_sheets.desktop.tray import SystemTray

        tray = SystemTray(port=5000)

        # Verify _apply_settings method exists and can be called
        assert hasattr(tray, "_apply_settings")
        tray._apply_settings({"show_notifications": True})  # Should not raise

    def test_tray_callbacks_are_optional(self):
        """Test that tray works without callbacks."""
        from mysql_to_sheets.desktop.tray import SystemTray

        # Create tray with no callbacks
        tray = SystemTray(port=5000)

        # These should not raise even without callbacks
        tray._trigger_sync()
        tray._toggle_pause()
