"""Desktop application launcher for MySQL to Google Sheets sync.

This module provides the entry point for the PyInstaller-bundled
desktop application with native desktop experience:
- System tray with status indicator and quick actions
- Native desktop notifications for sync events
- Background sync capability without browser open
- Auto-start configuration for all platforms
"""

from mysql_to_sheets.desktop.app import main
from mysql_to_sheets.desktop.autostart import (
    disable_autostart,
    enable_autostart,
    is_autostart_enabled,
    toggle_autostart,
)
from mysql_to_sheets.desktop.autostart import (
    is_supported as is_autostart_supported,
)
from mysql_to_sheets.desktop.background import (
    BackgroundSyncManager,
    BackgroundSyncState,
    SyncResult,
    SyncStatus,
    get_background_manager,
)
from mysql_to_sheets.desktop.notifications import (
    DesktopNotifier,
    NotificationConfig,
    NotificationType,
    get_notifier,
    notify_sync_failed,
    notify_sync_success,
)
from mysql_to_sheets.desktop.tray import (
    SystemTray,
    TrayStatus,
    get_system_tray,
)

__all__ = [
    # Main entry point
    "main",
    # Auto-start
    "enable_autostart",
    "disable_autostart",
    "is_autostart_enabled",
    "is_autostart_supported",
    "toggle_autostart",
    # Background sync
    "BackgroundSyncManager",
    "BackgroundSyncState",
    "SyncResult",
    "SyncStatus",
    "get_background_manager",
    # Notifications
    "DesktopNotifier",
    "NotificationConfig",
    "NotificationType",
    "get_notifier",
    "notify_sync_success",
    "notify_sync_failed",
    # System tray
    "SystemTray",
    "TrayStatus",
    "get_system_tray",
]
