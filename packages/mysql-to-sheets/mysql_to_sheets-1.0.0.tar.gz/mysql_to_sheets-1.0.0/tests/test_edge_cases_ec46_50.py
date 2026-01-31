"""Tests for edge cases EC-46 through EC-50.

EC-46: Boolean environment variable parsing
EC-47: SQL subquery validation (queries starting with parentheses)
EC-48: SQLite relative path resolution
EC-49: IPv6 address parsing in DATABASE_URL
EC-50: SSL certificate file validation
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mysql_to_sheets.core.config import (
    Config,
    _parse_bool,
    parse_database_uri,
    reset_config,
    TRUTHY_VALUES,
    FALSY_VALUES,
)
from mysql_to_sheets.core.exceptions import ConfigError
from mysql_to_sheets.core.sync_legacy import validate_query_type


class TestBooleanEnvParsing:
    """Test EC-46: Boolean environment variable parsing.

    Users expect "1", "yes", "on" to work as truthy values, and
    "0", "no", "off" to work as falsy values.
    """

    def test_truthy_values_accepted(self):
        """Verify all truthy values are accepted."""
        truthy_values = ["true", "TRUE", "True", "1", "yes", "YES", "on", "ON", "enabled", "ENABLED"]
        for value in truthy_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                result = _parse_bool("TEST_BOOL", default=False)
                assert result is True, f"Expected True for '{value}'"

    def test_falsy_values_accepted(self):
        """Verify all falsy values are accepted."""
        falsy_values = ["false", "FALSE", "False", "0", "no", "NO", "off", "OFF", "disabled", "DISABLED", ""]
        for value in falsy_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                result = _parse_bool("TEST_BOOL", default=True)
                assert result is False, f"Expected False for '{value}'"

    def test_default_when_not_set(self):
        """Verify default is returned when env var is not set."""
        env = os.environ.copy()
        env.pop("TEST_UNSET_VAR", None)
        with patch.dict(os.environ, env, clear=True):
            assert _parse_bool("TEST_UNSET_VAR", default=True) is True
            assert _parse_bool("TEST_UNSET_VAR", default=False) is False

    def test_invalid_value_raises_config_error(self):
        """Verify invalid boolean value raises ConfigError with CONFIG_123."""
        with patch.dict(os.environ, {"TEST_BOOL": "maybe"}):
            with pytest.raises(ConfigError) as exc_info:
                _parse_bool("TEST_BOOL")
            assert "CONFIG_123" in str(exc_info.value.code)
            assert "maybe" in str(exc_info.value)
            assert "TEST_BOOL" in str(exc_info.value)

    def test_whitespace_stripped(self):
        """Verify whitespace is stripped before comparison."""
        with patch.dict(os.environ, {"TEST_BOOL": "  true  "}):
            assert _parse_bool("TEST_BOOL") is True
        with patch.dict(os.environ, {"TEST_BOOL": "\tfalse\n"}):
            assert _parse_bool("TEST_BOOL") is False

    def test_truthy_falsy_constants_are_frozensets(self):
        """Verify TRUTHY_VALUES and FALSY_VALUES are immutable."""
        assert isinstance(TRUTHY_VALUES, frozenset)
        assert isinstance(FALSY_VALUES, frozenset)

    def test_config_uses_parse_bool_for_db_pool_enabled(self):
        """Verify Config respects boolean parsing for DB_POOL_ENABLED."""
        reset_config()
        env = {
            "DB_USER": "test",
            "DB_PASSWORD": "test",
            "DB_NAME": "test",
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
            "DB_POOL_ENABLED": "1",  # Should be parsed as True
        }
        with patch.dict(os.environ, env, clear=True):
            reset_config()
            config = Config()
            assert config.db_pool_enabled is True


class TestSubqueryValidation:
    """Test EC-47: SQL subquery validation.

    Valid SQL like (SELECT * FROM users) UNION ... should not be
    wrongly flagged as non-SELECT.
    """

    def test_simple_subquery_accepted(self):
        """Verify (SELECT ...) queries are accepted."""
        query = "(SELECT * FROM users)"
        # Should not raise even in strict mode
        validate_query_type(query, strict=True)

    def test_union_with_subqueries_accepted(self):
        """Verify UNION queries with subqueries are accepted."""
        query = "(SELECT id FROM users) UNION (SELECT id FROM admins)"
        validate_query_type(query, strict=True)

    def test_nested_subquery_accepted(self):
        """Verify nested subqueries are accepted."""
        query = "((SELECT * FROM users))"
        validate_query_type(query, strict=True)

    def test_subquery_with_whitespace_accepted(self):
        """Verify subqueries with leading whitespace are accepted."""
        query = "  (  SELECT * FROM users  )"
        validate_query_type(query, strict=True)

    def test_subquery_after_comments_accepted(self):
        """Verify subqueries after SQL comments are accepted."""
        query = "-- Get all users\n(SELECT * FROM users)"
        validate_query_type(query, strict=True)

    def test_cte_with_subquery_accepted(self):
        """Verify CTEs are still accepted."""
        query = "WITH cte AS (SELECT * FROM users) SELECT * FROM cte"
        validate_query_type(query, strict=True)

    def test_non_select_still_rejected(self):
        """Verify non-SELECT queries are still rejected in strict mode."""
        with pytest.raises(ConfigError) as exc_info:
            validate_query_type("DELETE FROM users", strict=True)
        assert "CONFIG_107" in str(exc_info.value.code)

    def test_insert_in_parens_rejected(self):
        """Verify (INSERT ...) is still rejected in strict mode."""
        with pytest.raises(ConfigError) as exc_info:
            validate_query_type("(INSERT INTO users VALUES (1))", strict=True)
        assert "CONFIG_107" in str(exc_info.value.code)


class TestSQLitePathResolution:
    """Test EC-48: SQLite relative path resolution.

    Relative SQLite paths should be resolved to absolute paths and
    a warning should be logged.
    """

    def test_relative_path_resolved_to_absolute(self):
        """Verify relative SQLite paths are resolved to absolute."""
        reset_config()
        env = {
            "DB_TYPE": "sqlite",
            "DB_NAME": "data/test.db",
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
        }
        with patch.dict(os.environ, env, clear=True):
            reset_config()
            config = Config()
            # Path should now be absolute
            assert os.path.isabs(config.db_name)
            assert config.db_name.endswith("data/test.db")

    def test_absolute_path_unchanged(self):
        """Verify absolute SQLite paths remain unchanged."""
        reset_config()
        absolute_path = "/tmp/test_absolute.db"
        env = {
            "DB_TYPE": "sqlite",
            "DB_NAME": absolute_path,
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
        }
        with patch.dict(os.environ, env, clear=True):
            reset_config()
            config = Config()
            assert config.db_name == absolute_path

    def test_memory_database_unchanged(self):
        """Verify :memory: SQLite database is not modified."""
        reset_config()
        env = {
            "DB_TYPE": "sqlite",
            "DB_NAME": ":memory:",
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
        }
        with patch.dict(os.environ, env, clear=True):
            reset_config()
            config = Config()
            assert config.db_name == ":memory:"

    def test_original_path_stored(self):
        """Verify original relative path is stored for logging."""
        reset_config()
        env = {
            "DB_TYPE": "sqlite",
            "DB_NAME": "relative.db",
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
        }
        with patch.dict(os.environ, env, clear=True):
            reset_config()
            config = Config()
            # Original path should be stored in private attribute
            assert hasattr(config, "_sqlite_original_path")
            assert config._sqlite_original_path == "relative.db"

    def test_non_sqlite_paths_unchanged(self):
        """Verify non-SQLite database paths are not modified."""
        reset_config()
        env = {
            "DB_TYPE": "mysql",
            "DB_NAME": "mydb",
            "DB_USER": "test",
            "DB_PASSWORD": "test",
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
        }
        with patch.dict(os.environ, env, clear=True):
            reset_config()
            config = Config()
            assert config.db_name == "mydb"


class TestIPv6DatabaseURL:
    """Test EC-49: IPv6 address parsing in DATABASE_URL.

    IPv6 addresses in brackets like mysql://user:pass@[::1]:3306/db
    should be handled correctly.
    """

    def test_ipv6_localhost_parsed(self):
        """Verify [::1] localhost is parsed correctly."""
        url = "mysql://user:pass@[::1]:3306/testdb"
        result = parse_database_uri(url)
        assert result["db_host"] == "::1"
        assert result["db_port"] == 3306
        assert result["db_user"] == "user"
        assert result["db_password"] == "pass"
        assert result["db_name"] == "testdb"

    def test_full_ipv6_parsed(self):
        """Verify full IPv6 addresses are parsed correctly."""
        url = "postgres://user:pass@[2001:db8::1]:5432/testdb"
        result = parse_database_uri(url)
        assert result["db_host"] == "2001:db8::1"
        assert result["db_port"] == 5432

    def test_ipv6_without_port(self):
        """Verify IPv6 without explicit port uses default."""
        url = "mysql://user:pass@[::1]/testdb"
        result = parse_database_uri(url)
        assert result["db_host"] == "::1"
        assert result["db_port"] == 3306  # Default MySQL port

    def test_ipv6_without_brackets_fails(self):
        """Verify IPv6 without brackets fails clearly."""
        # Raw IPv6 without brackets causes parsing issues
        # This should fail with some error (may vary based on parsing)
        url = "mysql://user:pass@::1:3306/testdb"
        with pytest.raises(ValueError):
            # Should fail because URI is malformed
            parse_database_uri(url)

    def test_password_with_at_and_ipv6(self):
        """Verify password with @ works alongside IPv6."""
        # URL-encoded @ in password
        url = "mysql://user:p%40ss@[::1]:3306/testdb"
        result = parse_database_uri(url)
        assert result["db_password"] == "p@ss"
        assert result["db_host"] == "::1"


class TestSSLCertificateValidation:
    """Test EC-50: SSL certificate file validation.

    DB_SSL_CA pointing to non-existent file should produce a clear
    error during validation, not a cryptic connection timeout.
    """

    def test_missing_ssl_cert_detected(self):
        """Verify missing SSL certificate file is detected."""
        reset_config()
        env = {
            "DB_TYPE": "postgres",
            "DB_USER": "test",
            "DB_PASSWORD": "test",
            "DB_NAME": "test",
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
            "DB_SSL_CA": "/nonexistent/path/to/cert.pem",
        }
        with patch.dict(os.environ, env, clear=True):
            reset_config()
            config = Config()
            errors = config.validate()
            # Should have an error about SSL cert
            ssl_errors = [e for e in errors if "SSL" in e or "ssl" in e]
            assert len(ssl_errors) > 0
            assert "not found" in ssl_errors[0].lower() or "does not exist" in ssl_errors[0].lower()

    def test_ssl_cert_directory_rejected(self):
        """Verify SSL certificate path that is a directory is rejected."""
        reset_config()
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {
                "DB_TYPE": "postgres",
                "DB_USER": "test",
                "DB_PASSWORD": "test",
                "DB_NAME": "test",
                "GOOGLE_SHEET_ID": "test",
                "SQL_QUERY": "SELECT 1",
                "DB_SSL_CA": tmpdir,  # Directory, not file
            }
            with patch.dict(os.environ, env, clear=True):
                reset_config()
                config = Config()
                errors = config.validate()
                ssl_errors = [e for e in errors if "SSL" in e or "ssl" in e]
                assert len(ssl_errors) > 0
                assert "directory" in ssl_errors[0].lower()

    def test_verify_ca_requires_ssl_ca(self):
        """Verify DB_SSL_MODE=verify-ca requires DB_SSL_CA."""
        reset_config()
        env = {
            "DB_TYPE": "postgres",
            "DB_USER": "test",
            "DB_PASSWORD": "test",
            "DB_NAME": "test",
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
            "DB_SSL_MODE": "verify-ca",
            # DB_SSL_CA not set
        }
        with patch.dict(os.environ, env, clear=True):
            reset_config()
            config = Config()
            errors = config.validate()
            ssl_errors = [e for e in errors if "SSL" in e or "ssl" in e.lower()]
            assert len(ssl_errors) > 0
            assert "verify-ca" in ssl_errors[0] or "DB_SSL_CA" in ssl_errors[0]

    def test_verify_full_requires_ssl_ca(self):
        """Verify DB_SSL_MODE=verify-full requires DB_SSL_CA."""
        reset_config()
        env = {
            "DB_TYPE": "postgres",
            "DB_USER": "test",
            "DB_PASSWORD": "test",
            "DB_NAME": "test",
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
            "DB_SSL_MODE": "verify-full",
            # DB_SSL_CA not set
        }
        with patch.dict(os.environ, env, clear=True):
            reset_config()
            config = Config()
            errors = config.validate()
            ssl_errors = [e for e in errors if "SSL" in e or "ssl" in e.lower()]
            assert len(ssl_errors) > 0
            assert "verify-full" in ssl_errors[0] or "DB_SSL_CA" in ssl_errors[0]

    def test_valid_ssl_cert_accepted(self):
        """Verify valid SSL certificate file is accepted."""
        reset_config()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write("-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----\n")
            cert_path = f.name
        try:
            env = {
                "DB_TYPE": "postgres",
                "DB_USER": "test",
                "DB_PASSWORD": "test",
                "DB_NAME": "test",
                "GOOGLE_SHEET_ID": "test",
                "SQL_QUERY": "SELECT 1",
                "DB_SSL_CA": cert_path,
                "DB_SSL_MODE": "verify-ca",
            }
            with patch.dict(os.environ, env, clear=True):
                reset_config()
                config = Config()
                errors = config.validate()
                # Should not have SSL-related errors
                ssl_errors = [e for e in errors if "SSL" in e or "ssl" in e.lower()]
                assert len(ssl_errors) == 0
        finally:
            os.unlink(cert_path)

    def test_tilde_in_ssl_path_expanded(self):
        """Verify tilde (~) in SSL cert path is expanded."""
        reset_config()
        # Create a temp file in a real location
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write("-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----\n")
            cert_path = f.name
        try:
            # Use path with tilde (simulate home directory)
            home = os.path.expanduser("~")
            if cert_path.startswith(home):
                tilde_path = cert_path.replace(home, "~", 1)
            else:
                # Can't test tilde expansion without home directory prefix
                pytest.skip("Temp file not in home directory")

            env = {
                "DB_TYPE": "postgres",
                "DB_USER": "test",
                "DB_PASSWORD": "test",
                "DB_NAME": "test",
                "GOOGLE_SHEET_ID": "test",
                "SQL_QUERY": "SELECT 1",
                "DB_SSL_CA": tilde_path,
            }
            with patch.dict(os.environ, env, clear=True):
                reset_config()
                config = Config()
                errors = config.validate()
                # Should not have errors about missing file
                missing_errors = [e for e in errors if "not found" in e.lower()]
                assert len(missing_errors) == 0
        finally:
            os.unlink(cert_path)
