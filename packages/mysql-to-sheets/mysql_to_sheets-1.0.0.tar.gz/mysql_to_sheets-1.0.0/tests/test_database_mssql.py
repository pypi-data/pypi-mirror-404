"""Tests for SQL Server database connection."""

from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.database.base import DatabaseConfig
from mysql_to_sheets.core.database.mssql import MSSQLConnection, _get_pymssql
from mysql_to_sheets.core.exceptions import DatabaseError, UnsupportedDatabaseError


class TestGetPymssql:
    """Tests for _get_pymssql lazy import."""

    def test_import_success(self):
        """Test successful pymssql import."""
        try:
            pymssql = _get_pymssql()
            assert pymssql is not None
        except UnsupportedDatabaseError:
            # pymssql not installed - skip this test
            pytest.skip("pymssql not installed")

    @patch.dict("sys.modules", {"pymssql": None})
    def test_import_failure(self):
        """Test import failure raises UnsupportedDatabaseError."""
        import importlib
        import sys

        # Remove cached module if present
        if "mysql_to_sheets.core.database.mssql" in sys.modules:
            del sys.modules["mysql_to_sheets.core.database.mssql"]

        with pytest.raises(UnsupportedDatabaseError) as exc_info:
            # Force reimport
            import mysql_to_sheets.core.database.mssql as mssql_module

            importlib.reload(mssql_module)
            mssql_module._get_pymssql()

        assert "pymssql" in str(exc_info.value.message).lower()


class TestMSSQLConnection:
    """Tests for MSSQLConnection class."""

    def test_db_type(self):
        """Test that db_type returns 'mssql'."""
        config = DatabaseConfig(db_type="mssql", user="test", password="test")
        conn = MSSQLConnection(config)
        assert conn.db_type == "mssql"

    def test_database_config_default_port(self):
        """Test that mssql sets default port to 1433."""
        config = DatabaseConfig(db_type="mssql", user="test", password="test")
        assert config.port == 1433

    def test_database_config_sqlserver_alias_port(self):
        """Test that sqlserver alias also sets default port to 1433."""
        config = DatabaseConfig(db_type="sqlserver", user="test", password="test")
        assert config.port == 1433

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_connect_success(self, mock_get_pymssql):
        """Test successful connection."""
        mock_pymssql = MagicMock()
        mock_connection = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(
            db_type="mssql",
            host="sql.example.com",
            port=1433,
            user="admin",
            password="secret",
            database="testdb",
            connect_timeout=30,
        )

        conn = MSSQLConnection(config)
        conn.connect()

        mock_pymssql.connect.assert_called_once_with(
            server="sql.example.com",
            port=1433,
            user="admin",
            password="secret",
            database="testdb",
            timeout=30,
            login_timeout=30,
        )
        assert conn._connection == mock_connection

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_connect_failure(self, mock_get_pymssql):
        """Test connection failure raises DatabaseError."""
        mock_pymssql = MagicMock()
        mock_pymssql.Error = Exception
        mock_pymssql.connect.side_effect = Exception("Connection refused")
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(
            db_type="mssql",
            host="sql.example.com",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = MSSQLConnection(config)

        with pytest.raises(DatabaseError) as exc_info:
            conn.connect()

        assert "Failed to connect to SQL Server" in str(exc_info.value.message)

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_execute_success(self, mock_get_pymssql):
        """Test successful query execution."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",), ("email",)]
        mock_cursor.fetchall.return_value = [
            (1, "Alice", "alice@example.com"),
            (2, "Bob", "bob@example.com"),
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_pymssql.Error = Exception
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(
            db_type="mssql",
            host="sql.example.com",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = MSSQLConnection(config)
        result = conn.execute("SELECT * FROM users")

        assert result.headers == ["id", "name", "email"]
        assert len(result.rows) == 2
        assert result.rows[0] == [1, "Alice", "alice@example.com"]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users")

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_execute_no_results(self, mock_get_pymssql):
        """Test query execution with empty results."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",)]
        mock_cursor.fetchall.return_value = []

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_pymssql.Error = Exception
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(db_type="mssql", user="admin", password="secret")

        conn = MSSQLConnection(config)
        result = conn.execute("SELECT * FROM empty")

        assert result.headers == ["id"]
        assert result.rows == []
        assert result.row_count == 0

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_execute_failure(self, mock_get_pymssql):
        """Test query execution failure raises DatabaseError."""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Syntax error")

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_pymssql.Error = Exception
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(db_type="mssql", user="admin", password="secret")

        conn = MSSQLConnection(config)

        with pytest.raises(DatabaseError) as exc_info:
            conn.execute("SELECT * FROM users")

        assert "Failed to execute SQL Server query" in str(exc_info.value.message)

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_execute_streaming(self, mock_get_pymssql):
        """Test streaming query execution."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchmany.side_effect = [
            [(1, "Alice"), (2, "Bob")],
            [(3, "Charlie")],
            [],
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_pymssql.Error = Exception
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(db_type="mssql", user="admin", password="secret")

        conn = MSSQLConnection(config)
        chunks = list(conn.execute_streaming("SELECT * FROM users", chunk_size=2))

        assert len(chunks) == 2
        assert chunks[0].headers == ["id", "name"]
        assert len(chunks[0].rows) == 2
        assert len(chunks[1].rows) == 1

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_execute_streaming_empty(self, mock_get_pymssql):
        """Test streaming with empty result set."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",)]
        mock_cursor.fetchmany.return_value = []

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_pymssql.Error = Exception
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(db_type="mssql", user="admin", password="secret")

        conn = MSSQLConnection(config)
        chunks = list(conn.execute_streaming("SELECT * FROM empty"))

        assert chunks == []

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_execute_streaming_failure(self, mock_get_pymssql):
        """Test streaming query failure raises DatabaseError."""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Query failed")

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_pymssql.Error = Exception
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(db_type="mssql", user="admin", password="secret")

        conn = MSSQLConnection(config)

        with pytest.raises(DatabaseError) as exc_info:
            list(conn.execute_streaming("SELECT * FROM users"))

        assert "Failed to execute SQL Server streaming query" in str(exc_info.value.message)

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_test_connection_success(self, mock_get_pymssql):
        """Test connection test success."""
        mock_connection = MagicMock()

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_pymssql.Error = Exception
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(
            db_type="mssql",
            host="sql.example.com",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = MSSQLConnection(config)
        result = conn.test_connection()

        assert result is True
        mock_connection.close.assert_called_once()

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_test_connection_failure(self, mock_get_pymssql):
        """Test connection test failure raises DatabaseError."""
        mock_pymssql = MagicMock()
        mock_pymssql.Error = Exception
        mock_pymssql.connect.side_effect = Exception("Connection failed")
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(db_type="mssql", user="admin", password="secret")

        conn = MSSQLConnection(config)

        with pytest.raises(DatabaseError) as exc_info:
            conn.test_connection()

        assert "SQL Server connection test failed" in str(exc_info.value.message)

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_context_manager(self, mock_get_pymssql):
        """Test context manager usage."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("test",)]
        mock_cursor.fetchall.return_value = [(1,)]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_pymssql.Error = Exception
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(db_type="mssql", user="admin", password="secret")

        with MSSQLConnection(config) as conn:
            result = conn.execute("SELECT 1 as test")
            assert result.rows == [[1]]

        mock_connection.close.assert_called()

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_close_idempotent(self, mock_get_pymssql):
        """Test that close() can be called multiple times."""
        mock_connection = MagicMock()

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(db_type="mssql", user="admin", password="secret")
        conn = MSSQLConnection(config)
        conn.connect()

        conn.close()
        conn.close()  # Should not raise

        assert conn._connection is None

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_close_handles_exception(self, mock_get_pymssql):
        """Test that close() handles exceptions gracefully."""
        mock_connection = MagicMock()
        mock_connection.close.side_effect = Exception("Close failed")

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(db_type="mssql", user="admin", password="secret")
        conn = MSSQLConnection(config)
        conn.connect()

        conn.close()  # Should not raise despite exception

        assert conn._connection is None

    @patch("mysql_to_sheets.core.database.mssql._get_pymssql")
    def test_execute_auto_connect(self, mock_get_pymssql):
        """Test that execute connects automatically if not connected."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("test",)]
        mock_cursor.fetchall.return_value = [(1,)]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        mock_pymssql = MagicMock()
        mock_pymssql.connect.return_value = mock_connection
        mock_pymssql.Error = Exception
        mock_get_pymssql.return_value = mock_pymssql

        config = DatabaseConfig(db_type="mssql", user="admin", password="secret")
        conn = MSSQLConnection(config)
        # Don't call connect() explicitly
        result = conn.execute("SELECT 1 as test")

        assert result.rows == [[1]]
        mock_pymssql.connect.assert_called_once()
