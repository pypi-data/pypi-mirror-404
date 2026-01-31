"""Tests for database base module."""

from mysql_to_sheets.core.database.base import DatabaseConfig, FetchResult


class TestDatabaseConfig:
    """Tests for DatabaseConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DatabaseConfig()

        assert config.db_type == "mysql"
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.user == ""
        assert config.password == ""
        assert config.database == ""
        assert config.connect_timeout == 10
        assert config.read_timeout == 300
        assert config.ssl_mode == ""
        assert config.ssl_ca == ""

    def test_mysql_config(self):
        """Test MySQL configuration."""
        config = DatabaseConfig(
            db_type="mysql",
            host="db.example.com",
            port=3306,
            user="admin",
            password="secret",
            database="testdb",
        )

        assert config.db_type == "mysql"
        assert config.host == "db.example.com"
        assert config.port == 3306

    def test_postgres_config_default_port(self):
        """Test that PostgreSQL uses default port 5432 when not specified."""
        config = DatabaseConfig(
            db_type="postgres",
            host="db.example.com",
            user="admin",
            password="secret",
            database="testdb",
        )

        assert config.db_type == "postgres"
        assert config.port == 5432  # Should be auto-corrected

    def test_postgres_config_explicit_port(self):
        """Test that explicit port is preserved for PostgreSQL."""
        config = DatabaseConfig(
            db_type="postgres",
            host="db.example.com",
            port=5433,  # Non-default port
            user="admin",
            password="secret",
            database="testdb",
        )

        assert config.port == 5433

    def test_postgres_ssl_config(self):
        """Test PostgreSQL SSL configuration."""
        config = DatabaseConfig(
            db_type="postgres",
            host="db.example.com",
            user="admin",
            password="secret",
            database="testdb",
            ssl_mode="require",
            ssl_ca="/path/to/ca.pem",
        )

        assert config.ssl_mode == "require"
        assert config.ssl_ca == "/path/to/ca.pem"


class TestFetchResult:
    """Tests for FetchResult dataclass."""

    def test_empty_result(self):
        """Test empty result initialization."""
        result = FetchResult()

        assert result.headers == []
        assert result.rows == []
        assert result.row_count == 0

    def test_with_data(self):
        """Test result with data."""
        result = FetchResult(
            headers=["id", "name", "email"],
            rows=[
                [1, "Alice", "alice@example.com"],
                [2, "Bob", "bob@example.com"],
            ],
        )

        assert result.headers == ["id", "name", "email"]
        assert len(result.rows) == 2
        assert result.row_count == 2

    def test_row_count_auto_calculated(self):
        """Test that row_count is calculated from rows if not provided."""
        result = FetchResult(
            headers=["id"],
            rows=[[1], [2], [3]],
        )

        assert result.row_count == 3

    def test_row_count_explicit(self):
        """Test explicit row_count overrides calculation."""
        result = FetchResult(
            headers=["id"],
            rows=[[1], [2], [3]],
            row_count=10,  # Explicit value
        )

        assert result.row_count == 10
