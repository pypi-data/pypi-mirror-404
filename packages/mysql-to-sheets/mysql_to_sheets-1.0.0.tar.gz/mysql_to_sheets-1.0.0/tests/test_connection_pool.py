"""Tests for core/connection_pool.py — MySQL connection pooling."""

from unittest.mock import MagicMock, patch

import pytest

# Guard: mysql.connector may not be installed in all environments
mysql_connector = pytest.importorskip("mysql.connector")

from mysql_to_sheets.core.connection_pool import (
    PoolConfig,
    PooledConnection,
    get_connection_pool,
    get_pool_stats,
    pooled_connection,
    reset_pool,
)
from mysql_to_sheets.core.exceptions import DatabaseError


@pytest.fixture(autouse=True)
def _reset_global_pool():
    """Ensure global pool is reset between tests."""
    reset_pool()
    yield
    reset_pool()


class TestPoolConfig:
    def test_defaults(self):
        pc = PoolConfig()
        assert pc.pool_size == 5
        assert pc.pool_name == "mysql_to_sheets_pool"
        assert pc.pool_reset_session is True


class TestGetConnectionPool:
    @patch("mysql_to_sheets.core.connection_pool.MySQLConnectionPool")
    def test_creates_pool(self, mock_pool_cls, mock_config):
        pool = get_connection_pool(mock_config)
        mock_pool_cls.assert_called_once()
        assert pool is mock_pool_cls.return_value

    @patch("mysql_to_sheets.core.connection_pool.MySQLConnectionPool")
    def test_returns_cached_pool(self, mock_pool_cls, mock_config):
        pool1 = get_connection_pool(mock_config)
        pool2 = get_connection_pool(mock_config)
        assert pool1 is pool2
        assert mock_pool_cls.call_count == 1

    @patch(
        "mysql_to_sheets.core.connection_pool.MySQLConnectionPool",
        side_effect=mysql_connector.Error("fail"),
    )
    def test_raises_database_error(self, mock_pool_cls, mock_config):
        with pytest.raises(DatabaseError):
            get_connection_pool(mock_config)


class TestResetPool:
    @patch("mysql_to_sheets.core.connection_pool.MySQLConnectionPool")
    def test_reset_clears_cache(self, mock_pool_cls, mock_config):
        get_connection_pool(mock_config)
        reset_pool()
        get_connection_pool(mock_config)
        assert mock_pool_cls.call_count == 2


class TestGetPoolStats:
    def test_none_when_no_pool(self):
        assert get_pool_stats() is None

    @patch("mysql_to_sheets.core.connection_pool.MySQLConnectionPool")
    def test_returns_stats(self, mock_pool_cls, mock_config):
        mock_pool_cls.return_value.pool_name = "test"
        mock_pool_cls.return_value.pool_size = 5
        get_connection_pool(mock_config)
        stats = get_pool_stats()
        assert stats["pool_name"] == "test"
        assert stats["pool_size"] == 5


class TestPooledConnection:
    @patch("mysql_to_sheets.core.connection_pool.MySQLConnectionPool")
    def test_context_manager(self, mock_pool_cls, mock_config):
        mock_conn = MagicMock()
        mock_pool_cls.return_value.get_connection.return_value = mock_conn

        with pooled_connection(mock_config) as conn:
            assert conn is mock_conn

        mock_conn.close.assert_called_once()


class TestPooledConnectionClass:
    @patch("mysql_to_sheets.core.connection_pool.MySQLConnectionPool")
    def test_enter_exit(self, mock_pool_cls, mock_config):
        mock_conn = MagicMock()
        mock_pool_cls.return_value.get_connection.return_value = mock_conn

        pc = PooledConnection(mock_config)
        conn = pc.__enter__()
        assert conn is mock_conn
        pc.__exit__(None, None, None)
        mock_conn.close.assert_called_once()
