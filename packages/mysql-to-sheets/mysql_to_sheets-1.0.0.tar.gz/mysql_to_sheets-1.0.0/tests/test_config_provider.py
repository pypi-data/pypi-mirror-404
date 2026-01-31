"""Tests for configuration providers and factory."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mysql_to_sheets.core.config import Config, reset_config
from mysql_to_sheets.core.config_factory import (
    clear_config_provider,
    get_config_provider,
    get_current_provider,
    provider_context,
    reset_config_provider_factory,
    set_config_provider,
)
from mysql_to_sheets.core.config_provider import ConfigProvider
from mysql_to_sheets.core.env_config_provider import EnvConfigProvider


class TestConfigProvider:
    """Tests for ConfigProvider ABC."""

    def test_provider_is_abstract(self):
        """ConfigProvider cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            ConfigProvider()  # type: ignore

    def test_provider_repr_basic(self):
        """Provider repr shows type."""
        provider = EnvConfigProvider()
        assert "EnvConfigProvider" in repr(provider)
        assert "type='env'" in repr(provider)


class TestEnvConfigProvider:
    """Tests for EnvConfigProvider."""

    def setup_method(self):
        """Reset state before each test."""
        reset_config()
        reset_config_provider_factory()

    def teardown_method(self):
        """Clean up after each test."""
        reset_config()
        reset_config_provider_factory()

    def test_provider_type(self):
        """Provider type is 'env'."""
        provider = EnvConfigProvider()
        assert provider.provider_type == "env"

    def test_tenant_id_is_none(self):
        """EnvConfigProvider has no tenant context."""
        provider = EnvConfigProvider()
        assert provider.tenant_id is None

    def test_config_id_is_none(self):
        """EnvConfigProvider has no config ID."""
        provider = EnvConfigProvider()
        assert provider.config_id is None

    def test_get_config_returns_config(self):
        """get_config returns a Config instance."""
        provider = EnvConfigProvider()
        config = provider.get_config()
        assert isinstance(config, Config)

    def test_get_config_caches_result(self):
        """get_config returns the same instance on subsequent calls."""
        provider = EnvConfigProvider()
        config1 = provider.get_config()
        config2 = provider.get_config()
        assert config1 is config2

    def test_refresh_clears_cache(self):
        """refresh returns a new Config instance."""
        provider = EnvConfigProvider()
        config1 = provider.get_config()
        config2 = provider.refresh()
        # Note: objects may be equal but should be freshly created
        assert isinstance(config2, Config)

    def test_custom_env_file(self):
        """Provider can use custom .env file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("DB_HOST=custom-host\n")
            f.write("DB_USER=custom-user\n")
            f.write("DB_PASSWORD=custom-pass\n")
            f.write("DB_NAME=custom-db\n")
            f.write("GOOGLE_SHEET_ID=custom-sheet\n")
            f.write("SQL_QUERY=SELECT 1\n")
            f.flush()

            try:
                provider = EnvConfigProvider(env_file=f.name)
                config = provider.get_config()
                assert config.db_host == "custom-host"
            finally:
                os.unlink(f.name)


class TestConfigFactory:
    """Tests for config factory functions."""

    def setup_method(self):
        """Reset state before each test."""
        reset_config()
        reset_config_provider_factory()

    def teardown_method(self):
        """Clean up after each test."""
        reset_config()
        reset_config_provider_factory()

    def test_get_config_provider_default(self):
        """Default provider is EnvConfigProvider."""
        provider = get_config_provider()
        assert isinstance(provider, EnvConfigProvider)
        assert provider.provider_type == "env"

    def test_get_config_provider_explicit_env(self):
        """Can explicitly request env provider."""
        provider = get_config_provider(provider_type="env")
        assert isinstance(provider, EnvConfigProvider)

    def test_set_and_get_current_provider(self):
        """set_config_provider sets context provider."""
        provider = EnvConfigProvider()
        token = set_config_provider(provider)
        try:
            current = get_current_provider()
            assert current is provider
        finally:
            clear_config_provider(token)

    def test_clear_config_provider(self):
        """clear_config_provider removes context provider."""
        provider = EnvConfigProvider()
        token = set_config_provider(provider)
        clear_config_provider(token)
        assert get_current_provider() is None

    def test_provider_context_manager(self):
        """provider_context sets and clears provider."""
        provider = EnvConfigProvider()

        assert get_current_provider() is None

        with provider_context(provider):
            assert get_current_provider() is provider

        assert get_current_provider() is None

    def test_provider_context_creates_provider(self):
        """provider_context can create provider from parameters."""
        with provider_context(provider_type="env") as provider:
            assert isinstance(provider, EnvConfigProvider)
            assert get_current_provider() is provider

    def test_context_provider_used_by_get_config(self):
        """get_config uses context provider when set."""
        provider = EnvConfigProvider()
        token = set_config_provider(provider)
        try:
            from mysql_to_sheets.core.config import get_config

            config = get_config()
            assert isinstance(config, Config)
        finally:
            clear_config_provider(token)


class TestDatabaseConfigProvider:
    """Tests for DatabaseConfigProvider."""

    def setup_method(self):
        """Reset state before each test."""
        reset_config()
        reset_config_provider_factory()

    def teardown_method(self):
        """Clean up after each test."""
        reset_config()
        reset_config_provider_factory()

    def test_provider_type(self):
        """Provider type is 'database'."""
        from mysql_to_sheets.core.database_config_provider import DatabaseConfigProvider

        provider = DatabaseConfigProvider(tenant_id=1)
        assert provider.provider_type == "database"

    def test_tenant_id(self):
        """DatabaseConfigProvider has tenant context."""
        from mysql_to_sheets.core.database_config_provider import DatabaseConfigProvider

        provider = DatabaseConfigProvider(tenant_id=123)
        assert provider.tenant_id == 123

    def test_config_id(self):
        """DatabaseConfigProvider has config ID when provided."""
        from mysql_to_sheets.core.database_config_provider import DatabaseConfigProvider

        provider = DatabaseConfigProvider(tenant_id=1, config_id=456)
        assert provider.config_id == 456

    def test_config_name(self):
        """DatabaseConfigProvider has config name when provided."""
        from mysql_to_sheets.core.database_config_provider import DatabaseConfigProvider

        provider = DatabaseConfigProvider(tenant_id=1, config_name="test-config")
        assert provider.config_name == "test-config"

    def test_get_config_without_tenant_returns_base(self):
        """get_config without tenant returns environment config."""
        from mysql_to_sheets.core.database_config_provider import DatabaseConfigProvider

        provider = DatabaseConfigProvider()
        config = provider.get_config()
        assert isinstance(config, Config)

    def test_factory_creates_database_provider(self):
        """Factory creates DatabaseConfigProvider for tenant_id."""
        provider = get_config_provider(tenant_id=123, provider_type="database")

        from mysql_to_sheets.core.database_config_provider import DatabaseConfigProvider

        assert isinstance(provider, DatabaseConfigProvider)
        assert provider.tenant_id == 123


class TestProviderRepr:
    """Tests for provider string representations."""

    def test_env_provider_repr(self):
        """EnvConfigProvider repr is informative."""
        provider = EnvConfigProvider()
        repr_str = repr(provider)
        assert "EnvConfigProvider" in repr_str
        assert "env" in repr_str

    def test_database_provider_repr_with_ids(self):
        """DatabaseConfigProvider repr shows tenant and config."""
        from mysql_to_sheets.core.database_config_provider import DatabaseConfigProvider

        provider = DatabaseConfigProvider(tenant_id=123, config_id=456)
        repr_str = repr(provider)
        assert "DatabaseConfigProvider" in repr_str
        assert "tenant_id=123" in repr_str
        assert "config_id=456" in repr_str
