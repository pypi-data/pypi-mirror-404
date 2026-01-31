"""Tests for database factory module."""

import pytest

from mysql_to_sheets.core.database.base import DatabaseConfig
from mysql_to_sheets.core.database.factory import (
    get_connection,
    get_supported_databases,
)
from mysql_to_sheets.core.database.mssql import MSSQLConnection
from mysql_to_sheets.core.database.mysql import MySQLConnection
from mysql_to_sheets.core.database.postgres import PostgresConnection
from mysql_to_sheets.core.database.sqlite import SQLiteConnection
from mysql_to_sheets.core.exceptions import UnsupportedDatabaseError


class TestGetConnection:
    """Tests for get_connection factory function."""

    def test_get_mysql_connection(self):
        """Test getting a MySQL connection."""
        config = DatabaseConfig(
            db_type="mysql",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = get_connection(config)

        assert isinstance(conn, MySQLConnection)
        assert conn.db_type == "mysql"

    def test_get_postgres_connection(self):
        """Test getting a PostgreSQL connection."""
        config = DatabaseConfig(
            db_type="postgres",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = get_connection(config)

        assert isinstance(conn, PostgresConnection)
        assert conn.db_type == "postgres"

    def test_get_postgresql_alias(self):
        """Test that 'postgresql' is accepted as alias for postgres."""
        config = DatabaseConfig(
            db_type="postgresql",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = get_connection(config)

        assert isinstance(conn, PostgresConnection)

    def test_case_insensitive(self):
        """Test that db_type is case insensitive."""
        config = DatabaseConfig(
            db_type="MySQL",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = get_connection(config)

        assert isinstance(conn, MySQLConnection)

    def test_get_sqlite_connection(self):
        """Test getting a SQLite connection."""
        config = DatabaseConfig(
            db_type="sqlite",
            database=":memory:",
        )

        conn = get_connection(config)

        assert isinstance(conn, SQLiteConnection)
        assert conn.db_type == "sqlite"

    def test_get_mssql_connection(self):
        """Test getting a SQL Server connection."""
        config = DatabaseConfig(
            db_type="mssql",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = get_connection(config)

        assert isinstance(conn, MSSQLConnection)
        assert conn.db_type == "mssql"

    def test_get_sqlserver_alias(self):
        """Test that 'sqlserver' is accepted as alias for mssql."""
        config = DatabaseConfig(
            db_type="sqlserver",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = get_connection(config)

        assert isinstance(conn, MSSQLConnection)

    def test_unsupported_database(self):
        """Test that unsupported database type raises error."""
        config = DatabaseConfig(
            db_type="oracle",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        with pytest.raises(UnsupportedDatabaseError) as exc_info:
            get_connection(config)

        assert "oracle" in str(exc_info.value.message).lower()
        assert "mysql" in str(exc_info.value.message).lower()
        assert "postgres" in str(exc_info.value.message).lower()


class TestGetSupportedDatabases:
    """Tests for get_supported_databases function."""

    def test_supported_databases(self):
        """Test that supported databases are returned."""
        supported = get_supported_databases()

        assert "mysql" in supported
        assert "postgres" in supported
        assert "sqlite" in supported
        assert "mssql" in supported
        assert len(supported) == 4
