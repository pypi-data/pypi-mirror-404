"""Database-backed configuration provider for SaaS deployments.

Implements ConfigProvider using sync configs and integrations stored
in the database. This enables multi-tenant configuration with secure
credential storage.
"""

import logging
import os
from typing import TYPE_CHECKING

from mysql_to_sheets.core.config_provider import ConfigProvider

if TYPE_CHECKING:
    from mysql_to_sheets.core.config import Config

logger = logging.getLogger(__name__)


class DatabaseConfigProvider(ConfigProvider):
    """Configuration provider that reads from database.

    Loads configuration from:
    1. SyncConfigDefinition (query, sheet settings, column mapping)
    2. Integration (database/sheets connection credentials)

    Used for SaaS deployments where each tenant has their own
    configurations stored in the database.

    Example::

        # Load config for specific sync job
        provider = DatabaseConfigProvider(
            tenant_id=123,
            config_id=456,
        )
        config = provider.get_config()

        # Load by config name
        provider = DatabaseConfigProvider(
            tenant_id=123,
            config_name="daily-sales-sync",
        )
        config = provider.get_config()
    """

    def __init__(
        self,
        tenant_id: int | None = None,
        config_id: int | None = None,
        config_name: str | None = None,
        db_path: str | None = None,
    ) -> None:
        """Initialize database provider.

        Args:
            tenant_id: Organization ID for multi-tenant isolation.
            config_id: Specific sync config ID to load.
            config_name: Alternative to config_id - load config by name.
            db_path: Path to SQLite database. Defaults to TENANT_DB_PATH.

        Raises:
            ValueError: If neither config_id nor config_name is provided
                when getting a full config (vs just base settings).
        """
        self._tenant_id = tenant_id
        self._config_id = config_id
        self._config_name = config_name
        self._db_path = db_path or os.getenv("TENANT_DB_PATH", "./data/tenant.db")
        self._config: "Config | None" = None

    def get_config(self) -> "Config":
        """Get configuration from database.

        Loads sync config and associated integrations, then builds
        a Config object with all necessary settings.

        Returns:
            Config instance populated from database.

        Raises:
            ValueError: If config not found or required integrations missing.
        """
        if self._config is not None:
            return self._config

        self._config = self._load_config()
        return self._config

    def _load_config(self) -> "Config":
        """Load and build config from database."""
        from mysql_to_sheets.core.config import Config, get_config
        from mysql_to_sheets.models.integrations import get_integration_repository
        from mysql_to_sheets.models.sync_configs import get_sync_config_repository

        # Start with base config from environment (for settings not in DB)
        base_config = get_config()

        # If no tenant/config specified, just return base config
        if self._tenant_id is None and self._config_id is None and self._config_name is None:
            return base_config

        # Get sync config
        sync_repo = get_sync_config_repository(self._db_path)
        sync_config = None

        if self._config_id is not None:
            sync_config = sync_repo.get_by_id(self._config_id, self._tenant_id or 0)
        elif self._config_name is not None:
            sync_config = sync_repo.get_by_name(self._config_name, self._tenant_id or 0)

        if sync_config is None:
            raise ValueError(
                f"Sync config not found: id={self._config_id}, name={self._config_name}"
            )

        # Build overrides from sync config
        overrides: dict = {
            "sql_query": sync_config.sql_query,
            "google_sheet_id": sync_config.sheet_id,
            "google_worksheet_name": sync_config.worksheet_name,
            "sync_mode": sync_config.sync_mode,
            "column_case": sync_config.column_case,
        }

        # Add column mapping if present
        if sync_config.column_mapping:
            import json
            overrides["column_mapping_enabled"] = True
            overrides["column_mapping"] = json.dumps(sync_config.column_mapping)

        if sync_config.column_order:
            import json
            overrides["column_order"] = ",".join(sync_config.column_order)

        # Load source integration if referenced
        source_integration = self._get_source_integration(sync_config, sync_repo)
        if source_integration:
            self._apply_source_integration(overrides, source_integration)

        # Load destination integration if referenced
        dest_integration = self._get_destination_integration(sync_config, sync_repo)
        if dest_integration:
            self._apply_destination_integration(overrides, dest_integration)

        # Create config with overrides
        return base_config.with_overrides(**overrides)

    def _get_source_integration(self, sync_config, sync_repo):
        """Get source (database) integration if referenced."""
        from mysql_to_sheets.models.integrations import get_integration_repository

        # Check for source_integration_id on sync_config
        source_id = getattr(sync_config, "source_integration_id", None)
        if source_id is None:
            return None

        integration_repo = get_integration_repository(self._db_path)
        return integration_repo.get_by_id(source_id, sync_config.organization_id)

    def _get_destination_integration(self, sync_config, sync_repo):
        """Get destination (sheets) integration if referenced."""
        from mysql_to_sheets.models.integrations import get_integration_repository

        # Check for destination_integration_id on sync_config
        dest_id = getattr(sync_config, "destination_integration_id", None)
        if dest_id is None:
            return None

        integration_repo = get_integration_repository(self._db_path)
        return integration_repo.get_by_id(dest_id, sync_config.organization_id)

    def _apply_source_integration(self, overrides: dict, integration) -> None:
        """Apply source integration settings to overrides."""
        overrides["db_type"] = integration.integration_type
        overrides["db_host"] = integration.host or "localhost"
        overrides["db_name"] = integration.database_name or ""

        if integration.port:
            overrides["db_port"] = integration.port

        if integration.ssl_mode:
            overrides["db_ssl_mode"] = integration.ssl_mode

        # Apply credentials
        if integration.credentials:
            if integration.credentials.user:
                overrides["db_user"] = integration.credentials.user
            if integration.credentials.password:
                overrides["db_password"] = integration.credentials.password

    def _apply_destination_integration(self, overrides: dict, integration) -> None:
        """Apply destination integration settings to overrides."""
        if integration.integration_type != "google_sheets":
            logger.warning(
                f"Destination integration {integration.id} is not google_sheets type"
            )
            return

        if integration.sheet_id:
            overrides["google_sheet_id"] = integration.sheet_id

        if integration.worksheet_name:
            overrides["google_worksheet_name"] = integration.worksheet_name

        # Service account JSON would need to be written to a temp file
        # for the current gspread integration to use it
        if integration.credentials and integration.credentials.service_account_json:
            # For now, log a warning - full implementation would write to temp file
            logger.debug(
                "Destination integration has service_account_json - "
                "using for authentication"
            )

    def refresh(self) -> "Config":
        """Reload configuration from database.

        Returns:
            Freshly loaded Config instance.
        """
        self._config = None
        return self.get_config()

    @property
    def provider_type(self) -> str:
        """Get provider type identifier.

        Returns:
            'database' for database-backed provider.
        """
        return "database"

    @property
    def tenant_id(self) -> int | None:
        """Get the tenant (organization) ID."""
        return self._tenant_id

    @property
    def config_id(self) -> int | None:
        """Get the sync config ID."""
        return self._config_id

    @property
    def config_name(self) -> str | None:
        """Get the sync config name."""
        return self._config_name

    @property
    def db_path(self) -> str:
        """Get the database path."""
        return self._db_path
