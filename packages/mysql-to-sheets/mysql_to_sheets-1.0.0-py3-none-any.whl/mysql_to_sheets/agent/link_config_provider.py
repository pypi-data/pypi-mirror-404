"""ConfigProvider that fetches sync configs from the control plane.

This provider:
1. Authenticates to control plane using LINK_TOKEN
2. Fetches sync configurations (query, sheet_id, mappings)
3. Merges with local credentials from environment/keychain
4. Returns a Config object ready for sync operations

Security: Database credentials never leave the customer network.
"""

import logging
import os
from typing import TYPE_CHECKING, Any

from mysql_to_sheets.core.config_provider import ConfigProvider
from mysql_to_sheets.core.exceptions import ConfigError

if TYPE_CHECKING:
    from mysql_to_sheets.core.config import Config

logger = logging.getLogger(__name__)


class LinkConfigProvider(ConfigProvider):
    """ConfigProvider that fetches sync configs from the SaaS control plane.

    Combines remote sync configuration (query, sheet_id, mappings) with
    local credentials (database password, service account). This ensures
    sensitive credentials never touch the control plane.

    Example usage::

        provider = LinkConfigProvider(
            control_plane_url="https://app.mysql-to-sheets.com",
            link_token="eyJhbGciOiJSUzI1NiI...",
            config_name="daily-sales",
        )
        config = provider.get_config()

        # Config has:
        # - sql_query from control plane
        # - google_sheet_id from control plane
        # - column_mapping from control plane
        # - db_password from local environment
        # - service_account_file from local filesystem

    Attributes:
        control_plane_url: Base URL of the control plane API.
        link_token: RS256-signed JWT for authentication.
        config_name: Name of the sync config to fetch.
    """

    def __init__(
        self,
        control_plane_url: str | None = None,
        link_token: str | None = None,
        config_name: str | None = None,
        config_id: int | None = None,
    ) -> None:
        """Initialize the link config provider.

        Args:
            control_plane_url: Base URL of the control plane API.
                Defaults to CONTROL_PLANE_URL env var.
            link_token: RS256 JWT for authentication.
                Defaults to LINK_TOKEN env var.
            config_name: Name of the sync config to fetch.
                Required if config_id is not provided.
            config_id: ID of the sync config to fetch.
                Required if config_name is not provided.
        """
        self._control_plane_url = (
            control_plane_url
            or os.getenv("CONTROL_PLANE_URL", "https://app.mysql-to-sheets.com")
        ).rstrip("/")

        self._link_token = link_token or os.getenv("LINK_TOKEN", "")
        self._config_name = config_name or os.getenv("AGENT_CONFIG_NAME")
        self._config_id_value = config_id

        # Parse config ID from env if not provided
        if self._config_id_value is None:
            config_id_str = os.getenv("AGENT_CONFIG_ID")
            if config_id_str:
                try:
                    self._config_id_value = int(config_id_str)
                except ValueError:
                    logger.warning(f"Invalid AGENT_CONFIG_ID: {config_id_str}")

        # Cached config
        self._cached_config: "Config | None" = None
        self._cached_etag: str | None = None

        # Organization ID from token (set after first fetch)
        self._organization_id: int | None = None

    @property
    def provider_type(self) -> str:
        """Get the provider type identifier."""
        return "link"

    @property
    def tenant_id(self) -> int | None:
        """Get the organization ID from the link token."""
        return self._organization_id

    @property
    def config_id(self) -> int | None:
        """Get the sync config ID if specified."""
        return self._config_id_value

    @property
    def control_plane_url(self) -> str:
        """Get the control plane URL."""
        return self._control_plane_url

    def get_config(self) -> "Config":
        """Get the configuration, using cache if available.

        Returns cached config if available, otherwise fetches from
        control plane and merges with local credentials.

        Returns:
            Config instance ready for sync operations.

        Raises:
            ConfigError: If configuration cannot be loaded.
        """
        if self._cached_config is not None:
            return self._cached_config

        return self.refresh()

    def refresh(self) -> "Config":
        """Reload configuration from control plane.

        Forces a fresh load, bypassing cache. Uses ETag for
        conditional requests when available.

        Returns:
            Freshly loaded Config instance.

        Raises:
            ConfigError: If configuration cannot be loaded.
        """
        from mysql_to_sheets.agent.link_token import (
            LinkTokenStatus,
            validate_link_token,
        )

        # Validate link token
        if not self._link_token:
            raise ConfigError(
                "LINK_TOKEN is required for agent mode",
                missing_fields=["LINK_TOKEN"],
                code="CONFIG_101",
            )

        token_info = validate_link_token(self._link_token)
        if token_info.status != LinkTokenStatus.VALID:
            raise ConfigError(
                f"Invalid LINK_TOKEN: {token_info.error}",
                missing_fields=["LINK_TOKEN"],
                code="CONFIG_102",
            )

        # Extract organization ID from token
        if token_info.organization_id:
            try:
                self._organization_id = int(token_info.organization_id.replace("org_", ""))
            except ValueError:
                self._organization_id = None

        # Fetch remote config
        remote_config = self._fetch_remote_config()

        # Merge with local credentials
        config = self._merge_with_local(remote_config)

        # Cache the result
        self._cached_config = config

        return config

    def _fetch_remote_config(self) -> dict[str, Any]:
        """Fetch sync configuration from control plane.

        Returns:
            Dictionary with remote config fields.

        Raises:
            ConfigError: If fetch fails.
        """
        import json
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen

        # Build URL
        if self._config_id_value:
            url = f"{self._control_plane_url}/api/agent/configs/{self._config_id_value}"
        elif self._config_name:
            url = f"{self._control_plane_url}/api/agent/configs?name={self._config_name}"
        else:
            url = f"{self._control_plane_url}/api/agent/configs"

        logger.debug(f"Fetching config from {url}")

        # Build request with auth header
        headers = {
            "Authorization": f"Bearer {self._link_token}",
            "Accept": "application/json",
            "User-Agent": "mysql-to-sheets-agent/1.0",
        }

        # Add ETag for conditional request
        if self._cached_etag:
            headers["If-None-Match"] = self._cached_etag

        try:
            request = Request(url, headers=headers)
            response = urlopen(request, timeout=30)

            # Store ETag for future requests
            etag = response.headers.get("ETag")
            if etag:
                self._cached_etag = etag

            data = json.loads(response.read().decode("utf-8"))

            # Handle list response (get first config)
            if isinstance(data, list):
                if not data:
                    raise ConfigError(
                        "No sync configurations found",
                        code="CONFIG_103",
                    )
                data = data[0]

            logger.info(f"Fetched config: {data.get('name', 'unnamed')}")
            return data

        except HTTPError as e:
            if e.code == 304:
                # Not modified, return cached data marker
                logger.debug("Config not modified (304)")
                return {"_not_modified": True}
            elif e.code == 401:
                raise ConfigError(
                    "LINK_TOKEN rejected by control plane",
                    missing_fields=["LINK_TOKEN"],
                    code="CONFIG_102",
                ) from e
            elif e.code == 404:
                raise ConfigError(
                    f"Sync config not found: {self._config_name or self._config_id_value}",
                    code="CONFIG_103",
                ) from e
            else:
                raise ConfigError(
                    f"Failed to fetch config from control plane: HTTP {e.code}",
                    code="CONFIG_103",
                ) from e
        except URLError as e:
            raise ConfigError(
                f"Cannot connect to control plane: {e.reason}",
                code="CONFIG_103",
            ) from e
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"Invalid response from control plane: {e}",
                code="CONFIG_103",
            ) from e

    def _merge_with_local(self, remote_config: dict[str, Any]) -> "Config":
        """Merge remote config with local credentials.

        Remote config provides:
        - sql_query
        - google_sheet_id
        - google_worksheet_name
        - column_mapping
        - sync_mode
        - chunk_size

        Local environment provides:
        - Database credentials (DB_HOST, DB_USER, DB_PASSWORD, etc.)
        - Service account file path
        - Other local settings

        Args:
            remote_config: Configuration from control plane.

        Returns:
            Merged Config object.
        """
        from mysql_to_sheets.core.config import get_config

        # Handle not-modified response
        if remote_config.get("_not_modified") and self._cached_config:
            return self._cached_config

        # Start with base config from environment
        base_config = get_config()

        # Build overrides from remote config
        overrides: dict[str, Any] = {}

        # Map remote config fields to Config attributes
        field_mapping = {
            "sql_query": "sql_query",
            "query": "sql_query",
            "sheet_id": "google_sheet_id",
            "google_sheet_id": "google_sheet_id",
            "worksheet_name": "google_worksheet_name",
            "google_worksheet_name": "google_worksheet_name",
            "sync_mode": "sync_mode",
            "mode": "sync_mode",
            "chunk_size": "sync_chunk_size",
            "sync_chunk_size": "sync_chunk_size",
        }

        for remote_key, config_key in field_mapping.items():
            if remote_key in remote_config and remote_config[remote_key]:
                overrides[config_key] = remote_config[remote_key]

        # Handle column mapping
        column_map = remote_config.get("column_map") or remote_config.get("column_mapping")
        if column_map:
            if isinstance(column_map, str):
                import json
                try:
                    column_map = json.loads(column_map)
                except json.JSONDecodeError:
                    pass
            if isinstance(column_map, dict):
                overrides["column_mapping_enabled"] = True
                overrides["column_mapping"] = column_map

        # Handle column order
        columns = remote_config.get("columns") or remote_config.get("column_order")
        if columns:
            if isinstance(columns, str):
                columns = [c.strip() for c in columns.split(",")]
            if isinstance(columns, list):
                overrides["column_order"] = columns

        # Apply overrides
        if overrides:
            logger.debug(f"Applying remote config overrides: {list(overrides.keys())}")
            return base_config.with_overrides(**overrides)

        return base_config

    def invalidate_cache(self) -> None:
        """Invalidate the cached configuration.

        Forces the next get_config() call to fetch fresh data
        from the control plane.
        """
        self._cached_config = None
        self._cached_etag = None
        logger.debug("Config cache invalidated")
