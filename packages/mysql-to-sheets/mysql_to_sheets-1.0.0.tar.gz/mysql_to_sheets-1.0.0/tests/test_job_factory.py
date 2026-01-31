"""Tests for the job queue backend factory."""

import os
import tempfile
from unittest.mock import patch

import pytest

from mysql_to_sheets.core.job_backend import JobQueueBackend
from mysql_to_sheets.core.job_factory import (
    _resolve_backend_type,
    get_backend_type,
    get_job_backend,
    reset_job_backend,
)


class TestGetJobBackend:
    """Tests for get_job_backend factory function."""

    def setup_method(self):
        """Reset backend before each test."""
        reset_job_backend()

    def teardown_method(self):
        """Clean up after each test."""
        reset_job_backend()

    def test_default_sqlite_backend(self):
        """Test that SQLite is the default backend."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            backend = get_job_backend(db_path=db_path)

            assert backend is not None
            assert isinstance(backend, JobQueueBackend)
            assert get_backend_type() == "sqlite"
        finally:
            os.unlink(db_path)

    def test_explicit_sqlite_backend(self):
        """Test explicitly requesting SQLite backend."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            backend = get_job_backend(backend_type="sqlite", db_path=db_path)

            assert get_backend_type() == "sqlite"
        finally:
            os.unlink(db_path)

    def test_explicit_redis_backend(self):
        """Test explicitly requesting Redis backend."""
        try:
            import fakeredis
        except ImportError:
            pytest.skip("fakeredis not installed")

        # Mock the redis module to use fakeredis
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        with patch("mysql_to_sheets.core.redis_job_queue.redis") as mock_redis:
            mock_redis.from_url.return_value = fake_redis

            backend = get_job_backend(
                backend_type="redis",
                redis_url="redis://localhost:6379/0",
            )

            assert get_backend_type() == "redis"

    def test_backend_caching(self):
        """Test that backends are cached."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            backend1 = get_job_backend(db_path=db_path)
            backend2 = get_job_backend(db_path=db_path)

            assert backend1 is backend2
        finally:
            os.unlink(db_path)

    def test_config_determines_backend(self):
        """Test that config determines backend type."""
        from mysql_to_sheets.core.config import Config

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            config = Config(
                job_queue_backend="sqlite",
                tenant_db_path=db_path,
            )

            backend = get_job_backend(config=config)

            assert get_backend_type() == "sqlite"
        finally:
            os.unlink(db_path)


class TestResolveBackendType:
    """Tests for backend type resolution."""

    def test_explicit_type_takes_precedence(self):
        """Test that explicit type takes precedence over config."""
        from mysql_to_sheets.core.config import Config

        config = Config(job_queue_backend="redis")
        result = _resolve_backend_type(config, "sqlite")

        assert result == "sqlite"

    def test_config_type(self):
        """Test using config to determine type."""
        from mysql_to_sheets.core.config import Config

        config = Config(job_queue_backend="redis")
        result = _resolve_backend_type(config, None)

        assert result == "redis"

    def test_env_var_fallback(self):
        """Test falling back to environment variable."""
        with patch.dict(os.environ, {"JOB_QUEUE_BACKEND": "redis"}):
            result = _resolve_backend_type(None, None)

        assert result == "redis"

    def test_default_sqlite(self):
        """Test default is SQLite."""
        with patch.dict(os.environ, clear=True):
            os.environ.pop("JOB_QUEUE_BACKEND", None)
            result = _resolve_backend_type(None, None)

        assert result == "sqlite"

    def test_case_insensitive(self):
        """Test that backend type is case insensitive."""
        result = _resolve_backend_type(None, "REDIS")
        assert result == "redis"

        result = _resolve_backend_type(None, "SQLite")
        assert result == "sqlite"


class TestResetJobBackend:
    """Tests for backend reset."""

    def test_reset_clears_cache(self):
        """Test that reset clears the cached backend."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            backend1 = get_job_backend(db_path=db_path)
            reset_job_backend()
            backend2 = get_job_backend(db_path=db_path)

            assert backend1 is not backend2
        finally:
            os.unlink(db_path)

    def test_reset_clears_type(self):
        """Test that reset clears the backend type."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            get_job_backend(db_path=db_path)
            assert get_backend_type() == "sqlite"

            reset_job_backend()
            assert get_backend_type() is None
        finally:
            os.unlink(db_path)


class TestBackendInterface:
    """Tests to verify backends implement the interface correctly."""

    def test_sqlite_backend_interface(self):
        """Test that SQLite backend implements required methods."""
        from mysql_to_sheets.core.sqlite_job_queue import SQLiteJobQueue

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            backend = SQLiteJobQueue(db_path=db_path)

            # Verify all required methods exist
            assert hasattr(backend, "create")
            assert hasattr(backend, "get_by_id")
            assert hasattr(backend, "get_next_pending")
            assert hasattr(backend, "claim_job")
            assert hasattr(backend, "complete")
            assert hasattr(backend, "fail")
            assert hasattr(backend, "cancel")
            assert hasattr(backend, "retry")
            assert hasattr(backend, "release_job")
            assert hasattr(backend, "heartbeat")
            assert hasattr(backend, "get_all")
            assert hasattr(backend, "count")
            assert hasattr(backend, "cleanup_stale")
            assert hasattr(backend, "delete_old")
            assert hasattr(backend, "get_stats")
        finally:
            os.unlink(db_path)

    def test_redis_backend_interface(self):
        """Test that Redis backend implements required methods."""
        try:
            import fakeredis
        except ImportError:
            pytest.skip("fakeredis not installed")

        from mysql_to_sheets.core.redis_job_queue import RedisJobQueue

        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        backend = RedisJobQueue(redis_client=fake_redis)

        # Verify all required methods exist
        assert hasattr(backend, "create")
        assert hasattr(backend, "get_by_id")
        assert hasattr(backend, "get_next_pending")
        assert hasattr(backend, "claim_job")
        assert hasattr(backend, "complete")
        assert hasattr(backend, "fail")
        assert hasattr(backend, "cancel")
        assert hasattr(backend, "retry")
        assert hasattr(backend, "release_job")
        assert hasattr(backend, "heartbeat")
        assert hasattr(backend, "get_all")
        assert hasattr(backend, "count")
        assert hasattr(backend, "cleanup_stale")
        assert hasattr(backend, "delete_old")
        assert hasattr(backend, "get_stats")
