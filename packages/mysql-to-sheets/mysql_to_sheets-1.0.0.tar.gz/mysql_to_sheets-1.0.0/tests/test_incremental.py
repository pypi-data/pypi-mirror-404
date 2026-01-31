"""Tests for incremental sync module."""

from datetime import datetime, timedelta, timezone

import pytest

from mysql_to_sheets.core.incremental import (
    IncrementalConfig,
    build_incremental_query,
    create_incremental_config,
    has_group_or_order,
    has_where_clause,
    parse_relative_timestamp,
    parse_timestamp,
)


class TestIncrementalConfig:
    """Tests for IncrementalConfig."""

    def test_default_inactive(self):
        """Test config is inactive by default."""
        config = IncrementalConfig()

        assert config.is_active() is False

    def test_active_when_configured(self):
        """Test config is active when properly configured."""
        config = IncrementalConfig(
            enabled=True,
            timestamp_column="updated_at",
            since=datetime(2024, 1, 1),
        )

        assert config.is_active() is True

    def test_inactive_without_since(self):
        """Test config is inactive without since timestamp."""
        config = IncrementalConfig(
            enabled=True,
            timestamp_column="updated_at",
        )

        assert config.is_active() is False

    def test_inactive_without_column(self):
        """Test config is inactive without timestamp column."""
        config = IncrementalConfig(
            enabled=True,
            since=datetime(2024, 1, 1),
        )

        assert config.is_active() is False


class TestBuildIncrementalQuery:
    """Tests for build_incremental_query function."""

    def test_inactive_config_unchanged(self):
        """Test query unchanged with inactive config."""
        query = "SELECT * FROM users"
        config = IncrementalConfig()

        result = build_incremental_query(query, config)

        assert result == query

    def test_simple_query_add_where(self):
        """Test adding WHERE to simple query."""
        query = "SELECT * FROM users"
        config = IncrementalConfig(
            enabled=True,
            timestamp_column="updated_at",
            since=datetime(2024, 1, 15, 10, 30, 0),
        )

        result = build_incremental_query(query, config)

        assert "WHERE updated_at > '2024-01-15 10:30:00'" in result

    def test_query_with_existing_where(self):
        """Test adding to existing WHERE clause."""
        query = "SELECT * FROM users WHERE active = 1"
        config = IncrementalConfig(
            enabled=True,
            timestamp_column="updated_at",
            since=datetime(2024, 1, 1),
        )

        result = build_incremental_query(query, config)

        assert "active = 1" in result
        assert "updated_at >" in result
        assert " AND " in result

    def test_query_with_order_by(self):
        """Test inserting WHERE before ORDER BY."""
        query = "SELECT * FROM users ORDER BY name"
        config = IncrementalConfig(
            enabled=True,
            timestamp_column="created_at",
            since=datetime(2024, 1, 1),
        )

        result = build_incremental_query(query, config)

        # WHERE should come before ORDER BY
        where_pos = result.upper().find("WHERE")
        order_pos = result.upper().find("ORDER BY")
        assert where_pos < order_pos

    def test_query_with_group_by(self):
        """Test inserting WHERE before GROUP BY."""
        query = "SELECT category, COUNT(*) FROM products GROUP BY category"
        config = IncrementalConfig(
            enabled=True,
            timestamp_column="updated_at",
            since=datetime(2024, 1, 1),
        )

        result = build_incremental_query(query, config)

        where_pos = result.upper().find("WHERE")
        group_pos = result.upper().find("GROUP BY")
        assert where_pos < group_pos

    def test_query_with_until(self):
        """Test adding both since and until filters."""
        query = "SELECT * FROM users"
        config = IncrementalConfig(
            enabled=True,
            timestamp_column="updated_at",
            since=datetime(2024, 1, 1),
            until=datetime(2024, 1, 31),
        )

        result = build_incremental_query(query, config)

        assert "updated_at > '2024-01-01 00:00:00'" in result
        assert "updated_at <= '2024-01-31 00:00:00'" in result


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_has_where_clause_true(self):
        """Test detecting WHERE clause."""
        assert has_where_clause("SELECT * FROM users WHERE id = 1") is True
        assert has_where_clause("SELECT * from users where id = 1") is True

    def test_has_where_clause_false(self):
        """Test detecting absence of WHERE clause."""
        assert has_where_clause("SELECT * FROM users") is False
        assert has_where_clause("SELECT * FROM users ORDER BY name") is False

    def test_has_group_or_order_true(self):
        """Test detecting GROUP BY and ORDER BY."""
        assert has_group_or_order("SELECT * FROM users ORDER BY name") is True
        assert has_group_or_order("SELECT * FROM users GROUP BY category") is True

    def test_has_group_or_order_false(self):
        """Test absence of GROUP BY and ORDER BY."""
        assert has_group_or_order("SELECT * FROM users") is False
        assert has_group_or_order("SELECT * FROM users WHERE id = 1") is False


class TestParseTimestamp:
    """Tests for timestamp parsing."""

    def test_parse_iso_format(self):
        """Test parsing ISO format."""
        result = parse_timestamp("2024-01-15T10:30:00")

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_mysql_format(self):
        """Test parsing MySQL datetime format."""
        result = parse_timestamp("2024-01-15 10:30:00")

        assert result.year == 2024
        assert result.hour == 10

    def test_parse_date_only(self):
        """Test parsing date without time."""
        result = parse_timestamp("2024-01-15")

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0

    def test_parse_with_microseconds(self):
        """Test parsing timestamp with microseconds."""
        result = parse_timestamp("2024-01-15 10:30:00.123456")

        assert result.microsecond == 123456

    def test_parse_invalid_format(self):
        """Test error on invalid format."""
        with pytest.raises(ValueError):
            parse_timestamp("not a date")


class TestParseRelativeTimestamp:
    """Tests for relative timestamp parsing."""

    def test_parse_days(self):
        """Test parsing days offset."""
        result = parse_relative_timestamp("-7d")
        expected = datetime.now(timezone.utc) - timedelta(days=7)

        # Allow 1 second tolerance
        assert abs((result - expected).total_seconds()) < 1

    def test_parse_hours(self):
        """Test parsing hours offset."""
        result = parse_relative_timestamp("-24h")
        expected = datetime.now(timezone.utc) - timedelta(hours=24)

        assert abs((result - expected).total_seconds()) < 1

    def test_parse_minutes(self):
        """Test parsing minutes offset."""
        result = parse_relative_timestamp("-30m")
        expected = datetime.now(timezone.utc) - timedelta(minutes=30)

        assert abs((result - expected).total_seconds()) < 1

    def test_parse_seconds(self):
        """Test parsing seconds offset."""
        result = parse_relative_timestamp("-60s")
        expected = datetime.now(timezone.utc) - timedelta(seconds=60)

        assert abs((result - expected).total_seconds()) < 1

    def test_invalid_format(self):
        """Test error on invalid format."""
        with pytest.raises(ValueError):
            parse_relative_timestamp("7d")  # Missing minus

        with pytest.raises(ValueError):
            parse_relative_timestamp("-7x")  # Invalid unit


class TestCreateIncrementalConfig:
    """Tests for create_incremental_config factory function."""

    def test_create_with_string_since(self):
        """Test creating config with string timestamp."""
        config = create_incremental_config(
            enabled=True,
            timestamp_column="updated_at",
            since="2024-01-15T10:30:00",
        )

        assert config.is_active() is True
        assert config.since.year == 2024

    def test_create_with_datetime_since(self):
        """Test creating config with datetime object."""
        since = datetime(2024, 1, 15)
        config = create_incremental_config(
            enabled=True,
            timestamp_column="updated_at",
            since=since,
        )

        assert config.since == since

    def test_create_with_relative_since(self):
        """Test creating config with relative timestamp."""
        config = create_incremental_config(
            enabled=True,
            timestamp_column="updated_at",
            since="-7d",
        )

        expected = datetime.now(timezone.utc) - timedelta(days=7)
        assert abs((config.since - expected).total_seconds()) < 1

    def test_create_disabled(self):
        """Test creating disabled config."""
        config = create_incremental_config(
            enabled=False,
            timestamp_column="updated_at",
            since="2024-01-15",
        )

        assert config.is_active() is False
