"""Abstract base class for configuration providers.

Defines the interface that all config providers must implement,
allowing for pluggable configuration sources (environment, database, etc.).

The provider pattern enables:
- Multi-tenant SaaS deployments with database-backed configs
- Backward compatibility with existing .env-based configuration
- Runtime configuration refresh without restart
- Context-aware configuration scoping
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mysql_to_sheets.core.config import Config


class ConfigProvider(ABC):
    """Abstract base class for configuration providers.

    All config providers must implement these methods to provide
    consistent configuration loading semantics.

    Example usage::

        # Using environment provider (default)
        provider = EnvConfigProvider()
        config = provider.get_config()

        # Using database provider for SaaS
        provider = DatabaseConfigProvider(tenant_id=123, config_id=456)
        config = provider.get_config()

        # Refresh config after changes
        config = provider.refresh()
    """

    @abstractmethod
    def get_config(self) -> "Config":
        """Get the current configuration.

        Returns a cached configuration if available, otherwise loads
        from the underlying source.

        Returns:
            Config instance for the current context.

        Raises:
            ConfigError: If configuration is invalid or cannot be loaded.
        """
        pass

    @abstractmethod
    def refresh(self) -> "Config":
        """Reload configuration from the underlying source.

        Forces a fresh load, bypassing any cached values. Useful when
        configuration may have changed (e.g., database update).

        Returns:
            Freshly loaded Config instance.

        Raises:
            ConfigError: If configuration is invalid or cannot be loaded.
        """
        pass

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Get the provider type identifier.

        Returns:
            Provider type string (e.g., 'env', 'database').
        """
        pass

    @property
    def tenant_id(self) -> int | None:
        """Get the tenant (organization) ID for multi-tenant providers.

        Returns:
            Tenant ID if this is a tenant-scoped provider, None otherwise.
        """
        return None

    @property
    def config_id(self) -> int | None:
        """Get the sync config ID if this provider is config-specific.

        Returns:
            Config ID if this provider is for a specific sync config, None otherwise.
        """
        return None

    def __repr__(self) -> str:
        """String representation of the provider."""
        parts = [f"type={self.provider_type!r}"]
        if self.tenant_id is not None:
            parts.append(f"tenant_id={self.tenant_id}")
        if self.config_id is not None:
            parts.append(f"config_id={self.config_id}")
        return f"{self.__class__.__name__}({', '.join(parts)})"
