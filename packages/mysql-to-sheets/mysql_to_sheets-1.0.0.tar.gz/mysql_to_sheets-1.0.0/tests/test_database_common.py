"""Common parameterized tests across all database backends.

This test module verifies that all database implementations (MySQL, PostgreSQL,
SQLite, SQL Server) comply with the DatabaseConnection protocol and behave
consistently across the factory and connection lifecycle.
"""

from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.database.base import DatabaseConfig, FetchResult, WriteResult
from mysql_to_sheets.core.database.factory import get_connection
from mysql_to_sheets.core.database.mssql import MSSQLConnection
from mysql_to_sheets.core.database.mysql import MySQLConnection
from mysql_to_sheets.core.database.postgres import PostgresConnection
from mysql_to_sheets.core.database.sqlite import SQLiteConnection
from mysql_to_sheets.core.exceptions import UnsupportedDatabaseError

# Database type mapping for parameterized tests
DATABASE_TYPES = [
    ("mysql", MySQLConnection, "mysql.connector"),
    ("postgres", PostgresConnection, "psycopg2"),
    ("sqlite", SQLiteConnection, "sqlite3"),
    ("mssql", MSSQLConnection, "pymssql"),
]


def _patch_driver(db_type, driver_module):
    """Helper to get the correct patch path for each database type.

    Postgres and MSSQL use lazy imports via getter functions, while
    MySQL and SQLite import directly.
    """
    if db_type == "postgres":
        return patch(f"mysql_to_sheets.core.database.{db_type}._get_psycopg2")
    elif db_type == "mssql":
        return patch(f"mysql_to_sheets.core.database.{db_type}._get_pymssql")
    else:
        return patch(f"mysql_to_sheets.core.database.{db_type}.{driver_module}")


class TestDatabaseFactory:
    """Tests for get_connection factory function across all backends."""

    @pytest.mark.parametrize("db_type,expected_class,_", DATABASE_TYPES)
    def test_factory_returns_correct_type(self, db_type, expected_class, _):
        """Test factory returns correct connection class for each db_type."""
        config = DatabaseConfig(
            db_type=db_type,
            host="localhost",
            user="test_user",
            password="test_pass",
            database="test_db" if db_type != "sqlite" else ":memory:",
        )

        conn = get_connection(config)

        assert isinstance(conn, expected_class)
        assert conn.db_type in (db_type, "postgres")  # Allow 'postgres' for postgresql

    @pytest.mark.parametrize("db_type,expected_class,_", DATABASE_TYPES)
    def test_factory_case_insensitive(self, db_type, expected_class, _):
        """Test factory handles case-insensitive db_type."""
        config = DatabaseConfig(
            db_type=db_type.upper(),
            host="localhost",
            user="test_user",
            password="test_pass",
            database="test_db" if db_type != "sqlite" else ":memory:",
        )

        conn = get_connection(config)

        assert isinstance(conn, expected_class)

    def test_factory_unsupported_database(self):
        """Test factory raises error for unsupported database type."""
        config = DatabaseConfig(
            db_type="oracle",
            host="localhost",
            user="test",
            password="test",
        )

        with pytest.raises(UnsupportedDatabaseError) as exc_info:
            get_connection(config)

        assert "oracle" in str(exc_info.value.message).lower()
        assert "mysql" in str(exc_info.value.message).lower()

    @pytest.mark.parametrize(
        "alias,expected_class",
        [
            ("postgresql", PostgresConnection),
            ("sqlserver", MSSQLConnection),
        ],
    )
    def test_factory_aliases(self, alias, expected_class):
        """Test factory accepts database type aliases."""
        config = DatabaseConfig(
            db_type=alias,
            host="localhost",
            user="test",
            password="test",
            database="test_db",
        )

        conn = get_connection(config)

        assert isinstance(conn, expected_class)


class TestConnectionLifecycle:
    """Tests for connection lifecycle methods across all backends."""

    @pytest.mark.parametrize("db_type,connection_class,driver_module", DATABASE_TYPES)
    def test_connect_success(self, db_type, connection_class, driver_module):
        """Test successful connection for each backend."""
        mock_connection = MagicMock()

        with _patch_driver(db_type, driver_module) as mock_driver:
            if db_type in ("postgres", "mssql"):
                # Lazy import pattern - return mock module
                mock_module = MagicMock()
                mock_module.connect.return_value = mock_connection
                mock_driver.return_value = mock_module
            else:
                # Direct import pattern
                mock_driver.connect.return_value = mock_connection

            config = DatabaseConfig(
                db_type=db_type,
                host="localhost",
                user="test_user",
                password="test_pass",
                database="test_db" if db_type != "sqlite" else ":memory:",
            )

            conn = connection_class(config)
            conn.connect()

            assert conn._connection is not None

    @pytest.mark.parametrize("db_type,connection_class,driver_module", DATABASE_TYPES)
    def test_close_connection(self, db_type, connection_class, driver_module):
        """Test closing connection cleans up resources."""
        mock_connection = MagicMock()

        config = DatabaseConfig(
            db_type=db_type,
            host="localhost",
            user="test_user",
            password="test_pass",
            database="test_db" if db_type != "sqlite" else ":memory:",
        )

        conn = connection_class(config)
        conn._connection = mock_connection

        conn.close()

        assert conn._connection is None
        mock_connection.close.assert_called_once()

    @pytest.mark.parametrize("db_type,connection_class,driver_module", DATABASE_TYPES)
    def test_context_manager(self, db_type, connection_class, driver_module):
        """Test connection works as context manager."""
        mock_connection = MagicMock()

        with _patch_driver(db_type, driver_module) as mock_driver:
            if db_type in ("postgres", "mssql"):
                mock_module = MagicMock()
                mock_module.connect.return_value = mock_connection
                mock_driver.return_value = mock_module
            else:
                mock_driver.connect.return_value = mock_connection

            config = DatabaseConfig(
                db_type=db_type,
                host="localhost",
                user="test_user",
                password="test_pass",
                database="test_db" if db_type != "sqlite" else ":memory:",
            )

            conn = connection_class(config)

            with conn:
                assert conn._connection is not None

            # Connection should be closed after exiting context
            assert conn._connection is None


class TestQueryExecution:
    """Tests for query execution across all backends."""

    @pytest.mark.parametrize("db_type,connection_class,driver_module", DATABASE_TYPES)
    def test_execute_success(self, db_type, connection_class, driver_module):
        """Test successful query execution returns FetchResult."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",), ("email",)]
        mock_cursor.fetchall.return_value = [
            (1, "Alice", "alice@example.com"),
            (2, "Bob", "bob@example.com"),
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with _patch_driver(db_type, driver_module) as mock_driver:
            if db_type in ("postgres", "mssql"):
                mock_module = MagicMock()
                mock_module.connect.return_value = mock_connection
                mock_driver.return_value = mock_module
            else:
                mock_driver.connect.return_value = mock_connection

            config = DatabaseConfig(
                db_type=db_type,
                host="localhost",
                user="test_user",
                password="test_pass",
                database="test_db" if db_type != "sqlite" else ":memory:",
            )

            conn = connection_class(config)
            result = conn.execute("SELECT * FROM users")

            assert isinstance(result, FetchResult)
            assert result.headers == ["id", "name", "email"]
            assert len(result.rows) == 2
            assert result.rows[0] == [1, "Alice", "alice@example.com"]
            assert result.row_count == 2

    @pytest.mark.parametrize("db_type,connection_class,driver_module", DATABASE_TYPES)
    def test_execute_streaming(self, db_type, connection_class, driver_module):
        """Test streaming query execution yields chunks."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchmany.side_effect = [
            [(1, "Alice"), (2, "Bob")],  # First chunk
            [(3, "Charlie")],  # Second chunk
            [],  # End of results
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with _patch_driver(db_type, driver_module) as mock_driver:
            if db_type in ("postgres", "mssql"):
                mock_module = MagicMock()
                mock_module.connect.return_value = mock_connection
                mock_driver.return_value = mock_module
            else:
                mock_driver.connect.return_value = mock_connection

            config = DatabaseConfig(
                db_type=db_type,
                host="localhost",
                user="test_user",
                password="test_pass",
                database="test_db" if db_type != "sqlite" else ":memory:",
            )

            conn = connection_class(config)
            chunks = list(conn.execute_streaming("SELECT * FROM users", chunk_size=2))

            assert len(chunks) == 2
            assert chunks[0].row_count == 2
            assert chunks[1].row_count == 1
            assert chunks[0].headers == ["id", "name"]


class TestWriteOperations:
    """Tests for write operations across all backends."""

    @pytest.mark.parametrize("db_type,connection_class,driver_module", DATABASE_TYPES)
    def test_insert_rows(self, db_type, connection_class, driver_module):
        """Test inserting rows returns WriteResult."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 3

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with _patch_driver(db_type, driver_module) as mock_driver:
            if db_type in ("postgres", "mssql"):
                mock_module = MagicMock()
                mock_module.connect.return_value = mock_connection
                mock_driver.return_value = mock_module
            else:
                mock_driver.connect.return_value = mock_connection

            config = DatabaseConfig(
                db_type=db_type,
                host="localhost",
                user="test_user",
                password="test_pass",
                database="test_db" if db_type != "sqlite" else ":memory:",
            )

            conn = connection_class(config)
            result = conn.insert_rows(
                table="users",
                columns=["name", "email"],
                rows=[
                    ["Alice", "alice@example.com"],
                    ["Bob", "bob@example.com"],
                    ["Charlie", "charlie@example.com"],
                ],
            )

            assert isinstance(result, WriteResult)
            assert result.rows_affected == 3
            assert result.rows_inserted == 3
            mock_connection.commit.assert_called_once()

    @pytest.mark.parametrize("db_type,connection_class,driver_module", DATABASE_TYPES)
    def test_insert_empty_rows(self, db_type, connection_class, driver_module):
        """Test inserting empty rows returns zero affected without database call."""
        mock_connection = MagicMock()

        with _patch_driver(db_type, driver_module) as mock_driver:
            if db_type in ("postgres", "mssql"):
                mock_module = MagicMock()
                mock_module.connect.return_value = mock_connection
                mock_driver.return_value = mock_module
            else:
                mock_driver.connect.return_value = mock_connection

            config = DatabaseConfig(
                db_type=db_type,
                host="localhost",
                user="test_user",
                password="test_pass",
                database="test_db" if db_type != "sqlite" else ":memory:",
            )

            conn = connection_class(config)
            result = conn.insert_rows(table="users", columns=["name", "email"], rows=[])

            assert isinstance(result, WriteResult)
            assert result.rows_affected == 0
            # Should have connected but not executed any query
            assert conn._connection is not None

    @pytest.mark.parametrize("db_type,connection_class,driver_module", DATABASE_TYPES)
    def test_upsert_rows(self, db_type, connection_class, driver_module):
        """Test upserting rows returns WriteResult."""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 2

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with _patch_driver(db_type, driver_module) as mock_driver:
            if db_type in ("postgres", "mssql"):
                mock_module = MagicMock()
                mock_module.connect.return_value = mock_connection
                mock_driver.return_value = mock_module
            else:
                mock_driver.connect.return_value = mock_connection

            config = DatabaseConfig(
                db_type=db_type,
                host="localhost",
                user="test_user",
                password="test_pass",
                database="test_db" if db_type != "sqlite" else ":memory:",
            )

            conn = connection_class(config)
            result = conn.upsert_rows(
                table="users",
                columns=["id", "name", "email"],
                rows=[
                    [1, "Alice", "alice@example.com"],
                    [2, "Bob", "bob@example.com"],
                ],
                key_columns=["id"],
            )

            assert isinstance(result, WriteResult)
            assert result.rows_affected >= 0
            mock_connection.commit.assert_called_once()


class TestConnectionPool:
    """Tests for MySQL connection pooling."""

    @patch("mysql_to_sheets.core.connection_pool.MySQLConnectionPool")
    def test_get_connection_pool_creates_pool(self, mock_pool_class):
        """Test connection pool is created with correct config."""
        from mysql_to_sheets.core.config import Config
        from mysql_to_sheets.core.connection_pool import get_connection_pool, reset_pool

        # Reset pool before test
        reset_pool()

        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        config = Config(
            db_type="mysql",
            db_host="localhost",
            db_user="test",
            db_password="test",
            db_name="testdb",
            db_pool_size=10,
            google_sheet_id="test123",
            sql_query="SELECT 1",
        )

        pool = get_connection_pool(config)

        assert pool == mock_pool
        mock_pool_class.assert_called_once()

    @patch("mysql_to_sheets.core.connection_pool.MySQLConnectionPool")
    def test_pooled_connection_context_manager(self, mock_pool_class):
        """Test pooled_connection context manager."""
        from mysql_to_sheets.core.config import Config
        from mysql_to_sheets.core.connection_pool import pooled_connection, reset_pool

        # Reset pool before test
        reset_pool()

        mock_pool = MagicMock()
        mock_connection = MagicMock()
        mock_pool.get_connection.return_value = mock_connection
        mock_pool_class.return_value = mock_pool

        config = Config(
            db_type="mysql",
            db_host="localhost",
            db_user="test",
            db_password="test",
            db_name="testdb",
            google_sheet_id="test123",
            sql_query="SELECT 1",
        )

        with pooled_connection(config) as conn:
            assert conn == mock_connection

        mock_connection.close.assert_called_once()
