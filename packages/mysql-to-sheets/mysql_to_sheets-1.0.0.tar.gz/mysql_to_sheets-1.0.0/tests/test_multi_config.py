"""Tests for the multi-config module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mysql_to_sheets.core.multi_config import (
    ENV_VAR_PATTERN,
    DatabaseConfig,
    MultiSyncConfig,
    create_example_config,
    export_configs_to_file,
    load_config_file,
    merge_configs,
    save_config_file,
    substitute_env_vars,
    validate_config_file,
)
from mysql_to_sheets.models.sync_configs import SyncConfigDefinition


class TestDatabaseConfig:
    """Tests for DatabaseConfig dataclass."""

    def test_create_default(self):
        """Test creating DatabaseConfig with defaults."""
        config = DatabaseConfig()

        assert config.host == "localhost"
        assert config.port == 3306
        assert config.user == ""
        assert config.password == ""
        assert config.name == ""
        assert config.db_type == "mysql"

    def test_create_custom(self):
        """Test creating DatabaseConfig with custom values."""
        config = DatabaseConfig(
            host="db.example.com",
            port=5432,
            user="admin",
            password="secret",
            name="mydb",
            db_type="postgres",
        )

        assert config.host == "db.example.com"
        assert config.port == 5432
        assert config.db_type == "postgres"

    def test_to_dict(self):
        """Test converting DatabaseConfig to dictionary."""
        config = DatabaseConfig(
            host="localhost",
            port=3306,
            user="root",
            password="pass",
            name="test",
        )

        d = config.to_dict()

        assert d["host"] == "localhost"
        assert d["port"] == 3306
        assert d["user"] == "root"
        assert d["password"] == "pass"
        assert d["name"] == "test"

    def test_from_dict(self):
        """Test creating DatabaseConfig from dictionary."""
        data = {
            "host": "server",
            "port": 5432,
            "user": "postgres",
            "db_type": "postgres",
        }

        config = DatabaseConfig.from_dict(data)

        assert config.host == "server"
        assert config.port == 5432
        assert config.db_type == "postgres"


class TestSubstituteEnvVars:
    """Tests for environment variable substitution."""

    def test_env_var_pattern(self):
        """Test the regex pattern for env vars."""
        # Basic variable
        match = ENV_VAR_PATTERN.search("${VAR_NAME}")
        assert match is not None
        assert match.group(1) == "VAR_NAME"
        assert match.group(2) is None

        # Variable with default
        match = ENV_VAR_PATTERN.search("${VAR:-default}")
        assert match is not None
        assert match.group(1) == "VAR"
        assert match.group(2) == "default"

    def test_substitute_string_with_env_var(self):
        """Test substituting env vars in a string."""
        env_vars = {"DB_HOST": "production-server"}

        with patch.dict(os.environ, env_vars, clear=False):
            result = substitute_env_vars("host: ${DB_HOST}")

        assert result == "host: production-server"

    def test_substitute_string_with_default(self):
        """Test substituting with default value."""
        # Make sure the var is not set
        env_vars = {}

        with patch.dict(os.environ, env_vars, clear=True):
            result = substitute_env_vars("host: ${DB_HOST:-localhost}")

        assert result == "host: localhost"

    def test_substitute_uses_env_over_default(self):
        """Test that env value is used over default."""
        env_vars = {"DB_HOST": "actual-host"}

        with patch.dict(os.environ, env_vars, clear=False):
            result = substitute_env_vars("${DB_HOST:-default-host}")

        assert result == "actual-host"

    def test_substitute_missing_env_no_default(self):
        """Test missing env var without default becomes empty."""
        with patch.dict(os.environ, {}, clear=True):
            result = substitute_env_vars("host: ${MISSING_VAR}")

        assert result == "host: "

    def test_substitute_dict(self):
        """Test substituting env vars in a dictionary."""
        env_vars = {"DB_USER": "admin", "DB_PASS": "secret"}

        with patch.dict(os.environ, env_vars, clear=False):
            data = {
                "user": "${DB_USER}",
                "password": "${DB_PASS}",
            }
            result = substitute_env_vars(data)

        assert result["user"] == "admin"
        assert result["password"] == "secret"

    def test_substitute_list(self):
        """Test substituting env vars in a list."""
        env_vars = {"VAR1": "value1", "VAR2": "value2"}

        with patch.dict(os.environ, env_vars, clear=False):
            data = ["${VAR1}", "${VAR2}"]
            result = substitute_env_vars(data)

        assert result == ["value1", "value2"]

    def test_substitute_nested(self):
        """Test substituting env vars in nested structures."""
        env_vars = {"HOST": "server", "PORT": "5432"}

        with patch.dict(os.environ, env_vars, clear=False):
            data = {
                "database": {
                    "host": "${HOST}",
                    "port": "${PORT}",
                }
            }
            result = substitute_env_vars(data)

        assert result["database"]["host"] == "server"
        assert result["database"]["port"] == "5432"

    def test_substitute_non_string(self):
        """Test that non-strings are returned unchanged."""
        assert substitute_env_vars(123) == 123
        assert substitute_env_vars(True) is True
        assert substitute_env_vars(None) is None


class TestMultiSyncConfig:
    """Tests for MultiSyncConfig dataclass."""

    def test_create_empty(self):
        """Test creating empty MultiSyncConfig."""
        config = MultiSyncConfig(
            database=DatabaseConfig(),
            syncs=[],
        )

        assert config.version == "1.0"
        assert len(config.syncs) == 0

    def test_create_with_syncs(self):
        """Test creating MultiSyncConfig with sync definitions."""
        sync = SyncConfigDefinition(
            name="test-sync",
            sql_query="SELECT * FROM users",
            sheet_id="sheet123",
            organization_id=1,
        )

        config = MultiSyncConfig(
            database=DatabaseConfig(user="root", name="test"),
            syncs=[sync],
        )

        assert len(config.syncs) == 1
        assert config.syncs[0].name == "test-sync"

    def test_to_dict(self):
        """Test converting MultiSyncConfig to dictionary."""
        sync = SyncConfigDefinition(
            name="sync1",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=1,
        )

        config = MultiSyncConfig(
            database=DatabaseConfig(host="localhost"),
            syncs=[sync],
            version="2.0",
        )

        d = config.to_dict()

        assert d["version"] == "2.0"
        assert d["database"]["host"] == "localhost"
        assert len(d["syncs"]) == 1

    def test_validate_valid(self):
        """Test validation of valid config."""
        sync = SyncConfigDefinition(
            name="valid-sync",
            sql_query="SELECT * FROM data",
            sheet_id="sheet123",
            organization_id=1,
        )

        config = MultiSyncConfig(
            database=DatabaseConfig(user="admin", name="db"),
            syncs=[sync],
        )

        errors = config.validate()
        assert len(errors) == 0

    def test_validate_missing_db_user(self):
        """Test validation catches missing database user."""
        config = MultiSyncConfig(
            database=DatabaseConfig(name="db"),
            syncs=[],
        )

        errors = config.validate()
        assert any("user" in e.lower() for e in errors)

    def test_validate_missing_db_name(self):
        """Test validation catches missing database name."""
        config = MultiSyncConfig(
            database=DatabaseConfig(user="admin"),
            syncs=[],
        )

        errors = config.validate()
        assert any("name" in e.lower() for e in errors)

    def test_validate_duplicate_sync_names(self):
        """Test validation catches duplicate sync names."""
        sync1 = SyncConfigDefinition(
            name="same-name",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=1,
        )
        sync2 = SyncConfigDefinition(
            name="same-name",
            sql_query="SELECT 2",
            sheet_id="sheet2",
            organization_id=1,
        )

        config = MultiSyncConfig(
            database=DatabaseConfig(user="admin", name="db"),
            syncs=[sync1, sync2],
        )

        errors = config.validate()
        assert any("duplicate" in e.lower() for e in errors)


class TestLoadConfigFile:
    """Tests for load_config_file function."""

    def test_load_yaml_file(self):
        """Test loading a YAML config file."""
        yaml_content = """
version: "1.0"
database:
  host: localhost
  port: 3306
  user: root
  password: password
  name: testdb
syncs:
  - name: test-sync
    sql_query: SELECT * FROM users
    sheet_id: sheet123
    worksheet_name: Sheet1
"""
        with tempfile.NamedTemporaryFile(
            suffix=".yaml",
            mode="w",
            delete=False,
        ) as f:
            f.write(yaml_content)
            path = f.name

        try:
            config = load_config_file(path)

            assert config.version == "1.0"
            assert config.database.host == "localhost"
            assert config.database.user == "root"
            assert len(config.syncs) == 1
            assert config.syncs[0].name == "test-sync"
        finally:
            os.unlink(path)

    def test_load_json_file(self):
        """Test loading a JSON config file."""
        json_content = """{
  "version": "1.0",
  "database": {
    "host": "localhost",
    "user": "admin",
    "name": "db"
  },
  "syncs": [
    {
      "name": "json-sync",
      "sql_query": "SELECT 1",
      "sheet_id": "sheet456"
    }
  ]
}"""
        with tempfile.NamedTemporaryFile(
            suffix=".json",
            mode="w",
            delete=False,
        ) as f:
            f.write(json_content)
            path = f.name

        try:
            config = load_config_file(path)

            assert config.database.host == "localhost"
            assert len(config.syncs) == 1
            assert config.syncs[0].name == "json-sync"
        finally:
            os.unlink(path)

    def test_load_with_env_substitution(self):
        """Test that env vars are substituted when loading."""
        yaml_content = """
database:
  host: ${TEST_DB_HOST:-fallback}
  user: ${TEST_DB_USER}
  name: test
syncs: []
"""
        env_vars = {
            "TEST_DB_HOST": "env-host",
            "TEST_DB_USER": "env-user",
        }

        with tempfile.NamedTemporaryFile(
            suffix=".yaml",
            mode="w",
            delete=False,
        ) as f:
            f.write(yaml_content)
            path = f.name

        try:
            with patch.dict(os.environ, env_vars, clear=False):
                config = load_config_file(path)

            assert config.database.host == "env-host"
            assert config.database.user == "env-user"
        finally:
            os.unlink(path)

    def test_load_file_not_found(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_config_file("/nonexistent/path.yaml")

    def test_load_unsupported_format(self):
        """Test loading unsupported format raises error."""
        with tempfile.NamedTemporaryFile(
            suffix=".txt",
            mode="w",
            delete=False,
        ) as f:
            f.write("content")
            path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                load_config_file(path)

            assert "Unsupported file format" in str(exc_info.value)
        finally:
            os.unlink(path)

    def test_load_normalizes_query_field(self):
        """Test that 'query' is normalized to 'sql_query'."""
        yaml_content = """
database:
  user: root
  name: db
syncs:
  - name: test
    query: SELECT 1
    sheet_id: sheet123
"""
        with tempfile.NamedTemporaryFile(
            suffix=".yaml",
            mode="w",
            delete=False,
        ) as f:
            f.write(yaml_content)
            path = f.name

        try:
            config = load_config_file(path)
            assert config.syncs[0].sql_query == "SELECT 1"
        finally:
            os.unlink(path)


class TestSaveConfigFile:
    """Tests for save_config_file function."""

    def test_save_yaml(self):
        """Test saving config as YAML."""
        sync = SyncConfigDefinition(
            name="save-test",
            sql_query="SELECT * FROM data",
            sheet_id="sheet123",
            organization_id=1,
        )

        config = MultiSyncConfig(
            database=DatabaseConfig(host="localhost", user="root", name="db"),
            syncs=[sync],
        )

        with tempfile.NamedTemporaryFile(
            suffix=".yaml",
            delete=False,
        ) as f:
            path = f.name

        try:
            save_config_file(config, path, format="yaml")

            content = Path(path).read_text()
            assert "save-test" in content
            assert "localhost" in content
        finally:
            os.unlink(path)

    def test_save_json(self):
        """Test saving config as JSON."""
        sync = SyncConfigDefinition(
            name="json-test",
            sql_query="SELECT 1",
            sheet_id="sheet456",
            organization_id=1,
        )

        config = MultiSyncConfig(
            database=DatabaseConfig(user="admin", name="testdb"),
            syncs=[sync],
        )

        with tempfile.NamedTemporaryFile(
            suffix=".json",
            delete=False,
        ) as f:
            path = f.name

        try:
            save_config_file(config, path, format="json")

            content = Path(path).read_text()
            assert "json-test" in content
            assert '"name":' in content  # JSON format
        finally:
            os.unlink(path)

    def test_save_invalid_format(self):
        """Test saving with invalid format raises error."""
        config = MultiSyncConfig(
            database=DatabaseConfig(),
            syncs=[],
        )

        with pytest.raises(ValueError) as exc_info:
            save_config_file(config, "/tmp/test.txt", format="xml")

        assert "Invalid format" in str(exc_info.value)


class TestExportConfigsToFile:
    """Tests for export_configs_to_file function."""

    def test_export_configs(self):
        """Test exporting configs to file."""
        syncs = [
            SyncConfigDefinition(
                name="export1",
                sql_query="SELECT 1",
                sheet_id="sheet1",
                organization_id=1,
            ),
            SyncConfigDefinition(
                name="export2",
                sql_query="SELECT 2",
                sheet_id="sheet2",
                organization_id=1,
            ),
        ]

        with tempfile.NamedTemporaryFile(
            suffix=".yaml",
            delete=False,
        ) as f:
            path = f.name

        try:
            export_configs_to_file(syncs, path)

            content = Path(path).read_text()
            assert "export1" in content
            assert "export2" in content
        finally:
            os.unlink(path)


class TestCreateExampleConfig:
    """Tests for create_example_config function."""

    def test_create_example(self):
        """Test creating example config."""
        config = create_example_config()

        assert config.database is not None
        assert len(config.syncs) >= 1

        # Should have env var placeholders
        assert "${" in config.database.user or "${" in config.database.password


class TestValidateConfigFile:
    """Tests for validate_config_file function."""

    def test_validate_valid_file(self):
        """Test validating a valid config file."""
        yaml_content = """
database:
  user: root
  name: testdb
syncs:
  - name: valid
    sql_query: SELECT 1
    sheet_id: sheet123
"""
        with tempfile.NamedTemporaryFile(
            suffix=".yaml",
            mode="w",
            delete=False,
        ) as f:
            f.write(yaml_content)
            path = f.name

        try:
            is_valid, errors = validate_config_file(path)

            assert is_valid is True
            assert len(errors) == 0
        finally:
            os.unlink(path)

    def test_validate_invalid_file(self):
        """Test validating an invalid config file."""
        yaml_content = """
database:
  host: localhost
syncs:
  - name: invalid
    sheet_id: sheet123
"""  # Missing sql_query
        with tempfile.NamedTemporaryFile(
            suffix=".yaml",
            mode="w",
            delete=False,
        ) as f:
            f.write(yaml_content)
            path = f.name

        try:
            is_valid, errors = validate_config_file(path)

            assert is_valid is False
            assert len(errors) > 0
        finally:
            os.unlink(path)


class TestMergeConfigs:
    """Tests for merge_configs function."""

    def test_merge_two_configs(self):
        """Test merging two configs."""
        config1 = MultiSyncConfig(
            database=DatabaseConfig(host="host1", user="user1", name="db1"),
            syncs=[
                SyncConfigDefinition(
                    name="sync1",
                    sql_query="SELECT 1",
                    sheet_id="sheet1",
                    organization_id=1,
                ),
            ],
        )

        config2 = MultiSyncConfig(
            database=DatabaseConfig(host="host2", user="user2", name="db2"),
            syncs=[
                SyncConfigDefinition(
                    name="sync2",
                    sql_query="SELECT 2",
                    sheet_id="sheet2",
                    organization_id=1,
                ),
            ],
        )

        merged = merge_configs(config1, config2)

        # Uses database from first config
        assert merged.database.host == "host1"

        # Contains syncs from both
        assert len(merged.syncs) == 2
        sync_names = [s.name for s in merged.syncs]
        assert "sync1" in sync_names
        assert "sync2" in sync_names

    def test_merge_deduplicates_by_name(self):
        """Test that merge deduplicates syncs by name."""
        config1 = MultiSyncConfig(
            database=DatabaseConfig(user="u", name="db"),
            syncs=[
                SyncConfigDefinition(
                    name="duplicate",
                    sql_query="SELECT 1",
                    sheet_id="sheet1",
                    organization_id=1,
                ),
            ],
        )

        config2 = MultiSyncConfig(
            database=DatabaseConfig(user="u", name="db"),
            syncs=[
                SyncConfigDefinition(
                    name="duplicate",  # Same name
                    sql_query="SELECT 2",  # Different query
                    sheet_id="sheet2",
                    organization_id=1,
                ),
            ],
        )

        merged = merge_configs(config1, config2)

        # Only one sync with this name (last wins)
        assert len(merged.syncs) == 1
        assert merged.syncs[0].sql_query == "SELECT 2"

    def test_merge_no_configs_raises(self):
        """Test that merging no configs raises error."""
        with pytest.raises(ValueError) as exc_info:
            merge_configs()

        assert "At least one" in str(exc_info.value)
