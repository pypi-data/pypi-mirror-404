"""Auto-start configuration for the desktop application.

This module provides cross-platform auto-start functionality so the app
can launch automatically when the user logs in.

Supported platforms:
- Windows: Registry key in HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
- macOS: LaunchAgent plist in ~/Library/LaunchAgents/
- Linux: XDG autostart desktop file in ~/.config/autostart/
"""

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "MySQLToSheets"
APP_IDENTIFIER = "com.tla.mysql-to-sheets"


def get_executable_path() -> str:
    """Get the path to the current executable.

    Returns:
        Path to the executable (handles both frozen and development modes).
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return sys.executable
    else:
        # Running as Python script - return the Python interpreter with module
        return f'"{sys.executable}" -m mysql_to_sheets.desktop'


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def _is_linux() -> bool:
    return platform.system() == "Linux"


# ==============================================================================
# Windows Implementation
# ==============================================================================


def _windows_get_registry_key() -> str:
    """Get the Windows registry key path for auto-start."""
    return r"Software\Microsoft\Windows\CurrentVersion\Run"


def _windows_enable_autostart() -> bool:
    """Enable auto-start on Windows via registry."""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _windows_get_registry_key(),
            0,
            winreg.KEY_SET_VALUE,
        )
        executable = get_executable_path()
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, executable)
        winreg.CloseKey(key)
        logger.info(f"Windows auto-start enabled: {executable}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable Windows auto-start: {e}")
        return False


def _windows_disable_autostart() -> bool:
    """Disable auto-start on Windows via registry."""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _windows_get_registry_key(),
            0,
            winreg.KEY_SET_VALUE,
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass  # Already removed
        winreg.CloseKey(key)
        logger.info("Windows auto-start disabled")
        return True
    except Exception as e:
        logger.error(f"Failed to disable Windows auto-start: {e}")
        return False


def _windows_is_autostart_enabled() -> bool:
    """Check if auto-start is enabled on Windows."""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _windows_get_registry_key(),
            0,
            winreg.KEY_READ,
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


# ==============================================================================
# macOS Implementation
# ==============================================================================


def _macos_get_plist_path() -> Path:
    """Get the path to the LaunchAgent plist file."""
    return Path.home() / "Library" / "LaunchAgents" / f"{APP_IDENTIFIER}.plist"


def _macos_generate_plist() -> str:
    """Generate the LaunchAgent plist content."""
    executable = get_executable_path()

    # Handle both frozen and development modes
    if getattr(sys, "frozen", False):
        program_args = f"<string>{executable}</string>"
    else:
        # Running as Python module
        program_args = f"""<string>{sys.executable}</string>
        <string>-m</string>
        <string>mysql_to_sheets.desktop</string>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{APP_IDENTIFIER}</string>
    <key>ProgramArguments</key>
    <array>
        {program_args}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/{APP_IDENTIFIER}.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/{APP_IDENTIFIER}.error.log</string>
</dict>
</plist>
"""


def _macos_enable_autostart() -> bool:
    """Enable auto-start on macOS via LaunchAgent."""
    try:
        plist_path = _macos_get_plist_path()
        plist_path.parent.mkdir(parents=True, exist_ok=True)

        plist_content = _macos_generate_plist()
        plist_path.write_text(plist_content)

        # Load the LaunchAgent
        subprocess.run(
            ["launchctl", "load", str(plist_path)],
            check=True,
            capture_output=True,
        )

        logger.info(f"macOS auto-start enabled: {plist_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable macOS auto-start: {e}")
        return False


def _macos_disable_autostart() -> bool:
    """Disable auto-start on macOS via LaunchAgent."""
    try:
        plist_path = _macos_get_plist_path()

        if plist_path.exists():
            # Unload the LaunchAgent first
            subprocess.run(
                ["launchctl", "unload", str(plist_path)],
                check=False,  # Don't fail if not loaded
                capture_output=True,
            )
            plist_path.unlink()

        logger.info("macOS auto-start disabled")
        return True
    except Exception as e:
        logger.error(f"Failed to disable macOS auto-start: {e}")
        return False


def _macos_is_autostart_enabled() -> bool:
    """Check if auto-start is enabled on macOS."""
    return _macos_get_plist_path().exists()


# ==============================================================================
# Linux Implementation
# ==============================================================================


def _linux_get_desktop_file_path() -> Path:
    """Get the path to the XDG autostart desktop file."""
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_dir / "autostart" / f"{APP_NAME}.desktop"


def _linux_generate_desktop_file() -> str:
    """Generate the XDG desktop file content."""
    executable = get_executable_path()

    return f"""[Desktop Entry]
Type=Application
Name=MySQL to Google Sheets
Comment=Sync data from MySQL to Google Sheets
Exec={executable}
Icon=mysql-to-sheets
Terminal=false
Categories=Utility;Database;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""


def _linux_enable_autostart() -> bool:
    """Enable auto-start on Linux via XDG autostart."""
    try:
        desktop_path = _linux_get_desktop_file_path()
        desktop_path.parent.mkdir(parents=True, exist_ok=True)

        desktop_content = _linux_generate_desktop_file()
        desktop_path.write_text(desktop_content)

        # Make it executable
        desktop_path.chmod(0o755)

        logger.info(f"Linux auto-start enabled: {desktop_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable Linux auto-start: {e}")
        return False


def _linux_disable_autostart() -> bool:
    """Disable auto-start on Linux via XDG autostart."""
    try:
        desktop_path = _linux_get_desktop_file_path()

        if desktop_path.exists():
            desktop_path.unlink()

        logger.info("Linux auto-start disabled")
        return True
    except Exception as e:
        logger.error(f"Failed to disable Linux auto-start: {e}")
        return False


def _linux_is_autostart_enabled() -> bool:
    """Check if auto-start is enabled on Linux."""
    return _linux_get_desktop_file_path().exists()


# ==============================================================================
# Public API
# ==============================================================================


def enable_autostart() -> bool:
    """Enable auto-start for the current platform.

    Returns:
        True if auto-start was enabled successfully.
    """
    if _is_windows():
        return _windows_enable_autostart()
    elif _is_macos():
        return _macos_enable_autostart()
    elif _is_linux():
        return _linux_enable_autostart()
    else:
        logger.warning(f"Auto-start not supported on {platform.system()}")
        return False


def disable_autostart() -> bool:
    """Disable auto-start for the current platform.

    Returns:
        True if auto-start was disabled successfully.
    """
    if _is_windows():
        return _windows_disable_autostart()
    elif _is_macos():
        return _macos_disable_autostart()
    elif _is_linux():
        return _linux_disable_autostart()
    else:
        logger.warning(f"Auto-start not supported on {platform.system()}")
        return False


def is_autostart_enabled() -> bool:
    """Check if auto-start is enabled for the current platform.

    Returns:
        True if auto-start is currently enabled.
    """
    if _is_windows():
        return _windows_is_autostart_enabled()
    elif _is_macos():
        return _macos_is_autostart_enabled()
    elif _is_linux():
        return _linux_is_autostart_enabled()
    else:
        return False


def toggle_autostart() -> bool:
    """Toggle auto-start setting.

    Returns:
        True if auto-start is now enabled, False if disabled.
    """
    if is_autostart_enabled():
        disable_autostart()
        return False
    else:
        enable_autostart()
        return True


def is_supported() -> bool:
    """Check if auto-start is supported on the current platform.

    Returns:
        True if auto-start is supported.
    """
    return _is_windows() or _is_macos() or _is_linux()
