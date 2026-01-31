"""Tests for database type converters."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from mysql_to_sheets.core.database.type_converters import (
    clean_row,
    clean_rows,
    clean_value,
    get_converter,
    register_converter,
)


class TestCleanValue:
    """Tests for clean_value function."""

    def test_none_to_empty_string(self):
        """Test None converts to empty string."""
        assert clean_value(None) == ""

    def test_decimal_to_float(self):
        """Test Decimal converts to float."""
        result = clean_value(Decimal("123.45"))
        assert result == 123.45
        assert isinstance(result, float)

    def test_datetime_to_string(self):
        """Test datetime converts to string format."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = clean_value(dt)
        assert result == "2024-01-15 10:30:45"

    def test_date_to_string(self):
        """Test date converts to string format."""
        d = date(2024, 1, 15)
        result = clean_value(d)
        assert result == "2024-01-15"

    def test_bytes_to_string(self):
        """Test bytes converts to UTF-8 string."""
        result = clean_value(b"hello world")
        assert result == "hello world"

    def test_bytes_with_invalid_utf8(self):
        """Test bytes with invalid UTF-8 uses replace mode."""
        result = clean_value(b"\xff\xfe")
        assert isinstance(result, str)

    def test_dict_to_string(self):
        """Test dict converts to string."""
        result = clean_value({"key": "value"})
        assert "key" in result
        assert "value" in result

    def test_list_to_string(self):
        """Test list converts to string."""
        result = clean_value([1, 2, 3])
        assert "[1, 2, 3]" in result

    def test_uuid_to_string(self):
        """Test UUID converts to string."""
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        result = clean_value(uuid)
        assert result == "12345678-1234-5678-1234-567812345678"

    def test_int_unchanged(self):
        """Test int remains unchanged."""
        assert clean_value(42) == 42

    def test_float_unchanged(self):
        """Test float remains unchanged."""
        assert clean_value(3.14) == 3.14

    def test_string_unchanged(self):
        """Test string remains unchanged."""
        assert clean_value("hello") == "hello"

    def test_bool_unchanged(self):
        """Test bool remains unchanged."""
        assert clean_value(True) is True
        assert clean_value(False) is False


class TestCleanValuePostgres:
    """Tests for PostgreSQL-specific type conversions."""

    def test_tuple_array(self):
        """Test PostgreSQL array (tuple) conversion."""
        # psycopg2 returns arrays as tuples
        # Output is now comma-separated: "1, 2, 3" instead of "[1, 2, 3]"
        result = clean_value((1, 2, 3), db_type="postgres")
        assert result == "1, 2, 3"

    def test_list_array(self):
        """Test PostgreSQL array (list) conversion."""
        # Output is now comma-separated: "1, 2, 3" instead of "[1, 2, 3]"
        result = clean_value([1, 2, 3], db_type="postgres")
        assert result == "1, 2, 3"

    def test_nested_array(self):
        """Test nested PostgreSQL array conversion."""
        result = clean_value(([1, 2], [3, 4]), db_type="postgres")
        assert isinstance(result, str)
        # Nested arrays produce comma-separated inner arrays
        assert "1, 2" in result

    def test_json_dict(self):
        """Test PostgreSQL JSON/JSONB dict conversion."""
        result = clean_value({"name": "Alice", "age": 30}, db_type="postgres")
        # Should be JSON string
        assert '"name"' in result
        assert '"Alice"' in result


class TestCleanRow:
    """Tests for clean_row function."""

    def test_clean_row(self):
        """Test cleaning a row of values."""
        row = [1, None, Decimal("10.5"), datetime(2024, 1, 15, 0, 0, 0)]
        result = clean_row(row)

        assert result[0] == 1
        assert result[1] == ""
        assert result[2] == 10.5
        assert result[3] == "2024-01-15 00:00:00"

    def test_clean_row_with_db_type(self):
        """Test cleaning a row with database type."""
        row = [UUID("12345678-1234-5678-1234-567812345678")]
        result = clean_row(row, db_type="postgres")

        assert result[0] == "12345678-1234-5678-1234-567812345678"


class TestCleanRows:
    """Tests for clean_rows function."""

    def test_clean_rows(self):
        """Test cleaning multiple rows."""
        rows = [
            [1, "Alice", Decimal("100.0")],
            [2, "Bob", Decimal("200.0")],
        ]
        result = clean_rows(rows)

        assert len(result) == 2
        assert result[0] == [1, "Alice", 100.0]
        assert result[1] == [2, "Bob", 200.0]

    def test_clean_empty_rows(self):
        """Test cleaning empty rows list."""
        result = clean_rows([])
        assert result == []


class TestConverterRegistry:
    """Tests for converter registry functions."""

    def test_get_converter_default(self):
        """Test getting a default converter."""
        converter = get_converter("mysql", Decimal)
        assert converter is not None
        assert converter(Decimal("10")) == 10.0

    def test_get_converter_not_found(self):
        """Test getting a converter that doesn't exist."""
        converter = get_converter("mysql", complex)
        assert converter is None

    def test_register_custom_converter(self):
        """Test registering a custom converter."""

        class CustomType:
            def __init__(self, value):
                self.value = value

        register_converter("mysql", CustomType, lambda v: f"custom:{v.value}")

        converter = get_converter("mysql", CustomType)
        assert converter is not None
        assert converter(CustomType("test")) == "custom:test"

    def test_database_specific_converter(self):
        """Test database-specific converters take precedence."""
        # Register a postgres-specific converter
        register_converter("postgres", tuple, lambda v: f"pg_array:{v}")

        # Get postgres converter
        converter = get_converter("postgres", tuple)
        assert converter is not None

        # MySQL should have different behavior
        mysql_converter = get_converter("mysql", tuple)
        # MySQL falls back to default which may or may not exist
