"""Tests for PostgreSQL database connection."""

from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.database.base import DatabaseConfig
from mysql_to_sheets.core.database.postgres import PostgresConnection, _get_psycopg2
from mysql_to_sheets.core.exceptions import DatabaseError, UnsupportedDatabaseError


class TestGetPsycopg2:
    """Tests for _get_psycopg2 lazy import."""

    def test_import_success(self):
        """Test successful psycopg2 import."""
        # This test will pass if psycopg2 is installed
        try:
            psycopg2 = _get_psycopg2()
            assert psycopg2 is not None
        except UnsupportedDatabaseError:
            # psycopg2 not installed - skip this test
            pytest.skip("psycopg2 not installed")

    @patch.dict("sys.modules", {"psycopg2": None})
    def test_import_failure(self):
        """Test import failure raises UnsupportedDatabaseError."""
        # Clear any cached import
        import sys

        if "mysql_to_sheets.core.database.postgres" in sys.modules:
            # Force reimport by removing from cache
            pass

        # This test verifies the error message
        with pytest.raises(UnsupportedDatabaseError) as exc_info:
            # Force a new import attempt
            import importlib

            import mysql_to_sheets.core.database.postgres as pg_module

            importlib.reload(pg_module)
            pg_module._get_psycopg2()

        assert "psycopg2" in str(exc_info.value.message).lower()


class TestPostgresConnection:
    """Tests for PostgresConnection class."""

    def test_db_type(self):
        """Test that db_type returns 'postgres'."""
        config = DatabaseConfig(db_type="postgres", user="test", password="test")
        conn = PostgresConnection(config)
        assert conn.db_type == "postgres"

    def test_build_connection_params(self):
        """Test connection parameter building."""
        config = DatabaseConfig(
            db_type="postgres",
            host="db.example.com",
            port=5432,
            user="admin",
            password="secret",
            database="testdb",
            connect_timeout=30,
        )

        conn = PostgresConnection(config)
        params = conn._build_connection_params()

        assert params["host"] == "db.example.com"
        assert params["port"] == 5432
        assert params["user"] == "admin"
        assert params["password"] == "secret"
        assert params["dbname"] == "testdb"
        assert params["connect_timeout"] == 30

    def test_build_connection_params_with_ssl(self):
        """Test connection parameter building with SSL."""
        config = DatabaseConfig(
            db_type="postgres",
            host="db.example.com",
            user="admin",
            password="secret",
            database="testdb",
            ssl_mode="verify-full",
            ssl_ca="/path/to/ca.pem",
        )

        conn = PostgresConnection(config)
        params = conn._build_connection_params()

        assert params["sslmode"] == "verify-full"
        assert params["sslrootcert"] == "/path/to/ca.pem"

    @patch("mysql_to_sheets.core.database.postgres._get_psycopg2")
    def test_connect_success(self, mock_get_psycopg2):
        """Test successful connection."""
        mock_psycopg2 = MagicMock()
        mock_connection = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection
        mock_get_psycopg2.return_value = mock_psycopg2

        config = DatabaseConfig(
            db_type="postgres",
            host="localhost",
            port=5432,
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = PostgresConnection(config)
        conn.connect()

        mock_psycopg2.connect.assert_called_once()
        call_kwargs = mock_psycopg2.connect.call_args[1]
        assert call_kwargs["host"] == "localhost"
        assert call_kwargs["port"] == 5432
        assert call_kwargs["dbname"] == "testdb"

    @patch("mysql_to_sheets.core.database.postgres._get_psycopg2")
    def test_connect_failure(self, mock_get_psycopg2):
        """Test connection failure raises DatabaseError."""
        mock_psycopg2 = MagicMock()
        mock_psycopg2.Error = Exception
        mock_psycopg2.connect.side_effect = Exception("Connection refused")
        mock_get_psycopg2.return_value = mock_psycopg2

        config = DatabaseConfig(
            db_type="postgres",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = PostgresConnection(config)

        with pytest.raises(DatabaseError) as exc_info:
            conn.connect()

        assert "Failed to connect to PostgreSQL" in str(exc_info.value.message)

    @patch("mysql_to_sheets.core.database.postgres._get_psycopg2")
    def test_execute_success(self, mock_get_psycopg2):
        """Test successful query execution."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",), ("email",)]
        mock_cursor.fetchall.return_value = [
            (1, "Alice", "alice@example.com"),
            (2, "Bob", "bob@example.com"),
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection
        mock_psycopg2.Error = Exception
        mock_get_psycopg2.return_value = mock_psycopg2

        config = DatabaseConfig(
            db_type="postgres",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = PostgresConnection(config)
        result = conn.execute("SELECT * FROM users")

        assert result.headers == ["id", "name", "email"]
        assert len(result.rows) == 2
        assert result.rows[0] == [1, "Alice", "alice@example.com"]

    @patch("mysql_to_sheets.core.database.postgres._get_psycopg2")
    def test_execute_streaming(self, mock_get_psycopg2):
        """Test streaming query execution with named cursor."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchmany.side_effect = [
            [(1, "Alice"), (2, "Bob")],
            [(3, "Charlie")],
            [],
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection
        mock_psycopg2.Error = Exception
        mock_get_psycopg2.return_value = mock_psycopg2

        config = DatabaseConfig(
            db_type="postgres",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = PostgresConnection(config)
        chunks = list(conn.execute_streaming("SELECT * FROM users", chunk_size=2))

        assert len(chunks) == 2
        assert chunks[0].headers == ["id", "name"]
        assert len(chunks[0].rows) == 2
        assert len(chunks[1].rows) == 1

        # Verify named cursor was used for server-side cursor
        # The cursor name includes thread ID and timestamp for uniqueness (EC-27)
        mock_connection.cursor.assert_called_once()
        call_kwargs = mock_connection.cursor.call_args.kwargs
        assert "name" in call_kwargs
        assert call_kwargs["name"].startswith("streaming_cursor_")

    @patch("mysql_to_sheets.core.database.postgres._get_psycopg2")
    def test_test_connection_success(self, mock_get_psycopg2):
        """Test connection test success."""
        mock_connection = MagicMock()

        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection
        mock_psycopg2.Error = Exception
        mock_get_psycopg2.return_value = mock_psycopg2

        config = DatabaseConfig(
            db_type="postgres",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = PostgresConnection(config)
        result = conn.test_connection()

        assert result is True
        mock_connection.close.assert_called_once()

    @patch("mysql_to_sheets.core.database.postgres._get_psycopg2")
    def test_context_manager(self, mock_get_psycopg2):
        """Test context manager usage."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",)]
        mock_cursor.fetchall.return_value = [(1,)]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection
        mock_psycopg2.Error = Exception
        mock_get_psycopg2.return_value = mock_psycopg2

        config = DatabaseConfig(
            db_type="postgres",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        with PostgresConnection(config) as conn:
            result = conn.execute("SELECT 1")
            assert result.rows == [[1]]

        mock_connection.close.assert_called()
