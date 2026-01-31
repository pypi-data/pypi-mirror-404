"""MySQL to Google Sheets sync package.

A Python package that synchronizes data from MySQL databases to Google Sheets
using Service Account authentication. Supports CLI, REST API, Web Dashboard,
and Desktop Application interfaces.
"""

__version__ = "1.0.0"
__author__ = "Texas Longhorn Analytics"

from mysql_to_sheets.core.config import Config, get_config, reset_config
from mysql_to_sheets.core.config_factory import (
    get_config_provider,
    provider_context,
    set_config_provider,
)
from mysql_to_sheets.core.config_provider import ConfigProvider
from mysql_to_sheets.core.database_config_provider import DatabaseConfigProvider
from mysql_to_sheets.core.env_config_provider import EnvConfigProvider
from mysql_to_sheets.core.exceptions import (
    ConfigError,
    DatabaseError,
    SheetsError,
    SyncError,
)
from mysql_to_sheets.core.sync import SyncResult, SyncService, run_sync

__all__ = [
    # Version
    "__version__",
    # Config
    "Config",
    "get_config",
    "reset_config",
    # Config Providers
    "ConfigProvider",
    "EnvConfigProvider",
    "DatabaseConfigProvider",
    "get_config_provider",
    "set_config_provider",
    "provider_context",
    # Sync
    "run_sync",
    "SyncResult",
    "SyncService",
    # Exceptions
    "SyncError",
    "ConfigError",
    "DatabaseError",
    "SheetsError",
]
