"""Tests for database URI parsing functionality."""

import pytest

from mysql_to_sheets.core.config import parse_database_uri


class TestMySQLURIParsing:
    """Tests for MySQL URI parsing."""

    def test_basic_mysql_uri(self):
        """Test basic MySQL connection string."""
        result = parse_database_uri("mysql://root:password@localhost:3306/mydb")

        assert result["db_type"] == "mysql"
        assert result["db_host"] == "localhost"
        assert result["db_port"] == 3306
        assert result["db_user"] == "root"
        assert result["db_password"] == "password"
        assert result["db_name"] == "mydb"

    def test_mysql_default_port(self):
        """Test MySQL URI without port uses default 3306."""
        result = parse_database_uri("mysql://user:pass@myhost/testdb")

        assert result["db_port"] == 3306
        assert result["db_host"] == "myhost"

    def test_mysql_connector_scheme(self):
        """Test mysql+mysqlconnector scheme."""
        result = parse_database_uri("mysql+mysqlconnector://user:pass@host/db")

        assert result["db_type"] == "mysql"

    def test_mysql_pymysql_scheme(self):
        """Test mysql+pymysql scheme."""
        result = parse_database_uri("mysql+pymysql://user:pass@host/db")

        assert result["db_type"] == "mysql"


class TestPostgreSQLURIParsing:
    """Tests for PostgreSQL URI parsing."""

    def test_basic_postgres_uri(self):
        """Test basic PostgreSQL connection string."""
        result = parse_database_uri("postgres://admin:secret@db.example.com:5432/production")

        assert result["db_type"] == "postgres"
        assert result["db_host"] == "db.example.com"
        assert result["db_port"] == 5432
        assert result["db_user"] == "admin"
        assert result["db_password"] == "secret"
        assert result["db_name"] == "production"

    def test_postgresql_scheme(self):
        """Test postgresql:// scheme alias."""
        result = parse_database_uri("postgresql://user:pass@host/db")

        assert result["db_type"] == "postgres"

    def test_postgresql_psycopg2_scheme(self):
        """Test postgresql+psycopg2 scheme."""
        result = parse_database_uri("postgresql+psycopg2://user:pass@host/db")

        assert result["db_type"] == "postgres"

    def test_postgres_default_port(self):
        """Test PostgreSQL URI without port uses default 5432."""
        result = parse_database_uri("postgres://user:pass@host/db")

        assert result["db_port"] == 5432


class TestSQLiteURIParsing:
    """Tests for SQLite URI parsing."""

    def test_sqlite_relative_path(self):
        """Test SQLite with relative path."""
        result = parse_database_uri("sqlite:///data/mydb.sqlite")

        assert result["db_type"] == "sqlite"
        assert result["db_name"] == "data/mydb.sqlite"
        assert result["db_host"] == ""
        assert result["db_port"] == 0
        assert result["db_user"] == ""
        assert result["db_password"] == ""

    def test_sqlite_absolute_path(self):
        """Test SQLite with absolute path (4 slashes)."""
        result = parse_database_uri("sqlite:////var/data/production.db")

        assert result["db_type"] == "sqlite"
        assert result["db_name"] == "/var/data/production.db"

    def test_sqlite_windows_path(self):
        """Test SQLite with Windows-style path."""
        result = parse_database_uri("sqlite:///C:/Users/data/mydb.db")

        assert result["db_type"] == "sqlite"
        assert result["db_name"] == "C:/Users/data/mydb.db"

    def test_sqlite_simple_filename(self):
        """Test SQLite with simple filename."""
        result = parse_database_uri("sqlite:///test.db")

        assert result["db_type"] == "sqlite"
        assert result["db_name"] == "test.db"

    def test_sqlite_memory_db(self):
        """Test SQLite in-memory database."""
        result = parse_database_uri("sqlite:///:memory:")

        assert result["db_type"] == "sqlite"
        assert result["db_name"] == ":memory:"


class TestMSSQLURIParsing:
    """Tests for SQL Server URI parsing."""

    def test_basic_mssql_uri(self):
        """Test basic MSSQL connection string."""
        result = parse_database_uri("mssql://sa:MyPassword@sqlserver.local:1433/AdventureWorks")

        assert result["db_type"] == "mssql"
        assert result["db_host"] == "sqlserver.local"
        assert result["db_port"] == 1433
        assert result["db_user"] == "sa"
        assert result["db_password"] == "MyPassword"
        assert result["db_name"] == "AdventureWorks"

    def test_mssql_pymssql_scheme(self):
        """Test mssql+pymssql scheme."""
        result = parse_database_uri("mssql+pymssql://user:pass@host/db")

        assert result["db_type"] == "mssql"

    def test_mssql_pyodbc_scheme(self):
        """Test mssql+pyodbc scheme."""
        result = parse_database_uri("mssql+pyodbc://user:pass@host/db")

        assert result["db_type"] == "mssql"

    def test_mssql_default_port(self):
        """Test MSSQL URI without port uses default 1433."""
        result = parse_database_uri("mssql://user:pass@host/db")

        assert result["db_port"] == 1433


class TestSpecialCharactersInPassword:
    """Tests for URIs with special characters in password."""

    def test_password_with_at_sign(self):
        """Test password containing @ symbol (URL-encoded as %40)."""
        result = parse_database_uri("mysql://user:p%40ssword@localhost/db")

        assert result["db_password"] == "p@ssword"

    def test_password_with_colon(self):
        """Test password containing : symbol (URL-encoded as %3A)."""
        result = parse_database_uri("mysql://user:pass%3Aword@localhost/db")

        assert result["db_password"] == "pass:word"

    def test_password_with_slash(self):
        """Test password containing / symbol (URL-encoded as %2F)."""
        result = parse_database_uri("mysql://user:pass%2Fword@localhost/db")

        assert result["db_password"] == "pass/word"

    def test_password_with_multiple_special_chars(self):
        """Test password with multiple special characters."""
        result = parse_database_uri("postgres://user:p%40ss%3Aw%2Frd@host/db")

        assert result["db_password"] == "p@ss:w/rd"

    def test_password_with_percent(self):
        """Test password containing % symbol (URL-encoded as %25)."""
        result = parse_database_uri("mysql://user:100%25done@localhost/db")

        assert result["db_password"] == "100%done"

    def test_username_with_special_chars(self):
        """Test username with special characters."""
        result = parse_database_uri("mysql://my%40user:pass@localhost/db")

        assert result["db_user"] == "my@user"


class TestInvalidURIs:
    """Tests for invalid URI handling."""

    def test_empty_uri(self):
        """Test empty URI raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_database_uri("")

    def test_whitespace_uri(self):
        """Test whitespace-only URI raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_database_uri("   ")

    def test_unsupported_scheme(self):
        """Test unsupported database scheme raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported database scheme"):
            parse_database_uri("mongodb://user:pass@host/db")

    def test_missing_hostname(self):
        """Test URI without hostname raises ValueError."""
        with pytest.raises(ValueError, match="must include hostname"):
            parse_database_uri("mysql:///dbname")

    def test_missing_database_name(self):
        """Test URI without database name raises ValueError."""
        with pytest.raises(ValueError, match="must include database name"):
            parse_database_uri("mysql://user:pass@host/")

    def test_sqlite_empty_path(self):
        """Test SQLite URI without path raises ValueError."""
        with pytest.raises(ValueError, match="must include database file path"):
            parse_database_uri("sqlite://")

    def test_invalid_scheme_format(self):
        """Test malformed scheme raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported database scheme"):
            parse_database_uri("notadb://user:pass@host/db")


class TestMissingOptionalParts:
    """Tests for URIs with missing optional components."""

    def test_missing_password(self):
        """Test URI without password."""
        result = parse_database_uri("mysql://user@localhost/db")

        assert result["db_user"] == "user"
        assert result["db_password"] == ""

    def test_missing_user_and_password(self):
        """Test URI without user or password."""
        result = parse_database_uri("mysql://localhost/db")

        assert result["db_user"] == ""
        assert result["db_password"] == ""
        assert result["db_host"] == "localhost"

    def test_empty_password(self):
        """Test URI with empty password (colon but no value)."""
        result = parse_database_uri("mysql://user:@localhost/db")

        assert result["db_user"] == "user"
        assert result["db_password"] == ""


class TestIPAddresses:
    """Tests for URIs with IP addresses."""

    def test_ipv4_address(self):
        """Test URI with IPv4 address."""
        result = parse_database_uri("mysql://user:pass@192.168.1.100:3306/db")

        assert result["db_host"] == "192.168.1.100"

    def test_localhost_explicit(self):
        """Test URI with explicit localhost."""
        result = parse_database_uri("postgres://user:pass@127.0.0.1/db")

        assert result["db_host"] == "127.0.0.1"


class TestCaseInsensitivity:
    """Tests for case handling in URIs."""

    def test_uppercase_scheme(self):
        """Test uppercase scheme is handled."""
        result = parse_database_uri("MYSQL://user:pass@host/db")

        assert result["db_type"] == "mysql"

    def test_mixed_case_scheme(self):
        """Test mixed case scheme is handled."""
        result = parse_database_uri("PostgreSQL://user:pass@host/db")

        assert result["db_type"] == "postgres"
