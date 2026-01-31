"""Tests for MySQL database connection."""

from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.database.base import DatabaseConfig
from mysql_to_sheets.core.database.mysql import MySQLConnection
from mysql_to_sheets.core.exceptions import DatabaseError


class TestMySQLConnection:
    """Tests for MySQLConnection class."""

    def test_db_type(self):
        """Test that db_type returns 'mysql'."""
        config = DatabaseConfig(db_type="mysql", user="test", password="test")
        conn = MySQLConnection(config)
        assert conn.db_type == "mysql"

    @patch("mysql_to_sheets.core.database.mysql.mysql.connector.connect")
    def test_connect_success(self, mock_connect):
        """Test successful connection."""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        config = DatabaseConfig(
            db_type="mysql",
            host="localhost",
            port=3306,
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = MySQLConnection(config)
        conn.connect()

        mock_connect.assert_called_once_with(
            host="localhost",
            port=3306,
            user="admin",
            password="secret",
            database="testdb",
            connection_timeout=10,
        )

    @patch("mysql_to_sheets.core.database.mysql.mysql.connector.connect")
    def test_connect_failure(self, mock_connect):
        """Test connection failure raises DatabaseError."""
        from mysql.connector import Error as MySQLError

        mock_connect.side_effect = MySQLError("Connection refused")

        config = DatabaseConfig(
            db_type="mysql",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = MySQLConnection(config)

        with pytest.raises(DatabaseError) as exc_info:
            conn.connect()

        assert "Failed to connect to MySQL" in str(exc_info.value.message)

    @patch("mysql_to_sheets.core.database.mysql.mysql.connector.connect")
    def test_execute_success(self, mock_connect):
        """Test successful query execution."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",), ("email",)]
        mock_cursor.fetchall.return_value = [
            (1, "Alice", "alice@example.com"),
            (2, "Bob", "bob@example.com"),
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        config = DatabaseConfig(
            db_type="mysql",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = MySQLConnection(config)
        result = conn.execute("SELECT * FROM users")

        assert result.headers == ["id", "name", "email"]
        assert len(result.rows) == 2
        assert result.rows[0] == [1, "Alice", "alice@example.com"]

    @patch("mysql_to_sheets.core.database.mysql.mysql.connector.connect")
    def test_execute_failure(self, mock_connect):
        """Test query execution failure raises DatabaseError."""
        from mysql.connector import Error as MySQLError

        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = MySQLError("Syntax error")

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        config = DatabaseConfig(
            db_type="mysql",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = MySQLConnection(config)

        with pytest.raises(DatabaseError) as exc_info:
            conn.execute("INVALID SQL")

        assert "Failed to execute MySQL query" in str(exc_info.value.message)

    @patch("mysql_to_sheets.core.database.mysql.mysql.connector.connect")
    def test_execute_streaming(self, mock_connect):
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
        mock_connect.return_value = mock_connection

        config = DatabaseConfig(
            db_type="mysql",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = MySQLConnection(config)
        chunks = list(conn.execute_streaming("SELECT * FROM users", chunk_size=2))

        assert len(chunks) == 2
        assert chunks[0].headers == ["id", "name"]
        assert len(chunks[0].rows) == 2
        assert len(chunks[1].rows) == 1

    @patch("mysql_to_sheets.core.database.mysql.mysql.connector.connect")
    def test_test_connection_success(self, mock_connect):
        """Test connection test success."""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        config = DatabaseConfig(
            db_type="mysql",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = MySQLConnection(config)
        result = conn.test_connection()

        assert result is True
        mock_connection.close.assert_called_once()

    @patch("mysql_to_sheets.core.database.mysql.mysql.connector.connect")
    def test_close(self, mock_connect):
        """Test connection close."""
        mock_connection = MagicMock()
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        config = DatabaseConfig(
            db_type="mysql",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        conn = MySQLConnection(config)
        conn.connect()
        conn.close()

        mock_connection.close.assert_called_once()
        assert conn._connection is None

    @patch("mysql_to_sheets.core.database.mysql.mysql.connector.connect")
    def test_context_manager(self, mock_connect):
        """Test context manager usage."""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",)]
        mock_cursor.fetchall.return_value = [(1,)]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.is_connected.return_value = True
        mock_connect.return_value = mock_connection

        config = DatabaseConfig(
            db_type="mysql",
            host="localhost",
            user="admin",
            password="secret",
            database="testdb",
        )

        with MySQLConnection(config) as conn:
            result = conn.execute("SELECT 1")
            assert result.rows == [[1]]

        mock_connection.close.assert_called()
