"""Configuration provider factory and context management.

Provides factory functions to get the appropriate config provider
based on context. Supports context-scoped providers for multi-tenant
SaaS deployments.
"""

import logging
import threading
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Iterator

from mysql_to_sheets.core.config_provider import ConfigProvider
from mysql_to_sheets.core.env_config_provider import EnvConfigProvider

if TYPE_CHECKING:
    from mysql_to_sheets.core.config import Config

logger = logging.getLogger(__name__)


# Context variable for current provider
_provider_context: ContextVar[ConfigProvider | None] = ContextVar(
    "config_provider", default=None
)

# Global default provider (thread-safe singleton)
_default_provider: ConfigProvider | None = None
_provider_lock = threading.Lock()


def get_config_provider(
    tenant_id: int | None = None,
    config_id: int | None = None,
    config_name: str | None = None,
    provider_type: str | None = None,
    db_path: str | None = None,
) -> ConfigProvider:
    """Get or create a configuration provider.

    Factory function that returns the appropriate provider based on
    context and parameters. Provider selection order:

    1. Context variable (set via set_config_provider or provider_context)
    2. Explicit parameters (tenant_id, config_id, etc.)
    3. Global default (EnvConfigProvider)

    Args:
        tenant_id: Optional tenant (organization) ID for database provider.
        config_id: Optional sync config ID for config-specific provider.
        config_name: Optional sync config name (alternative to config_id).
        provider_type: Explicit provider type ('env' or 'database').
            Takes precedence over auto-detection.
        db_path: Database path for database provider.

    Returns:
        ConfigProvider instance.

    Raises:
        ValueError: If configuration is invalid or provider cannot be created.

    Examples::

        # Default: uses environment provider
        provider = get_config_provider()

        # Database provider for specific tenant
        provider = get_config_provider(tenant_id=123)

        # Database provider for specific sync config
        provider = get_config_provider(tenant_id=123, config_id=456)
    """
    # Check context first
    ctx_provider = _provider_context.get()
    if ctx_provider is not None:
        return ctx_provider

    # Determine provider type
    resolved_type = _resolve_provider_type(provider_type, tenant_id, config_id)

    if resolved_type == "database":
        return _create_database_provider(
            tenant_id=tenant_id,
            config_id=config_id,
            config_name=config_name,
            db_path=db_path,
        )

    # Default: environment provider
    return _get_default_provider()


def _resolve_provider_type(
    provider_type: str | None,
    tenant_id: int | None,
    config_id: int | None,
) -> str:
    """Resolve the provider type from parameters.

    Args:
        provider_type: Explicit provider type.
        tenant_id: Tenant ID (implies database provider).
        config_id: Config ID (implies database provider).

    Returns:
        Provider type string ('env' or 'database').
    """
    # Explicit type takes precedence
    if provider_type:
        return provider_type.lower()

    # Tenant or config ID implies database provider
    if tenant_id is not None or config_id is not None:
        return "database"

    # Default to environment
    return "env"


def _get_default_provider() -> ConfigProvider:
    """Get or create the default environment provider (singleton).

    Returns:
        EnvConfigProvider instance.
    """
    global _default_provider

    if _default_provider is not None:
        return _default_provider

    with _provider_lock:
        if _default_provider is not None:
            return _default_provider

        _default_provider = EnvConfigProvider()
        logger.debug("Created default environment config provider")
        return _default_provider


def _create_database_provider(
    tenant_id: int | None,
    config_id: int | None,
    config_name: str | None,
    db_path: str | None,
) -> ConfigProvider:
    """Create a database-backed config provider.

    Args:
        tenant_id: Tenant (organization) ID.
        config_id: Optional sync config ID.
        config_name: Optional sync config name.
        db_path: Database path.

    Returns:
        DatabaseConfigProvider instance.
    """
    from mysql_to_sheets.core.database_config_provider import DatabaseConfigProvider

    return DatabaseConfigProvider(
        tenant_id=tenant_id,
        config_id=config_id,
        config_name=config_name,
        db_path=db_path,
    )


def set_config_provider(provider: ConfigProvider) -> Token[ConfigProvider | None]:
    """Set the current config provider for this context.

    Must be called at the start of request handling to scope
    configuration to a specific provider.

    Args:
        provider: The config provider to use for this context.

    Returns:
        A contextvars Token that can be used to reset the value.

    Example::

        provider = DatabaseConfigProvider(tenant_id=123)
        token = set_config_provider(provider)
        try:
            # All get_config_provider() calls return this provider
            config = get_config_provider().get_config()
        finally:
            clear_config_provider(token)
    """
    return _provider_context.set(provider)


def get_current_provider() -> ConfigProvider | None:
    """Get the current context provider, or None if not set."""
    return _provider_context.get()


def clear_config_provider(token: Token[ConfigProvider | None] | None = None) -> None:
    """Clear the current config provider context.

    Args:
        token: Optional token from set_config_provider() to reset to previous value.
    """
    if token is not None:
        _provider_context.reset(token)
    else:
        _provider_context.set(None)


@contextmanager
def provider_context(
    provider: ConfigProvider | None = None,
    *,
    tenant_id: int | None = None,
    config_id: int | None = None,
    config_name: str | None = None,
    provider_type: str | None = None,
    db_path: str | None = None,
) -> Iterator[ConfigProvider]:
    """Context manager for scoped config provider.

    Sets a config provider for the duration of the context block.
    Automatically clears the provider on exit.

    Args:
        provider: Explicit provider to use. If None, creates one from parameters.
        tenant_id: Tenant ID for database provider.
        config_id: Config ID for database provider.
        config_name: Config name for database provider.
        provider_type: Explicit provider type.
        db_path: Database path for database provider.

    Yields:
        The active ConfigProvider for the context.

    Example::

        # Use explicit provider
        provider = DatabaseConfigProvider(tenant_id=123)
        with provider_context(provider):
            config = get_config_provider().get_config()

        # Create provider from parameters
        with provider_context(tenant_id=123, config_id=456) as provider:
            config = provider.get_config()
    """
    if provider is None:
        provider = get_config_provider(
            tenant_id=tenant_id,
            config_id=config_id,
            config_name=config_name,
            provider_type=provider_type,
            db_path=db_path,
        )

    token = set_config_provider(provider)
    try:
        yield provider
    finally:
        clear_config_provider(token)


def reset_config_provider_factory() -> None:
    """Reset the config provider factory state.

    Clears the default provider singleton and context variable.
    Useful for testing and cleanup.
    """
    global _default_provider
    with _provider_lock:
        _default_provider = None
    _provider_context.set(None)


def get_provider_type() -> str | None:
    """Get the current provider type.

    Returns:
        Provider type string or None if no provider is active.
    """
    provider = _provider_context.get()
    if provider is not None:
        return provider.provider_type
    if _default_provider is not None:
        return _default_provider.provider_type
    return None
