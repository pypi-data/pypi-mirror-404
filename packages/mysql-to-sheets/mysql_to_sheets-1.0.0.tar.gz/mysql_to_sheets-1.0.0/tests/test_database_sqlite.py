"""Tests for SQLite database connection."""

import os
import tempfile

import pytest

from mysql_to_sheets.core.database.base import DatabaseConfig
from mysql_to_sheets.core.database.sqlite import SQLiteConnection
from mysql_to_sheets.core.exceptions import DatabaseError


class TestSQLiteConnection:
    """Tests for SQLiteConnection class."""

    def test_db_type(self):
        """Test that db_type returns 'sqlite'."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        conn = SQLiteConnection(config)
        assert conn.db_type == "sqlite"

    def test_connect_memory(self):
        """Test connection to in-memory database."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        with SQLiteConnection(config) as conn:
            result = conn.execute("SELECT 1 as test")
            assert result.headers == ["test"]
            assert result.rows == [[1]]

    def test_connect_default_memory(self):
        """Test that empty database field defaults to :memory:."""
        config = DatabaseConfig(db_type="sqlite", database="")
        with SQLiteConnection(config) as conn:
            result = conn.execute("SELECT 1 as test")
            assert result.rows == [[1]]

    def test_connect_file(self):
        """Test connection to file-based database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            config = DatabaseConfig(db_type="sqlite", database=db_path)
            with SQLiteConnection(config) as conn:
                conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
                conn.execute("INSERT INTO test (name) VALUES ('Alice')")
                result = conn.execute("SELECT * FROM test")
                assert result.headers == ["id", "name"]
                assert result.rows == [[1, "Alice"]]
        finally:
            os.unlink(db_path)

    def test_execute_query(self):
        """Test query execution with multiple rows."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        with SQLiteConnection(config) as conn:
            conn.execute("CREATE TABLE users (id INTEGER, name TEXT, email TEXT)")
            conn.execute(
                "INSERT INTO users VALUES (1, 'Alice', 'alice@example.com'), "
                "(2, 'Bob', 'bob@example.com')"
            )
            result = conn.execute("SELECT * FROM users")

            assert result.headers == ["id", "name", "email"]
            assert result.row_count == 2
            assert result.rows[0] == [1, "Alice", "alice@example.com"]
            assert result.rows[1] == [2, "Bob", "bob@example.com"]

    def test_execute_no_results(self):
        """Test query that returns no results."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        with SQLiteConnection(config) as conn:
            conn.execute("CREATE TABLE empty (id INTEGER)")
            result = conn.execute("SELECT * FROM empty")

            assert result.headers == ["id"]
            assert result.rows == []
            assert result.row_count == 0

    def test_execute_auto_connect(self):
        """Test that execute connects automatically if not connected."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        conn = SQLiteConnection(config)
        # Don't call connect() explicitly
        result = conn.execute("SELECT 1 as test")
        assert result.rows == [[1]]
        conn.close()

    def test_execute_streaming(self):
        """Test streaming query execution."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        with SQLiteConnection(config) as conn:
            conn.execute("CREATE TABLE numbers (n INTEGER)")
            # Insert 5 rows
            for i in range(5):
                conn.execute(f"INSERT INTO numbers VALUES ({i})")

            chunks = list(conn.execute_streaming("SELECT * FROM numbers", chunk_size=2))

            # Should get 3 chunks: 2, 2, 1
            assert len(chunks) == 3
            assert chunks[0].headers == ["n"]
            assert len(chunks[0].rows) == 2
            assert len(chunks[1].rows) == 2
            assert len(chunks[2].rows) == 1

    def test_execute_streaming_empty(self):
        """Test streaming with empty result set."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        with SQLiteConnection(config) as conn:
            conn.execute("CREATE TABLE empty (id INTEGER)")
            chunks = list(conn.execute_streaming("SELECT * FROM empty"))
            assert chunks == []

    def test_test_connection_success(self):
        """Test connection test success."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        conn = SQLiteConnection(config)
        result = conn.test_connection()
        assert result is True

    def test_test_connection_file_success(self):
        """Test connection test with file database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            config = DatabaseConfig(db_type="sqlite", database=db_path)
            conn = SQLiteConnection(config)
            result = conn.test_connection()
            assert result is True
        finally:
            os.unlink(db_path)

    def test_context_manager(self):
        """Test context manager usage."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")

        with SQLiteConnection(config) as conn:
            result = conn.execute("SELECT 1 as test")
            assert result.rows == [[1]]

        # Connection should be closed after context manager exits
        assert conn._connection is None

    def test_close_idempotent(self):
        """Test that close() can be called multiple times."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        conn = SQLiteConnection(config)
        conn.connect()

        conn.close()
        conn.close()  # Should not raise

        assert conn._connection is None

    def test_foreign_keys_enabled(self):
        """Test that foreign keys are enabled by default."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        with SQLiteConnection(config) as conn:
            result = conn.execute("PRAGMA foreign_keys")
            # Should return 1 (enabled)
            assert result.rows[0][0] == 1

    def test_execute_syntax_error(self):
        """Test that syntax errors raise DatabaseError."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        with SQLiteConnection(config) as conn:
            with pytest.raises(DatabaseError) as exc_info:
                conn.execute("SELECTT 1")  # Syntax error

            assert "Failed to execute SQLite query" in str(exc_info.value.message)

    def test_execute_table_not_found(self):
        """Test that missing table raises DatabaseError."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        with SQLiteConnection(config) as conn:
            with pytest.raises(DatabaseError) as exc_info:
                conn.execute("SELECT * FROM nonexistent")

            assert "Failed to execute SQLite query" in str(exc_info.value.message)

    def test_database_config_port_zero(self):
        """Test that SQLite sets port to 0 (N/A)."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        # Port should be set to 0 for SQLite (N/A)
        assert config.port == 0


class TestSQLiteConnectionIntegration:
    """Integration tests for SQLite using temporary files."""

    def test_persistence_across_connections(self):
        """Test that data persists across connections for file databases."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # First connection: create and insert
            config = DatabaseConfig(db_type="sqlite", database=db_path)
            with SQLiteConnection(config) as conn:
                conn.execute("CREATE TABLE persist (value TEXT)")
                conn.execute("INSERT INTO persist VALUES ('hello')")

            # Second connection: read
            with SQLiteConnection(config) as conn:
                result = conn.execute("SELECT * FROM persist")
                assert result.rows == [["hello"]]
        finally:
            os.unlink(db_path)

    def test_large_streaming_result(self):
        """Test streaming with larger result set."""
        config = DatabaseConfig(db_type="sqlite", database=":memory:")
        with SQLiteConnection(config) as conn:
            conn.execute("CREATE TABLE big (id INTEGER, data TEXT)")

            # Insert 100 rows
            for i in range(100):
                conn.execute(f"INSERT INTO big VALUES ({i}, 'data_{i}')")

            # Stream with chunk size of 25
            chunks = list(conn.execute_streaming("SELECT * FROM big", chunk_size=25))

            assert len(chunks) == 4
            total_rows = sum(len(chunk.rows) for chunk in chunks)
            assert total_rows == 100
