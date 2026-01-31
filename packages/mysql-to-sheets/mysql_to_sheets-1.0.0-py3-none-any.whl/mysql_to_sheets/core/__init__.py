"""Core business logic for MySQL to Google Sheets sync."""

from mysql_to_sheets.core.config import Config, get_config, reset_config
from mysql_to_sheets.core.config_factory import (
    clear_config_provider,
    get_config_provider,
    get_current_provider,
    provider_context,
    reset_config_provider_factory,
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

# Import from sync package (which re-exports from sync_legacy.py)
# This maintains backward compatibility while enabling the new pipeline architecture
from mysql_to_sheets.core.sync import (
    SyncResult,
    SyncService,
    clean_data,
    clean_value,
    fetch_data,
    push_to_sheets,
    run_sync,
)

__all__ = [
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
    "clear_config_provider",
    "get_current_provider",
    "provider_context",
    "reset_config_provider_factory",
    # Sync
    "run_sync",
    "SyncResult",
    "SyncService",
    "fetch_data",
    "clean_data",
    "clean_value",
    "push_to_sheets",
    # Exceptions
    "SyncError",
    "ConfigError",
    "DatabaseError",
    "SheetsError",
]
