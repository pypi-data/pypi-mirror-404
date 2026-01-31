"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest

from mysql_to_sheets.core.config import Config, get_config, reset_config
from mysql_to_sheets.core.exceptions import ConfigError


class TestConfig:
    """Tests for Config dataclass."""

    def setup_method(self):
        """Reset config singleton before each test."""
        reset_config()

    def test_config_defaults(self):
        """Test that Config has sensible defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.db_host == "localhost"
            assert config.db_port == 3306
            assert config.google_worksheet_name == "Sheet1"
            assert config.log_level == "INFO"

    def test_config_from_env(self):
        """Test that Config reads from environment variables."""
        env_vars = {
            "DB_HOST": "testhost",
            "DB_PORT": "3307",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_NAME": "testdb",
            "GOOGLE_SHEET_ID": "test_sheet_id",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            reset_config()
            config = Config()
            assert config.db_host == "testhost"
            assert config.db_port == 3307
            assert config.db_user == "testuser"
            assert config.db_name == "testdb"
            assert config.google_sheet_id == "test_sheet_id"

    def test_config_validate_missing_required(self):
        """Test that validation catches missing required fields."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            errors = config.validate()
            assert "DB_USER is required" in errors
            assert "DB_PASSWORD is required" in errors
            assert "DB_NAME is required" in errors
            assert "GOOGLE_SHEET_ID is required" in errors
            assert "SQL_QUERY is required" in errors

    def test_config_validate_or_raise(self):
        """Test that validate_or_raise raises ConfigError."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            with pytest.raises(ConfigError) as exc_info:
                config.validate_or_raise()
            assert "Invalid configuration" in exc_info.value.message
            assert len(exc_info.value.missing_fields) > 0

    def test_config_is_valid(self):
        """Test is_valid method."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.is_valid() is False

    def test_config_with_overrides(self):
        """Test with_overrides creates new config with changed values."""
        with patch.dict(os.environ, {"DB_HOST": "original"}, clear=True):
            config = Config()
            new_config = config.with_overrides(db_host="overridden", db_port=9999)

            # Original unchanged
            assert config.db_host == "original"
            assert config.db_port == 3306

            # New config has overrides
            assert new_config.db_host == "overridden"
            assert new_config.db_port == 9999

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "db_host": "dicthost",
            "db_port": 3308,
            "google_sheet_id": "dict_sheet_id",
            "unknown_field": "ignored",  # Should be filtered out
        }
        config = Config.from_dict(data)
        assert config.db_host == "dicthost"
        assert config.db_port == 3308
        assert config.google_sheet_id == "dict_sheet_id"

    def test_config_repr_masks_password(self):
        """Test that repr masks the password."""
        with patch.dict(os.environ, {"DB_PASSWORD": "secret123"}, clear=True):
            config = Config()
            repr_str = repr(config)
            assert "secret123" not in repr_str
            assert "***" in repr_str


class TestGetConfig:
    """Tests for get_config singleton function."""

    def setup_method(self):
        """Reset config singleton before each test."""
        reset_config()

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self):
        """Test that reset_config clears the singleton."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        # After reset, should be a different instance
        # (though may have same values)
        assert config1 is not config2
