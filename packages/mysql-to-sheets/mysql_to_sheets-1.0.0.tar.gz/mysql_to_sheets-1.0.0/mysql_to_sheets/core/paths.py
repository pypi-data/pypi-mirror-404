"""Platform-aware path resolution for desktop application packaging.

This module provides functions to locate configuration, logs, and data directories
in a platform-appropriate way. It also handles detection of PyInstaller bundled
execution and ensures directories exist on first run.

Platform-specific directories:
    - Windows: %APPDATA%\\MySQLToSheets\\
    - macOS: ~/Library/Application Support/MySQLToSheets/
    - Linux: ~/.local/share/MySQLToSheets/
"""

import os
import sys
from pathlib import Path

# Application name used for directory naming
APP_NAME = "MySQLToSheets"


def is_bundled() -> bool:
    """Detect if running as a PyInstaller bundle.

    Returns:
        True if running from a PyInstaller bundle, False otherwise.
    """
    # PyInstaller sets sys.frozen when running as a bundle
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_bundle_dir() -> Path:
    """Get the directory where the bundled executable resides.

    Returns:
        Path to the bundle directory (where .exe or .app is located).
    """
    if is_bundled():
        # sys.executable points to the bundled executable
        return Path(sys.executable).parent
    # In development, return the package root
    return Path(__file__).parent.parent.parent


def get_meipass_dir() -> Path | None:
    """Get the PyInstaller _MEIPASS temporary extraction directory.

    This is where PyInstaller extracts bundled data files at runtime.

    Returns:
        Path to _MEIPASS directory if bundled, None otherwise.
    """
    if is_bundled():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return None


def get_platform_data_dir() -> Path:
    """Get the platform-specific application data directory.

    Returns:
        Path to the platform-appropriate data directory:
        - Windows: %APPDATA%\\MySQLToSheets
        - macOS: ~/Library/Application Support/MySQLToSheets
        - Linux: ~/.local/share/MySQLToSheets
    """
    if sys.platform == "win32":
        # Windows: %APPDATA%
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_NAME
        # Fallback to home directory
        return Path.home() / "AppData" / "Roaming" / APP_NAME
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support
        return Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        # Linux/Unix: ~/.local/share
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / APP_NAME
        return Path.home() / ".local" / "share" / APP_NAME


def get_config_dir() -> Path:
    """Get the directory for configuration files.

    This is where .env and service_account.json should be placed.

    Returns:
        Path to the configuration directory.
    """
    return get_platform_data_dir() / "config"


def get_logs_dir() -> Path:
    """Get the directory for log files.

    Returns:
        Path to the logs directory.
    """
    return get_platform_data_dir() / "logs"


def get_data_dir() -> Path:
    """Get the directory for data files (SQLite databases, etc.).

    Returns:
        Path to the data directory.
    """
    return get_platform_data_dir() / "data"


def ensure_directories() -> None:
    """Create all application directories if they don't exist.

    This should be called at application startup to ensure all
    required directories are present.
    """
    dirs = [
        get_platform_data_dir(),
        get_config_dir(),
        get_logs_dir(),
        get_data_dir(),
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


def get_default_service_account_path() -> Path:
    """Get the default path for the service account JSON file.

    Returns:
        Path where service_account.json should be located.
    """
    return get_config_dir() / "service_account.json"


def get_default_env_path() -> Path:
    """Get the default path for the .env file.

    Returns:
        Path where .env should be located.
    """
    return get_config_dir() / ".env"


def get_default_log_path() -> Path:
    """Get the default path for the sync log file.

    Returns:
        Path where sync.log should be located.
    """
    return get_logs_dir() / "sync.log"


def get_default_history_db_path() -> Path:
    """Get the default path for the history SQLite database.

    Returns:
        Path where history.db should be located.
    """
    return get_data_dir() / "history.db"


def get_default_api_keys_db_path() -> Path:
    """Get the default path for the API keys SQLite database.

    Returns:
        Path where api_keys.db should be located.
    """
    return get_data_dir() / "api_keys.db"


def get_default_scheduler_db_path() -> Path:
    """Get the default path for the scheduler SQLite database.

    Returns:
        Path where scheduler.db should be located.
    """
    return get_data_dir() / "scheduler.db"


def get_default_tenant_db_path() -> Path:
    """Get the default path for the tenant SQLite database.

    Returns:
        Path where tenant.db should be located.
    """
    return get_data_dir() / "tenant.db"


def find_env_file() -> Path | None:
    """Search for .env file in multiple locations.

    Searches in order:
    1. Current working directory
    2. Platform-specific config directory
    3. Executable directory (when bundled)
    4. Package root directory (development)

    Returns:
        Path to the first .env file found, or None if not found.
    """
    search_locations = [
        Path.cwd() / ".env",
        get_default_env_path(),
    ]

    if is_bundled():
        # Check next to the executable
        search_locations.append(get_bundle_dir() / ".env")
    else:
        # Development: check package root
        package_root = Path(__file__).parent.parent.parent
        search_locations.append(package_root / ".env")

    for location in search_locations:
        if location.exists():
            return location

    return None


def get_template_dir() -> Path:
    """Get the directory containing Flask/Jinja2 templates.

    Handles both development and PyInstaller bundled scenarios.

    Returns:
        Path to the templates directory.
    """
    if is_bundled():
        # Templates are extracted to _MEIPASS
        meipass = get_meipass_dir()
        if meipass:
            return meipass / "mysql_to_sheets" / "web" / "templates"
    # Development: relative to web module
    return Path(__file__).parent.parent / "web" / "templates"


def get_static_dir() -> Path:
    """Get the directory containing static assets (CSS, JS, images).

    Handles both development and PyInstaller bundled scenarios.

    Returns:
        Path to the static directory.
    """
    if is_bundled():
        # Static files are extracted to _MEIPASS
        meipass = get_meipass_dir()
        if meipass:
            return meipass / "mysql_to_sheets" / "web" / "static"
    # Development: relative to web module
    return Path(__file__).parent.parent / "web" / "static"


def is_first_run() -> bool:
    """Check if this is the first run of the application.

    First run is detected by checking if the .env file exists
    in the platform config directory.

    Returns:
        True if .env file does not exist in config directory.
    """
    return not get_default_env_path().exists()


def copy_env_example() -> bool:
    """Copy .env.example to the config directory if it doesn't exist.

    Returns:
        True if file was copied, False otherwise.
    """
    dest = get_default_env_path()
    if dest.exists():
        return False

    # Look for .env.example
    if is_bundled():
        meipass = get_meipass_dir()
        if meipass:
            source = meipass / ".env.example"
        else:
            return False
    else:
        source = Path(__file__).parent.parent.parent / ".env.example"

    if source.exists():
        ensure_directories()
        dest.write_text(source.read_text())
        return True

    return False
