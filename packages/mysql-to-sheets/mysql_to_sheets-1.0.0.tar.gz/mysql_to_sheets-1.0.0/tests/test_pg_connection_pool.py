"""Tests for PostgreSQL connection pooling in core/database/postgres.py."""

from unittest.mock import MagicMock, patch

import pytest

# Guard: psycopg2 may not be installed in all environments
psycopg2 = pytest.importorskip("psycopg2")

from mysql_to_sheets.core.database.postgres import (
    get_pg_pool,
    get_pg_pool_stats,
    pg_pooled_connection,
    reset_pg_pool,
)
from mysql_to_sheets.core.exceptions import DatabaseError


@pytest.fixture(autouse=True)
def _reset_global_pg_pool():
    """Ensure global PG pool is reset between tests."""
    reset_pg_pool()
    yield
    reset_pg_pool()


@pytest.fixture
def pg_config():
    """Minimal config object for PostgreSQL pooling tests."""
    config = MagicMock()
    config.db_host = "localhost"
    config.db_port = 5432
    config.db_user = "test_user"
    config.db_password = "test_pass"
    config.db_name = "test_db"
    config.db_connect_timeout = 10
    config.db_pool_size = 5
    config.db_ssl_mode = None
    config.db_ssl_ca = None
    return config


class TestGetPgPool:
    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_creates_pool(self, mock_pool_cls, pg_config):
        mock_pool_cls.return_value.closed = False
        pool = get_pg_pool(pg_config)
        mock_pool_cls.assert_called_once()
        assert pool is mock_pool_cls.return_value

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_returns_cached_pool(self, mock_pool_cls, pg_config):
        mock_pool_cls.return_value.closed = False
        pool1 = get_pg_pool(pg_config)
        pool2 = get_pg_pool(pg_config)
        assert pool1 is pool2
        assert mock_pool_cls.call_count == 1

    @patch(
        "psycopg2.pool.ThreadedConnectionPool",
        side_effect=psycopg2.Error("fail"),
    )
    def test_raises_database_error(self, mock_pool_cls, pg_config):
        with pytest.raises(DatabaseError):
            get_pg_pool(pg_config)

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_custom_pool_size(self, mock_pool_cls, pg_config):
        mock_pool_cls.return_value.closed = False
        get_pg_pool(pg_config, pool_size=10)
        call_kwargs = mock_pool_cls.call_args
        assert call_kwargs[1]["maxconn"] == 10


class TestResetPgPool:
    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_reset_clears_cache(self, mock_pool_cls, pg_config):
        mock_pool_cls.return_value.closed = False
        get_pg_pool(pg_config)
        reset_pg_pool()
        mock_pool_cls.return_value.closed = True  # After reset, pool is gone
        # Need a fresh mock for the next pool
        mock_pool_cls.return_value = MagicMock(closed=False)
        get_pg_pool(pg_config)
        assert mock_pool_cls.call_count == 2


class TestGetPgPoolStats:
    def test_none_when_no_pool(self):
        assert get_pg_pool_stats() is None

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_returns_stats(self, mock_pool_cls, pg_config):
        mock_pool_cls.return_value.closed = False
        mock_pool_cls.return_value.minconn = 1
        mock_pool_cls.return_value.maxconn = 5
        get_pg_pool(pg_config)
        stats = get_pg_pool_stats()
        assert stats["pool_minconn"] == 1
        assert stats["pool_maxconn"] == 5


class TestPgPooledConnection:
    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_context_manager(self, mock_pool_cls, pg_config):
        mock_conn = MagicMock()
        mock_pool = MagicMock(closed=False)
        mock_pool.getconn.return_value = mock_conn
        mock_pool_cls.return_value = mock_pool

        with pg_pooled_connection(pg_config) as conn:
            assert conn is mock_conn

        mock_pool.putconn.assert_called_once_with(mock_conn)

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_returns_conn_on_exception(self, mock_pool_cls, pg_config):
        mock_conn = MagicMock()
        mock_pool = MagicMock(closed=False)
        mock_pool.getconn.return_value = mock_conn
        mock_pool_cls.return_value = mock_pool

        with pytest.raises(ValueError):
            with pg_pooled_connection(pg_config) as _conn:
                raise ValueError("test error")

        mock_pool.putconn.assert_called_once_with(mock_conn)
