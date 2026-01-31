"""System tray integration for the desktop application.

This module provides cross-platform system tray functionality using pystray.
The tray icon shows sync status and provides quick access to common actions.
"""

import logging
import sys
import threading
import webbrowser
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from pystray import Icon, Menu, MenuItem

    from mysql_to_sheets.desktop.status_window import StatusWindow

logger = logging.getLogger(__name__)


class TrayStatus(Enum):
    """Status indicators for the tray icon."""

    IDLE = "idle"  # Green - ready
    SYNCING = "syncing"  # Yellow - in progress
    ERROR = "error"  # Red - last sync failed
    PAUSED = "paused"  # Gray - syncs paused
    OFFLINE = "offline"  # Blue-gray - no connectivity


# Icon colors as RGB tuples
ICON_COLORS = {
    TrayStatus.IDLE: (76, 175, 80),  # Green
    TrayStatus.SYNCING: (255, 193, 7),  # Amber
    TrayStatus.ERROR: (244, 67, 54),  # Red
    TrayStatus.PAUSED: (158, 158, 158),  # Gray
    TrayStatus.OFFLINE: (96, 125, 139),  # Blue-gray
}

# Icon filenames for each status
ICON_FILENAMES = {
    TrayStatus.IDLE: "tray-idle.png",
    TrayStatus.SYNCING: "tray-syncing.png",
    TrayStatus.ERROR: "tray-error.png",
    TrayStatus.PAUSED: "tray-paused.png",
    TrayStatus.OFFLINE: "tray-offline.png",
}


def _get_assets_dir() -> Path | None:
    """Get the assets directory path.

    Handles both development mode and PyInstaller bundled mode.

    Returns:
        Path to assets directory, or None if not found.
    """
    # Check if running as PyInstaller bundle
    if getattr(sys, "frozen", False):
        # Running as bundled executable
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        assets_dir = base_path / "assets"
        if assets_dir.exists():
            return assets_dir

    # Development mode: check relative to this file
    this_file = Path(__file__)
    # Navigate up to project root (desktop/tray.py -> mysql_to_sheets -> project root)
    project_root = this_file.parent.parent.parent
    assets_dir = project_root / "assets"
    if assets_dir.exists():
        return assets_dir

    return None


def _load_icon_from_assets(status: TrayStatus) -> "BytesIO | None":
    """Try to load icon from assets directory.

    Args:
        status: Current status to load icon for.

    Returns:
        BytesIO containing PNG data, or None if not found.
    """
    assets_dir = _get_assets_dir()
    if not assets_dir:
        return None

    filename = ICON_FILENAMES.get(status)
    if not filename:
        return None

    icon_path = assets_dir / filename
    if not icon_path.exists():
        return None

    try:
        with open(icon_path, "rb") as f:
            data = f.read()
        return BytesIO(data)
    except Exception as e:
        logger.warning(f"Failed to load icon from {icon_path}: {e}")
        return None


def _create_icon_image(status: TrayStatus, size: int = 64) -> "BytesIO":
    """Get icon for the tray, loading from assets or generating a fallback.

    First tries to load from assets/ directory (bundled icons).
    Falls back to generating a simple colored circle if assets not available.

    Args:
        status: Current status to determine icon.
        size: Icon size in pixels (used for fallback generation).

    Returns:
        BytesIO containing PNG image data.
    """
    # Try to load from assets first
    asset_icon = _load_icon_from_assets(status)
    if asset_icon:
        return asset_icon

    # Fallback: generate icon dynamically
    try:
        from PIL import Image, ImageDraw

        color = ICON_COLORS.get(status, ICON_COLORS[TrayStatus.IDLE])

        # Create image with transparency
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw filled circle
        padding = size // 8
        draw.ellipse(
            [padding, padding, size - padding, size - padding],
            fill=color + (255,),  # Add alpha channel
        )

        # Save to BytesIO
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    except ImportError:
        logger.warning("Pillow not installed, using fallback icon")
        # Return minimal valid PNG (1x1 transparent pixel)
        return BytesIO(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )


class SystemTray:
    """System tray manager for the desktop application.

    Provides:
    - Status indicator (colored icon)
    - Quick actions menu
    - Callbacks for user interactions
    """

    def __init__(
        self,
        port: int = 5000,
        on_sync_now: Callable[[], None] | None = None,
        on_sync_config: Callable[[int], None] | None = None,
        on_pause_toggle: Callable[[], bool] | None = None,
        on_quit: Callable[[], None] | None = None,
        get_last_sync_info: Callable[[], str] | None = None,
        get_configs: Callable[[], list[dict]] | None = None,
        get_schedules: Callable[[], list[dict]] | None = None,
        get_databases: Callable[[], list[dict]] | None = None,
        is_paused: Callable[[], bool] | None = None,
        status_window: "StatusWindow | None" = None,
    ) -> None:
        """Initialize the system tray.

        Args:
            port: The port the web dashboard is running on.
            on_sync_now: Callback to trigger a sync.
            on_sync_config: Callback to trigger sync for a specific config ID.
            on_pause_toggle: Callback to toggle pause state, returns new state.
            on_quit: Callback when quit is selected.
            get_last_sync_info: Callback to get last sync summary string.
            get_configs: Callback to get list of sync configs for submenu.
            get_schedules: Callback to get list of schedules for submenu.
            get_databases: Callback to get list of database integrations for submenu.
            is_paused: Callback to check if syncs are paused.
            status_window: Optional status window instance.
        """
        self.port = port
        self._on_sync_now = on_sync_now
        self._on_sync_config = on_sync_config
        self._on_pause_toggle = on_pause_toggle
        self._on_quit = on_quit
        self._get_last_sync_info = get_last_sync_info
        self._get_configs = get_configs
        self._get_schedules = get_schedules
        self._get_databases = get_databases
        self._is_paused = is_paused
        self._status_window = status_window

        self._status = TrayStatus.IDLE
        self._icon: "Icon | None" = None
        self._pystray_available = False
        self._thread: threading.Thread | None = None

        # State tracking for dynamic tooltip
        self._last_rows_synced: int | None = None
        self._last_sync_time: float | None = None
        self._last_error_msg: str | None = None

        # Update checker state
        self._update_available: bool = False
        self._update_version: str | None = None

        self._init_pystray()

    def _init_pystray(self) -> None:
        """Initialize pystray if available."""
        try:
            import pystray

            self._pystray_available = True
            logger.debug("Pystray initialized successfully")
        except ImportError:
            logger.warning(
                "Pystray not installed. System tray will be disabled. "
                "Install with: pip install pystray"
            )

    @property
    def is_available(self) -> bool:
        """Check if system tray is available."""
        return self._pystray_available

    def _get_icon_image(self) -> "BytesIO":
        """Get the current icon image based on status."""
        return _create_icon_image(self._status)

    def _create_menu(self) -> "Menu":
        """Create the tray menu."""
        from pystray import Menu, MenuItem

        # Get dynamic values
        is_paused = self._is_paused() if self._is_paused else False
        pause_text = "Resume Syncs" if is_paused else "Pause Syncs"
        last_sync_info = (
            self._get_last_sync_info() if self._get_last_sync_info else "No syncs yet"
        )

        # Build config submenu
        config_submenu = self._build_config_submenu()
        schedule_submenu = self._build_schedule_submenu()
        database_submenu = self._build_database_submenu()

        items = [
            MenuItem("Open Dashboard", self._open_dashboard, default=True),
        ]

        # Add status window if available
        if self._status_window:
            items.append(MenuItem("Open Status Window", self._open_status_window))

        items.extend([
            Menu.SEPARATOR,
            MenuItem("Run Sync Now", self._trigger_sync),
        ])

        # Add Quick Sync submenu if configs are available
        if config_submenu:
            items.append(MenuItem("Quick Sync", Menu(*config_submenu)))

        # Add Schedules submenu if schedules are available
        if schedule_submenu:
            items.append(MenuItem("Schedules", Menu(*schedule_submenu)))

        # Add Databases submenu if databases are available
        if database_submenu:
            items.append(MenuItem("Databases", Menu(*database_submenu)))

        items.extend([
            MenuItem(pause_text, self._toggle_pause),
            Menu.SEPARATOR,
            MenuItem(f"Last: {last_sync_info}", None, enabled=False),
            MenuItem("View History", self._open_history),
            Menu.SEPARATOR,
        ])

        # Add update notification if available
        if self._update_available and self._update_version:
            items.append(MenuItem(
                f"★ Update Available: v{self._update_version}",
                self._download_update,
            ))

        items.extend([
            MenuItem("Check for Updates...", self._check_for_updates),
            MenuItem("Settings", self._open_settings),
            MenuItem("Quit", self._quit),
        ])

        return Menu(*items)

    def _build_config_submenu(self) -> list["MenuItem"]:
        """Build submenu items for each sync config.

        Returns:
            List of MenuItem for each available config, or empty list.
        """
        from pystray import MenuItem

        if not self._get_configs:
            return []

        try:
            configs = self._get_configs()
            if not configs:
                return [MenuItem("No configs available", None, enabled=False)]

            items = []
            for config in configs[:10]:  # Limit to 10 items
                config_id = config.get("id")
                name = config.get("name", f"Config {config_id}")
                enabled = config.get("enabled", True)

                # Create callback that captures config_id
                def make_callback(cid: int) -> Callable:
                    return lambda: self._run_config(cid)

                items.append(MenuItem(
                    name,
                    make_callback(config_id),
                    enabled=enabled,
                ))

            return items
        except Exception as e:
            logger.warning(f"Failed to build config submenu: {e}")
            return []

    def _build_schedule_submenu(self) -> list["MenuItem"]:
        """Build submenu items for each schedule.

        Returns:
            List of MenuItem for each schedule, or empty list.
        """
        from pystray import MenuItem

        if not self._get_schedules:
            return []

        try:
            schedules = self._get_schedules()
            if not schedules:
                return [MenuItem("No schedules configured", None, enabled=False)]

            items = []
            for schedule in schedules[:10]:  # Limit to 10 items
                name = schedule.get("name", "Unnamed")
                enabled = schedule.get("enabled", False)
                next_run = schedule.get("next_run", "")

                # Show checkmark for enabled schedules
                status_prefix = "✓ " if enabled else "  "
                label = f"{status_prefix}{name}"
                if next_run:
                    label += f" ({next_run})"

                items.append(MenuItem(label, None, enabled=False))

            return items
        except Exception as e:
            logger.warning(f"Failed to build schedule submenu: {e}")
            return []

    def _build_database_submenu(self) -> list["MenuItem"]:
        """Build submenu items for database integrations with health status.

        Format: ● Connected / ○ Disconnected / ⚠ Error

        Returns:
            List of MenuItem for each database, or empty list.
        """
        from pystray import MenuItem

        if not self._get_databases:
            return []

        try:
            databases = self._get_databases()
            if not databases:
                return [MenuItem("No databases configured", None, enabled=False)]

            items = []
            for db in databases[:10]:  # Limit to 10 items
                name = db.get("name", "Unknown")
                db_type = db.get("integration_type", "")
                health = db.get("health_status", "unknown")

                # Status indicator
                if health == "connected":
                    prefix = "● "  # Green dot
                elif health == "disconnected":
                    prefix = "○ "  # Empty dot
                elif health == "error":
                    prefix = "⚠ "  # Warning
                else:
                    prefix = "? "  # Unknown

                # Format: "● MySQL - Production" or "○ PostgreSQL - Analytics"
                type_short = db_type.upper() if db_type else "DB"
                label = f"{prefix}{name} ({type_short})"

                items.append(MenuItem(label, None, enabled=False))

            # Add separator and link to dashboard
            from pystray import Menu
            items.append(Menu.SEPARATOR)
            items.append(MenuItem("Open Databases...", self._open_databases))

            return items
        except Exception as e:
            logger.warning(f"Failed to build database submenu: {e}")
            return []

    def _open_databases(self) -> None:
        """Open the databases page in browser."""
        webbrowser.open(f"http://127.0.0.1:{self.port}/databases")

    def _run_config(self, config_id: int) -> None:
        """Trigger sync for a specific config.

        Args:
            config_id: The ID of the config to sync.
        """
        if self._on_sync_config:
            try:
                self._on_sync_config(config_id)
            except Exception as e:
                logger.error(f"Failed to run config {config_id}: {e}")

    def _open_status_window(self) -> None:
        """Open the status window."""
        if self._status_window:
            try:
                self._status_window.show()
            except Exception as e:
                logger.error(f"Failed to open status window: {e}")

    def _open_dashboard(self) -> None:
        """Open the main dashboard in browser."""
        webbrowser.open(f"http://127.0.0.1:{self.port}/")

    def _open_history(self) -> None:
        """Open the history page in browser."""
        webbrowser.open(f"http://127.0.0.1:{self.port}/history")

    def _open_settings(self) -> None:
        """Open settings - native dialog if available, otherwise web."""
        try:
            from mysql_to_sheets.desktop.settings_dialog import create_settings_dialog

            dialog = create_settings_dialog(on_save=self._apply_settings)
            if dialog is not None:
                dialog.show()
                return
        except ImportError:
            pass
        webbrowser.open(f"http://127.0.0.1:{self.port}/configs")

    def _apply_settings(self, settings: dict) -> None:
        """Apply settings changes from the settings dialog.

        Args:
            settings: Dictionary of settings that were saved.
        """
        logger.info(f"Settings updated: {list(settings.keys())}")
        # Refresh menu if needed (e.g., notification settings changed)
        if self._icon:
            self._icon.update_menu()

    def _trigger_sync(self) -> None:
        """Trigger a sync operation."""
        if self._on_sync_now:
            try:
                self._on_sync_now()
            except Exception as e:
                logger.error(f"Failed to trigger sync: {e}")

    def _toggle_pause(self) -> None:
        """Toggle pause state."""
        if self._on_pause_toggle:
            try:
                self._on_pause_toggle()
                # Update menu to reflect new state
                if self._icon:
                    self._icon.update_menu()
            except Exception as e:
                logger.error(f"Failed to toggle pause: {e}")

    def _quit(self) -> None:
        """Handle quit action."""
        if self._on_quit:
            try:
                self._on_quit()
            except Exception as e:
                logger.error(f"Quit callback failed: {e}")

        if self._icon:
            self._icon.stop()

    def _check_for_updates(self) -> None:
        """Check for application updates."""
        try:
            from mysql_to_sheets.desktop.updater import get_update_checker

            checker = get_update_checker()
            update_info = checker.check_for_updates(force=True)

            if update_info:
                self._update_available = True
                self._update_version = update_info.version
                # Update menu to show update item
                if self._icon:
                    self._icon.update_menu()
                # Show notification
                try:
                    from mysql_to_sheets.desktop.notifications import show_notification

                    show_notification(
                        title="Update Available",
                        message=f"Version {update_info.version} is available. Click 'Check for Updates' in the menu to download.",
                    )
                except Exception:
                    pass
            else:
                # Optionally show "up to date" notification
                try:
                    from mysql_to_sheets.desktop.notifications import show_notification

                    show_notification(
                        title="No Updates",
                        message="You're running the latest version.",
                    )
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")

    def _download_update(self) -> None:
        """Open the download page for the update."""
        try:
            from mysql_to_sheets.desktop.updater import get_update_checker

            checker = get_update_checker()
            checker.open_download_page()
        except Exception as e:
            logger.error(f"Failed to open download page: {e}")

    def set_update_available(self, version: str) -> None:
        """Set update available state (called by background updater).

        Args:
            version: The new version available.
        """
        self._update_available = True
        self._update_version = version
        if self._icon:
            self._icon.update_menu()

    def _build_tooltip(self) -> str:
        """Build dynamic tooltip based on current state.

        Returns:
            Formatted tooltip string with status and last sync info.
        """
        import time

        base = "MySQL to Sheets"

        # Add status
        status_labels = {
            TrayStatus.IDLE: "Ready",
            TrayStatus.SYNCING: "Syncing...",
            TrayStatus.ERROR: "Error",
            TrayStatus.PAUSED: "Paused",
            TrayStatus.OFFLINE: "Offline",
        }
        status_text = status_labels.get(self._status, "")

        # Build info part
        if self._status == TrayStatus.ERROR and self._last_error_msg:
            # Show error details (truncated)
            error_short = self._last_error_msg[:50] + "..." if len(self._last_error_msg) > 50 else self._last_error_msg
            return f"{base} - {error_short}"
        elif self._status == TrayStatus.SYNCING:
            return f"{base} - Syncing..."
        elif self._last_rows_synced is not None and self._last_sync_time:
            # Show last sync info with relative time
            elapsed = time.time() - self._last_sync_time
            if elapsed < 60:
                time_str = "just now"
            elif elapsed < 3600:
                mins = int(elapsed / 60)
                time_str = f"{mins}m ago"
            elif elapsed < 86400:
                hours = int(elapsed / 3600)
                time_str = f"{hours}h ago"
            else:
                days = int(elapsed / 86400)
                time_str = f"{days}d ago"

            return f"{base} - {status_text} | Last: {self._last_rows_synced} rows ({time_str})"
        else:
            return f"{base} - {status_text}"

    def set_status(
        self,
        status: TrayStatus,
        rows_synced: int | None = None,
        error_msg: str | None = None,
    ) -> None:
        """Update the tray icon status and tooltip.

        Args:
            status: New status to display.
            rows_synced: Number of rows synced (for success state).
            error_msg: Error message (for error state).
        """
        import time

        self._status = status

        # Track last sync info
        if status == TrayStatus.IDLE and rows_synced is not None:
            self._last_rows_synced = rows_synced
            self._last_sync_time = time.time()
            self._last_error_msg = None
        elif status == TrayStatus.ERROR and error_msg:
            self._last_error_msg = error_msg

        logger.debug(f"Tray status changed to: {status.value}")

        if self._icon:
            try:
                from PIL import Image

                # Update icon
                image_data = self._get_icon_image()
                self._icon.icon = Image.open(image_data)

                # Update tooltip
                self._icon.title = self._build_tooltip()
            except Exception as e:
                logger.warning(f"Failed to update tray icon: {e}")

    def update_tooltip(self, text: str) -> None:
        """Update the tray icon tooltip.

        Args:
            text: New tooltip text.
        """
        if self._icon:
            self._icon.title = text

    def start(self) -> None:
        """Start the system tray in a background thread."""
        if not self.is_available:
            logger.info("System tray not available, skipping")
            return

        def _run_tray() -> None:
            try:
                from PIL import Image
                from pystray import Icon

                image_data = self._get_icon_image()
                image = Image.open(image_data)

                self._icon = Icon(
                    name="mysql-to-sheets",
                    icon=image,
                    title=self._build_tooltip(),
                    menu=self._create_menu,  # Use callable for dynamic menu
                )

                logger.info("System tray started")
                self._icon.run()

            except Exception as e:
                logger.error(f"Failed to start system tray: {e}")

        self._thread = threading.Thread(target=_run_tray, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the system tray."""
        if self._icon:
            try:
                self._icon.stop()
                logger.info("System tray stopped")
            except Exception as e:
                logger.warning(f"Error stopping tray: {e}")


# Global tray instance
_tray: SystemTray | None = None


def get_system_tray(
    port: int = 5000,
    on_sync_now: Callable[[], None] | None = None,
    on_sync_config: Callable[[int], None] | None = None,
    on_pause_toggle: Callable[[], bool] | None = None,
    on_quit: Callable[[], None] | None = None,
    get_last_sync_info: Callable[[], str] | None = None,
    get_configs: Callable[[], list[dict]] | None = None,
    get_schedules: Callable[[], list[dict]] | None = None,
    get_databases: Callable[[], list[dict]] | None = None,
    is_paused: Callable[[], bool] | None = None,
    status_window: "StatusWindow | None" = None,
) -> SystemTray:
    """Get or create the global system tray instance.

    Args:
        port: Dashboard port.
        on_sync_now: Sync trigger callback.
        on_sync_config: Callback to trigger sync for a specific config ID.
        on_pause_toggle: Pause toggle callback.
        on_quit: Quit callback.
        get_last_sync_info: Last sync info callback.
        get_configs: Callback to get list of sync configs.
        get_schedules: Callback to get list of schedules.
        get_databases: Callback to get list of database integrations.
        is_paused: Is paused check callback.
        status_window: Optional status window instance.

    Returns:
        The global SystemTray instance.
    """
    global _tray
    if _tray is None:
        _tray = SystemTray(
            port=port,
            on_sync_now=on_sync_now,
            on_sync_config=on_sync_config,
            on_pause_toggle=on_pause_toggle,
            on_quit=on_quit,
            get_last_sync_info=get_last_sync_info,
            get_configs=get_configs,
            get_schedules=get_schedules,
            get_databases=get_databases,
            is_paused=is_paused,
            status_window=status_window,
        )
    return _tray
