"""Tests for column mapping module."""

import os
from unittest.mock import patch

from mysql_to_sheets.core.column_mapping import (
    ColumnMappingConfig,
    _apply_case_transform,
    _parse_rename_map,
    _transform_column_name,
    apply_column_mapping,
    get_column_mapping_config,
)


class TestParseRenameMap:
    """Tests for _parse_rename_map function."""

    def test_empty_string(self):
        """Test empty string returns empty dict."""
        assert _parse_rename_map("") == {}
        assert _parse_rename_map("   ") == {}

    def test_json_format(self):
        """Test JSON format parsing."""
        result = _parse_rename_map('{"old_name": "New Name", "col2": "Column 2"}')
        assert result == {"old_name": "New Name", "col2": "Column 2"}

    def test_key_value_format(self):
        """Test key=value format parsing."""
        result = _parse_rename_map("old_name=New Name,col2=Column 2")
        assert result == {"old_name": "New Name", "col2": "Column 2"}

    def test_key_value_with_spaces(self):
        """Test key=value format with spaces."""
        result = _parse_rename_map("old_name = New Name , col2 = Column 2")
        assert result == {"old_name": "New Name", "col2": "Column 2"}

    def test_invalid_json_falls_back_to_key_value(self):
        """Test invalid JSON falls back to key=value parsing."""
        result = _parse_rename_map("{invalid json")
        # Should treat as key=value but won't parse correctly
        assert result == {}


class TestApplyCaseTransform:
    """Tests for _apply_case_transform function."""

    def test_none_transform(self):
        """Test 'none' keeps name unchanged."""
        assert _apply_case_transform("Column_Name", "none") == "Column_Name"

    def test_upper_transform(self):
        """Test 'upper' transforms to uppercase."""
        assert _apply_case_transform("column_name", "upper") == "COLUMN_NAME"

    def test_lower_transform(self):
        """Test 'lower' transforms to lowercase."""
        assert _apply_case_transform("COLUMN_NAME", "lower") == "column_name"

    def test_title_transform(self):
        """Test 'title' transforms to title case."""
        assert _apply_case_transform("column_name", "title") == "Column_Name"


class TestColumnMappingConfig:
    """Tests for ColumnMappingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ColumnMappingConfig()

        assert config.enabled is False
        assert config.rename_map == {}
        assert config.column_order is None
        assert config.case_transform == "none"
        assert config.strip_prefix == ""
        assert config.strip_suffix == ""

    def test_is_active_when_disabled(self):
        """Test is_active returns False when disabled."""
        config = ColumnMappingConfig(enabled=False, rename_map={"a": "b"})
        assert config.is_active() is False

    def test_is_active_with_rename_map(self):
        """Test is_active returns True with rename map."""
        config = ColumnMappingConfig(enabled=True, rename_map={"a": "b"})
        assert config.is_active() is True

    def test_is_active_with_column_order(self):
        """Test is_active returns True with column order."""
        config = ColumnMappingConfig(enabled=True, column_order=["a", "b"])
        assert config.is_active() is True

    def test_is_active_with_case_transform(self):
        """Test is_active returns True with case transform."""
        config = ColumnMappingConfig(enabled=True, case_transform="upper")
        assert config.is_active() is True

    def test_is_active_with_strip_prefix(self):
        """Test is_active returns True with strip prefix."""
        config = ColumnMappingConfig(enabled=True, strip_prefix="tbl_")
        assert config.is_active() is True

    def test_is_active_enabled_but_nothing_configured(self):
        """Test is_active returns False when enabled but nothing configured."""
        config = ColumnMappingConfig(enabled=True)
        assert config.is_active() is False

    @patch.dict(
        os.environ,
        {
            "COLUMN_MAPPING_ENABLED": "true",
            "COLUMN_MAPPING": '{"id": "ID", "name": "Name"}',
            "COLUMN_ORDER": "ID,Name,Email",
            "COLUMN_CASE": "title",
            "COLUMN_STRIP_PREFIX": "tbl_",
            "COLUMN_STRIP_SUFFIX": "_col",
        },
    )
    def test_from_env(self):
        """Test loading config from environment variables."""
        config = ColumnMappingConfig.from_env()

        assert config.enabled is True
        assert config.rename_map == {"id": "ID", "name": "Name"}
        assert config.column_order == ["ID", "Name", "Email"]
        assert config.case_transform == "title"
        assert config.strip_prefix == "tbl_"
        assert config.strip_suffix == "_col"


class TestTransformColumnName:
    """Tests for _transform_column_name function."""

    def test_no_transformation(self):
        """Test with no transformations."""
        config = ColumnMappingConfig(enabled=True)
        result = _transform_column_name("column_name", config)
        assert result == "column_name"

    def test_strip_prefix(self):
        """Test stripping prefix."""
        config = ColumnMappingConfig(enabled=True, strip_prefix="tbl_")
        result = _transform_column_name("tbl_users", config)
        assert result == "users"

    def test_strip_suffix(self):
        """Test stripping suffix."""
        config = ColumnMappingConfig(enabled=True, strip_suffix="_id")
        result = _transform_column_name("user_id", config)
        assert result == "user"

    def test_rename_after_strip(self):
        """Test renaming after stripping."""
        config = ColumnMappingConfig(
            enabled=True,
            strip_prefix="tbl_",
            rename_map={"users": "User Table"},
        )
        result = _transform_column_name("tbl_users", config)
        assert result == "User Table"

    def test_rename_original_name(self):
        """Test renaming using original name."""
        config = ColumnMappingConfig(
            enabled=True,
            rename_map={"tbl_users": "Users"},
        )
        result = _transform_column_name("tbl_users", config)
        assert result == "Users"

    def test_case_transform_after_rename(self):
        """Test case transform is applied after rename."""
        config = ColumnMappingConfig(
            enabled=True,
            rename_map={"id": "user id"},
            case_transform="title",
        )
        result = _transform_column_name("id", config)
        assert result == "User Id"


class TestApplyColumnMapping:
    """Tests for apply_column_mapping function."""

    def test_inactive_config_returns_unchanged(self):
        """Test that inactive config returns data unchanged."""
        config = ColumnMappingConfig(enabled=False, rename_map={"a": "b"})
        headers = ["a", "b", "c"]
        rows = [[1, 2, 3]]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        assert new_headers == headers
        assert new_rows == rows

    def test_rename_columns(self):
        """Test column renaming."""
        config = ColumnMappingConfig(
            enabled=True,
            rename_map={"cust_id": "Customer ID", "txn_dt": "Transaction Date"},
        )
        headers = ["cust_id", "txn_dt", "amount"]
        rows = [[1, "2024-01-15", 100.0]]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        assert new_headers == ["Customer ID", "Transaction Date", "amount"]
        assert new_rows == [[1, "2024-01-15", 100.0]]

    def test_column_order_filter(self):
        """Test column filtering with column_order."""
        config = ColumnMappingConfig(
            enabled=True,
            column_order=["name", "email"],
        )
        headers = ["id", "name", "email", "age"]
        rows = [[1, "Alice", "alice@example.com", 30]]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        assert new_headers == ["name", "email"]
        assert new_rows == [["Alice", "alice@example.com"]]

    def test_column_order_reorder(self):
        """Test column reordering."""
        config = ColumnMappingConfig(
            enabled=True,
            column_order=["email", "name", "id"],
        )
        headers = ["id", "name", "email"]
        rows = [[1, "Alice", "alice@example.com"]]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        assert new_headers == ["email", "name", "id"]
        assert new_rows == [["alice@example.com", "Alice", 1]]

    def test_column_order_with_renamed_columns(self):
        """Test column order uses renamed column names."""
        config = ColumnMappingConfig(
            enabled=True,
            rename_map={"cust_id": "Customer ID"},
            column_order=["Customer ID", "name"],
        )
        headers = ["cust_id", "name", "email"]
        rows = [[1, "Alice", "alice@example.com"]]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        assert new_headers == ["Customer ID", "name"]
        assert new_rows == [[1, "Alice"]]

    def test_column_order_missing_column_skipped(self):
        """Test missing columns in column_order are skipped."""
        config = ColumnMappingConfig(
            enabled=True,
            column_order=["name", "nonexistent", "email"],
        )
        headers = ["id", "name", "email"]
        rows = [[1, "Alice", "alice@example.com"]]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        # Only existing columns are included
        assert new_headers == ["name", "email"]
        assert new_rows == [["Alice", "alice@example.com"]]

    def test_case_transform_all_columns(self):
        """Test case transformation on all columns."""
        config = ColumnMappingConfig(
            enabled=True,
            case_transform="upper",
        )
        headers = ["customer_id", "name", "email"]
        rows = [[1, "Alice", "alice@example.com"]]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        assert new_headers == ["CUSTOMER_ID", "NAME", "EMAIL"]

    def test_multiple_rows(self):
        """Test with multiple rows."""
        config = ColumnMappingConfig(
            enabled=True,
            column_order=["name", "id"],
        )
        headers = ["id", "name", "email"]
        rows = [
            [1, "Alice", "alice@example.com"],
            [2, "Bob", "bob@example.com"],
            [3, "Charlie", "charlie@example.com"],
        ]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        assert new_headers == ["name", "id"]
        assert new_rows == [
            ["Alice", 1],
            ["Bob", 2],
            ["Charlie", 3],
        ]

    def test_combined_transformations(self):
        """Test combining multiple transformations."""
        config = ColumnMappingConfig(
            enabled=True,
            strip_prefix="tbl_",
            rename_map={"users": "User"},
            case_transform="title",
            column_order=["User", "Email"],
        )
        headers = ["tbl_users", "tbl_email", "tbl_age"]
        rows = [[1, "alice@example.com", 30]]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        assert new_headers == ["User", "Email"]
        assert new_rows == [[1, "alice@example.com"]]


class TestGetColumnMappingConfig:
    """Tests for get_column_mapping_config function."""

    def test_with_string_rename_map(self):
        """Test creating config with string rename map."""
        config = get_column_mapping_config(
            enabled=True,
            rename_map="id=ID,name=Name",
        )

        assert config.enabled is True
        assert config.rename_map == {"id": "ID", "name": "Name"}

    def test_with_dict_rename_map(self):
        """Test creating config with dict rename map."""
        config = get_column_mapping_config(
            enabled=True,
            rename_map={"id": "ID", "name": "Name"},
        )

        assert config.rename_map == {"id": "ID", "name": "Name"}

    def test_with_string_column_order(self):
        """Test creating config with string column order."""
        config = get_column_mapping_config(
            enabled=True,
            column_order="ID, Name, Email",
        )

        assert config.column_order == ["ID", "Name", "Email"]

    def test_with_list_column_order(self):
        """Test creating config with list column order."""
        config = get_column_mapping_config(
            enabled=True,
            column_order=["ID", "Name", "Email"],
        )

        assert config.column_order == ["ID", "Name", "Email"]

    @patch.dict(os.environ, {"COLUMN_MAPPING_ENABLED": "true"}, clear=True)
    def test_overrides_env_values(self):
        """Test that explicit values override env values."""
        config = get_column_mapping_config(
            enabled=False,  # Override env
        )

        assert config.enabled is False
