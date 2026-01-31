"""Multi-config file loader for YAML/JSON sync configurations.

Supports loading multiple sync configurations from a single YAML or JSON
file with environment variable substitution.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from mysql_to_sheets.models.sync_configs import (
    SyncConfigDefinition,
)

# Pattern for environment variable substitution: ${VAR_NAME} or ${VAR_NAME:-default}
ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


@dataclass
class DatabaseConfig:
    """Database configuration from config file.

    Holds database connection settings that can be shared
    across multiple sync configurations.
    """

    host: str = "localhost"
    port: int = 3306
    user: str = ""
    password: str = ""
    name: str = ""
    db_type: str = "mysql"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "name": self.name,
            "db_type": self.db_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatabaseConfig":
        """Create from dictionary.

        Args:
            data: Dictionary with database config.

        Returns:
            DatabaseConfig instance.
        """
        return cls(
            host=data.get("host", "localhost"),
            port=int(data.get("port", 3306)),
            user=data.get("user", ""),
            password=data.get("password", ""),
            name=data.get("name", ""),
            db_type=data.get("db_type", "mysql"),
        )


@dataclass
class MultiSyncConfig:
    """Container for multiple sync configurations.

    Holds shared database config and a list of individual
    sync configurations loaded from a file.
    """

    database: DatabaseConfig
    syncs: list[SyncConfigDefinition] = field(default_factory=list)
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation.
        """
        return {
            "version": self.version,
            "database": self.database.to_dict(),
            "syncs": [s.to_dict() for s in self.syncs],
        }

    def validate(self) -> list[str]:
        """Validate the configuration.

        Returns:
            List of validation error messages.
        """
        errors = []

        # Validate database config
        if not self.database.user:
            errors.append("Database user is required")
        if not self.database.name:
            errors.append("Database name is required")

        # Validate each sync config
        for i, sync in enumerate(self.syncs):
            sync_errors = sync.validate()
            for err in sync_errors:
                errors.append(f"syncs[{i}] ({sync.name or 'unnamed'}): {err}")

        # Check for duplicate names
        names = [s.name for s in self.syncs]
        duplicates = [n for n in names if names.count(n) > 1]
        if duplicates:
            errors.append(f"Duplicate sync names found: {set(duplicates)}")

        return errors


def substitute_env_vars(value: Any) -> Any:
    """Recursively substitute environment variables in a value.

    Supports ${VAR_NAME} and ${VAR_NAME:-default} syntax.

    Args:
        value: Value to process (string, dict, or list).

    Returns:
        Value with environment variables substituted.
    """
    if isinstance(value, str):

        def replace_match(match: re.Match[str]) -> str:
            var_name = match.group(1)
            default = match.group(2)
            return os.getenv(var_name, default if default is not None else "")

        return ENV_VAR_PATTERN.sub(replace_match, value)

    elif isinstance(value, dict):
        return {k: substitute_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [substitute_env_vars(item) for item in value]

    return value


def load_config_file(
    path: Path | str,
    organization_id: int = 0,
    logger: logging.Logger | None = None,
) -> MultiSyncConfig:
    """Load sync configurations from a YAML or JSON file.

    Supports environment variable substitution in values.

    Args:
        path: Path to the configuration file.
        organization_id: Organization ID to assign to configs.
        logger: Optional logger.

    Returns:
        MultiSyncConfig with database settings and sync definitions.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file format is invalid.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    if logger:
        logger.info(f"Loading configuration from {path}")

    # Read and parse file
    content = path.read_text(encoding="utf-8")

    if path.suffix.lower() in (".yaml", ".yml"):
        data = yaml.safe_load(content)
    elif path.suffix.lower() == ".json":
        data = json.loads(content)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .yaml, .yml, or .json")

    if not isinstance(data, dict):
        raise ValueError("Configuration file must contain a dictionary at the root level")

    # Substitute environment variables
    data = substitute_env_vars(data)

    # Parse database config
    db_data = data.get("database", {})
    database = DatabaseConfig.from_dict(db_data)

    # Parse sync configs
    syncs_data = data.get("syncs", [])
    if not isinstance(syncs_data, list):
        raise ValueError("'syncs' must be a list")

    syncs = []
    for i, sync_data in enumerate(syncs_data):
        if not isinstance(sync_data, dict):
            raise ValueError(f"syncs[{i}] must be a dictionary")

        # Normalize field names (support both 'query' and 'sql_query')
        if "query" in sync_data and "sql_query" not in sync_data:
            sync_data["sql_query"] = sync_data.pop("query")

        # Normalize worksheet name field
        if "worksheet" in sync_data and "worksheet_name" not in sync_data:
            sync_data["worksheet_name"] = sync_data.pop("worksheet")

        # Set organization ID
        sync_data["organization_id"] = organization_id

        try:
            sync = SyncConfigDefinition.from_dict(sync_data)
            syncs.append(sync)
        except KeyError as e:
            raise ValueError(f"syncs[{i}]: missing required field {e}")

    config = MultiSyncConfig(
        database=database,
        syncs=syncs,
        version=data.get("version", "1.0"),
    )

    if logger:
        logger.info(f"Loaded {len(syncs)} sync configurations")

    return config


def save_config_file(
    config: MultiSyncConfig,
    path: Path | str,
    format: str = "yaml",
    logger: logging.Logger | None = None,
) -> None:
    """Save sync configurations to a YAML or JSON file.

    Args:
        config: MultiSyncConfig to save.
        path: Output file path.
        format: Output format ("yaml" or "json").
        logger: Optional logger.

    Raises:
        ValueError: If format is invalid.
    """
    path = Path(path)

    if format not in ("yaml", "json"):
        raise ValueError(f"Invalid format: {format}. Use 'yaml' or 'json'")

    data = config.to_dict()

    # Remove organization_id from saved syncs (set at load time)
    for sync in data["syncs"]:
        sync.pop("organization_id", None)
        sync.pop("id", None)
        sync.pop("created_at", None)
        sync.pop("updated_at", None)
        sync.pop("created_by_user_id", None)

    if format == "yaml":
        content = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    else:
        content = json.dumps(data, indent=2)

    path.write_text(content, encoding="utf-8")

    if logger:
        logger.info(f"Saved {len(config.syncs)} sync configurations to {path}")


def export_configs_to_file(
    configs: list[SyncConfigDefinition],
    path: Path | str,
    database_config: DatabaseConfig | None = None,
    format: str = "yaml",
    logger: logging.Logger | None = None,
) -> None:
    """Export sync configurations to a YAML or JSON file.

    Args:
        configs: List of configurations to export.
        path: Output file path.
        database_config: Optional database config to include.
        format: Output format ("yaml" or "json").
        logger: Optional logger.
    """
    if database_config is None:
        database_config = DatabaseConfig()

    multi_config = MultiSyncConfig(
        database=database_config,
        syncs=configs,
    )

    save_config_file(multi_config, path, format, logger)


def create_example_config() -> MultiSyncConfig:
    """Create an example configuration for documentation.

    Returns:
        Example MultiSyncConfig with sample data.
    """
    database = DatabaseConfig(
        host="${DB_HOST:-localhost}",
        port=3306,
        user="${DB_USER}",
        password="${DB_PASSWORD}",
        name="${DB_NAME}",
        db_type="mysql",
    )

    syncs = [
        SyncConfigDefinition(
            name="customers",
            description="Sync active customers to Google Sheets",
            sql_query="SELECT id, name, email, created_at FROM customers WHERE active = 1",
            sheet_id="your-sheet-id-here",
            worksheet_name="Customers",
            organization_id=0,
            column_mapping={
                "id": "Customer ID",
                "name": "Full Name",
                "email": "Email Address",
                "created_at": "Registration Date",
            },
            sync_mode="replace",
        ),
        SyncConfigDefinition(
            name="recent_orders",
            description="Sync orders from the last 30 days",
            sql_query="SELECT * FROM orders WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)",
            sheet_id="your-sheet-id-here",
            worksheet_name="Recent Orders",
            organization_id=0,
            sync_mode="append",
        ),
    ]

    return MultiSyncConfig(database=database, syncs=syncs)


def validate_config_file(
    path: Path | str,
    logger: logging.Logger | None = None,
) -> tuple[bool, list[str]]:
    """Validate a configuration file.

    Args:
        path: Path to the configuration file.
        logger: Optional logger.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    try:
        config = load_config_file(path, organization_id=0, logger=logger)
        errors = config.validate()
        return len(errors) == 0, errors
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as e:
        return False, [str(e)]


def merge_configs(
    *configs: MultiSyncConfig,
    logger: logging.Logger | None = None,
) -> MultiSyncConfig:
    """Merge multiple configurations into one.

    Uses database config from first config. Deduplicates syncs by name.

    Args:
        *configs: Configurations to merge.
        logger: Optional logger.

    Returns:
        Merged configuration.

    Raises:
        ValueError: If no configs provided.
    """
    if not configs:
        raise ValueError("At least one configuration is required")

    # Use database from first config
    database = configs[0].database

    # Collect all syncs, deduplicating by name (last wins)
    syncs_by_name: dict[str, SyncConfigDefinition] = {}
    for config in configs:
        for sync in config.syncs:
            syncs_by_name[sync.name] = sync

    syncs = list(syncs_by_name.values())

    if logger:
        logger.info(f"Merged {len(configs)} configs into {len(syncs)} sync definitions")

    return MultiSyncConfig(database=database, syncs=syncs)
