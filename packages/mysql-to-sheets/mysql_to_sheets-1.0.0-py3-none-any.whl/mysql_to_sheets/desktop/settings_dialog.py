"""Settings dialog for the desktop application.

This module provides a native settings dialog with tabbed interface
for configuring application preferences.
"""

import json
import logging
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Default settings
DEFAULT_SETTINGS = {
    # General
    "start_on_login": False,
    "show_notifications": True,
    "minimize_to_tray": True,
    "show_status_window_on_start": False,
    # Sync
    "default_sync_mode": "replace",
    "chunk_size": 1000,
    "retry_attempts": 3,
    # Notifications
    "notify_on_success": True,
    "notify_on_failure": True,
    "play_sound": False,
    # Shortcuts
    "shortcuts_enabled": True,
}


def get_settings_path() -> Path:
    """Get the path to the settings file.

    Returns:
        Path to settings.json in user's config directory.
    """
    # Use platform-appropriate config directory
    try:
        from mysql_to_sheets.desktop.paths import get_config_dir

        return get_config_dir() / "settings.json"
    except ImportError:
        # Fallback to home directory
        return Path.home() / ".mysql-to-sheets" / "settings.json"


def load_settings() -> dict[str, Any]:
    """Load settings from file.

    Returns:
        Dictionary of settings, with defaults for missing keys.
    """
    settings = DEFAULT_SETTINGS.copy()
    settings_path = get_settings_path()

    if settings_path.exists():
        try:
            with open(settings_path) as f:
                saved = json.load(f)
                settings.update(saved)
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")

    return settings


def save_settings(settings: dict[str, Any]) -> bool:
    """Save settings to file.

    Args:
        settings: Dictionary of settings to save.

    Returns:
        True if saved successfully.
    """
    settings_path = get_settings_path()

    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return False


class SettingsDialog:
    """Native settings dialog with tabbed interface.

    Features:
    - General tab: Start on login, notifications, minimize to tray
    - Sync tab: Default mode, chunk size, retry attempts
    - Notifications tab: Success/failure notifications, sound
    """

    def __init__(
        self,
        parent=None,
        on_save: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        """Initialize the settings dialog.

        Args:
            parent: Parent window (optional).
            on_save: Callback when settings are saved.
        """
        self._parent = parent
        self._on_save = on_save
        self._dialog = None
        self._settings = load_settings()

        # UI elements (set when dialog is created)
        self._notebook = None
        self._vars: dict[str, Any] = {}

        self._ttkbootstrap_available = self._check_ttkbootstrap()

    def _check_ttkbootstrap(self) -> bool:
        """Check if ttkbootstrap is available."""
        try:
            import ttkbootstrap  # noqa: F401

            return True
        except ImportError:
            logger.warning(
                "ttkbootstrap not installed. Settings dialog will be disabled. "
                "Install with: pip install ttkbootstrap"
            )
            return False

    @property
    def is_available(self) -> bool:
        """Check if the settings dialog is available."""
        return self._ttkbootstrap_available

    def _create_dialog(self) -> None:
        """Create the settings dialog UI."""
        import ttkbootstrap as ttk
        from ttkbootstrap.constants import BOTH, BOTTOM, LEFT, RIGHT, TOP, W, X, Y

        # Create dialog window
        if self._parent:
            self._dialog = ttk.Toplevel(self._parent)
        else:
            self._dialog = ttk.Toplevel()

        self._dialog.title("Settings")
        self._dialog.geometry("480x420")
        self._dialog.resizable(False, False)

        # Make modal
        self._dialog.transient(self._parent)
        self._dialog.grab_set()

        # Main container
        main_frame = ttk.Frame(self._dialog, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # Create notebook for tabs
        self._notebook = ttk.Notebook(main_frame, bootstyle="dark")
        self._notebook.pack(fill=BOTH, expand=True, pady=(0, 15))

        # Create tabs
        self._create_general_tab()
        self._create_sync_tab()
        self._create_notifications_tab()
        self._create_shortcuts_tab()

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X)

        ttk.Button(
            btn_frame,
            text="Cancel",
            bootstyle="secondary-outline",
            command=self._on_cancel,
        ).pack(side=RIGHT, padx=(10, 0))

        ttk.Button(
            btn_frame,
            text="Save",
            bootstyle="success",
            command=self._on_save_click,
        ).pack(side=RIGHT)

        ttk.Button(
            btn_frame,
            text="Reset to Defaults",
            bootstyle="warning-outline",
            command=self._on_reset,
        ).pack(side=LEFT)

    def _create_general_tab(self) -> None:
        """Create the General settings tab."""
        import ttkbootstrap as ttk
        from ttkbootstrap.constants import W, X

        frame = ttk.Frame(self._notebook, padding=20)
        self._notebook.add(frame, text="  General  ")

        # Start on login
        self._vars["start_on_login"] = ttk.BooleanVar(
            value=self._settings.get("start_on_login", False)
        )
        ttk.Checkbutton(
            frame,
            text="Start application on system login",
            variable=self._vars["start_on_login"],
            bootstyle="round-toggle",
        ).pack(anchor=W, pady=(0, 15))

        # Show notifications
        self._vars["show_notifications"] = ttk.BooleanVar(
            value=self._settings.get("show_notifications", True)
        )
        ttk.Checkbutton(
            frame,
            text="Show system notifications",
            variable=self._vars["show_notifications"],
            bootstyle="round-toggle",
        ).pack(anchor=W, pady=(0, 15))

        # Minimize to tray
        self._vars["minimize_to_tray"] = ttk.BooleanVar(
            value=self._settings.get("minimize_to_tray", True)
        )
        ttk.Checkbutton(
            frame,
            text="Minimize to system tray on close",
            variable=self._vars["minimize_to_tray"],
            bootstyle="round-toggle",
        ).pack(anchor=W, pady=(0, 15))

        # Show status window on start
        self._vars["show_status_window_on_start"] = ttk.BooleanVar(
            value=self._settings.get("show_status_window_on_start", False)
        )
        ttk.Checkbutton(
            frame,
            text="Show status window when application starts",
            variable=self._vars["show_status_window_on_start"],
            bootstyle="round-toggle",
        ).pack(anchor=W, pady=(0, 15))

    def _create_sync_tab(self) -> None:
        """Create the Sync settings tab."""
        import ttkbootstrap as ttk
        from ttkbootstrap.constants import LEFT, W, X

        frame = ttk.Frame(self._notebook, padding=20)
        self._notebook.add(frame, text="  Sync  ")

        # Default sync mode
        mode_frame = ttk.Frame(frame)
        mode_frame.pack(fill=X, pady=(0, 15))

        ttk.Label(mode_frame, text="Default sync mode:").pack(anchor=W)
        self._vars["default_sync_mode"] = ttk.StringVar(
            value=self._settings.get("default_sync_mode", "replace")
        )
        mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self._vars["default_sync_mode"],
            values=["replace", "append", "streaming"],
            state="readonly",
            width=25,
        )
        mode_combo.pack(anchor=W, pady=(5, 0))

        # Chunk size
        chunk_frame = ttk.Frame(frame)
        chunk_frame.pack(fill=X, pady=(0, 15))

        ttk.Label(chunk_frame, text="Streaming chunk size:").pack(anchor=W)
        self._vars["chunk_size"] = ttk.IntVar(
            value=self._settings.get("chunk_size", 1000)
        )
        chunk_spin = ttk.Spinbox(
            chunk_frame,
            from_=100,
            to=10000,
            increment=100,
            textvariable=self._vars["chunk_size"],
            width=10,
        )
        chunk_spin.pack(anchor=W, pady=(5, 0))
        ttk.Label(
            chunk_frame,
            text="Rows per batch in streaming mode",
            font=("", 9),
            foreground="#94a3b8",
        ).pack(anchor=W)

        # Retry attempts
        retry_frame = ttk.Frame(frame)
        retry_frame.pack(fill=X, pady=(0, 15))

        ttk.Label(retry_frame, text="Retry attempts:").pack(anchor=W)
        self._vars["retry_attempts"] = ttk.IntVar(
            value=self._settings.get("retry_attempts", 3)
        )
        retry_spin = ttk.Spinbox(
            retry_frame,
            from_=0,
            to=10,
            increment=1,
            textvariable=self._vars["retry_attempts"],
            width=10,
        )
        retry_spin.pack(anchor=W, pady=(5, 0))
        ttk.Label(
            retry_frame,
            text="Number of retries on transient failures",
            font=("", 9),
            foreground="#94a3b8",
        ).pack(anchor=W)

    def _create_notifications_tab(self) -> None:
        """Create the Notifications settings tab."""
        import ttkbootstrap as ttk
        from ttkbootstrap.constants import W

        frame = ttk.Frame(self._notebook, padding=20)
        self._notebook.add(frame, text="  Notifications  ")

        # Notify on success
        self._vars["notify_on_success"] = ttk.BooleanVar(
            value=self._settings.get("notify_on_success", True)
        )
        ttk.Checkbutton(
            frame,
            text="Notify when sync completes successfully",
            variable=self._vars["notify_on_success"],
            bootstyle="round-toggle",
        ).pack(anchor=W, pady=(0, 15))

        # Notify on failure
        self._vars["notify_on_failure"] = ttk.BooleanVar(
            value=self._settings.get("notify_on_failure", True)
        )
        ttk.Checkbutton(
            frame,
            text="Notify when sync fails",
            variable=self._vars["notify_on_failure"],
            bootstyle="round-toggle",
        ).pack(anchor=W, pady=(0, 15))

        # Play sound
        self._vars["play_sound"] = ttk.BooleanVar(
            value=self._settings.get("play_sound", False)
        )
        ttk.Checkbutton(
            frame,
            text="Play sound with notifications",
            variable=self._vars["play_sound"],
            bootstyle="round-toggle",
        ).pack(anchor=W, pady=(0, 15))

    def _create_shortcuts_tab(self) -> None:
        """Create the Shortcuts settings tab."""
        import platform

        import ttkbootstrap as ttk
        from ttkbootstrap.constants import BOTH, BOTTOM, LEFT, TOP, W, X, Y

        frame = ttk.Frame(self._notebook, padding=20)
        self._notebook.add(frame, text="  Shortcuts  ")

        # Enable shortcuts checkbox
        self._vars["shortcuts_enabled"] = ttk.BooleanVar(
            value=self._settings.get("shortcuts_enabled", True)
        )
        ttk.Checkbutton(
            frame,
            text="Enable global keyboard shortcuts",
            variable=self._vars["shortcuts_enabled"],
            bootstyle="round-toggle",
        ).pack(anchor=W, pady=(0, 15))

        # Get platform-specific modifier
        primary_mod = "Cmd" if platform.system() == "Darwin" else "Ctrl"

        # Shortcuts list
        shortcuts_frame = ttk.LabelFrame(frame, text="Configured Shortcuts", padding=10)
        shortcuts_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        # Column headers
        header_frame = ttk.Frame(shortcuts_frame)
        header_frame.pack(fill=X, pady=(0, 5))
        ttk.Label(header_frame, text="Action", font=("", 9, "bold"), width=25).pack(side=LEFT)
        ttk.Label(header_frame, text="Shortcut", font=("", 9, "bold"), width=20).pack(side=LEFT)

        # Shortcut rows (display only - editing not implemented yet)
        shortcuts = [
            ("Trigger Sync", f"{primary_mod}+Shift+S"),
            ("Open Dashboard", f"{primary_mod}+Shift+D"),
            ("Toggle Status Window", f"{primary_mod}+Shift+W"),
            ("Pause/Resume", f"{primary_mod}+Shift+P"),
        ]

        for action, shortcut in shortcuts:
            row = ttk.Frame(shortcuts_frame)
            row.pack(fill=X, pady=2)
            ttk.Label(row, text=action, width=25).pack(side=LEFT)
            ttk.Label(row, text=shortcut, foreground="#64748b", width=20).pack(side=LEFT)

        # Platform note
        if platform.system() == "Darwin":
            note_text = (
                "Note: Global hotkeys require Accessibility permission. "
                "Grant access in System Preferences > Security & Privacy > Privacy > Accessibility."
            )
        elif platform.system() == "Linux":
            note_text = (
                "Note: Global hotkeys may require X11 and membership in the 'input' group."
            )
        else:
            note_text = ""

        if note_text:
            ttk.Label(
                frame,
                text=note_text,
                font=("", 8),
                foreground="#94a3b8",
                wraplength=400,
            ).pack(anchor=W, pady=(10, 0))

    def _gather_settings(self) -> dict[str, Any]:
        """Gather current settings from UI elements.

        Returns:
            Dictionary of current settings.
        """
        settings = {}
        for key, var in self._vars.items():
            settings[key] = var.get()
        return settings

    def _apply_settings(self, settings: dict[str, Any]) -> None:
        """Apply settings to UI elements.

        Args:
            settings: Dictionary of settings to apply.
        """
        for key, value in settings.items():
            if key in self._vars:
                self._vars[key].set(value)

    def _on_save_click(self) -> None:
        """Handle save button click."""
        settings = self._gather_settings()
        if save_settings(settings):
            self._settings = settings
            if self._on_save:
                try:
                    self._on_save(settings)
                except Exception as e:
                    logger.warning(f"Save callback failed: {e}")
            self._dialog.destroy()
            self._dialog = None
        else:
            # Show error (simple approach - could use a messagebox)
            logger.error("Failed to save settings")

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if self._dialog:
            self._dialog.destroy()
            self._dialog = None

    def _on_reset(self) -> None:
        """Handle reset to defaults button click."""
        self._apply_settings(DEFAULT_SETTINGS)

    def show(self) -> None:
        """Show the settings dialog."""
        if not self.is_available:
            logger.warning("Settings dialog not available (ttkbootstrap not installed)")
            return

        if self._dialog is None:
            self._create_dialog()

        if self._dialog:
            self._dialog.deiconify()
            self._dialog.lift()
            self._dialog.focus_force()

    def destroy(self) -> None:
        """Destroy the dialog."""
        if self._dialog:
            try:
                self._dialog.destroy()
            except Exception:
                pass
            self._dialog = None


def create_settings_dialog(
    parent=None,
    on_save: Callable[[dict[str, Any]], None] | None = None,
) -> SettingsDialog | None:
    """Create a settings dialog if ttkbootstrap is available.

    Args:
        parent: Parent window (optional).
        on_save: Callback when settings are saved.

    Returns:
        SettingsDialog instance or None if ttkbootstrap not available.
    """
    dialog = SettingsDialog(parent=parent, on_save=on_save)
    if dialog.is_available:
        return dialog
    return None
