"""Tests for the metadata database engine factory."""

import os
import tempfile
from unittest.mock import patch

from mysql_to_sheets.core.metadata_db import (
    _mask_url,
    _resolve_database_url,
    get_engine_for_jobs,
    get_metadata_db_type,
    get_metadata_engine,
    reset_engines,
)


class TestGetMetadataEngine:
    """Tests for get_metadata_engine function."""

    def setup_method(self):
        """Reset engines before each test."""
        reset_engines()

    def teardown_method(self):
        """Clean up after each test."""
        reset_engines()

    def test_sqlite_engine_from_url(self):
        """Test creating a SQLite engine from URL."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = get_metadata_engine(db_url=f"sqlite:///{db_path}")

            assert engine is not None
            assert "sqlite" in str(engine.url)
        finally:
            os.unlink(db_path)

    def test_engine_caching(self):
        """Test that engines are cached by URL."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            url = f"sqlite:///{db_path}"
            engine1 = get_metadata_engine(db_url=url)
            engine2 = get_metadata_engine(db_url=url)

            assert engine1 is engine2
        finally:
            os.unlink(db_path)

    def test_different_urls_different_engines(self):
        """Test that different URLs create different engines."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f1:
            db_path1 = f1.name
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f2:
            db_path2 = f2.name

        try:
            engine1 = get_metadata_engine(db_url=f"sqlite:///{db_path1}")
            engine2 = get_metadata_engine(db_url=f"sqlite:///{db_path2}")

            assert engine1 is not engine2
        finally:
            os.unlink(db_path1)
            os.unlink(db_path2)

    def test_config_sqlite_backend(self):
        """Test creating engine from config with SQLite."""
        from mysql_to_sheets.core.config import Config

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            config = Config(
                metadata_db_type="sqlite",
                tenant_db_path=db_path,
            )

            engine = get_metadata_engine(config=config)

            assert engine is not None
            assert "sqlite" in str(engine.url)
        finally:
            os.unlink(db_path)

    def test_config_postgres_backend(self):
        """Test config with PostgreSQL URL."""
        from mysql_to_sheets.core.config import Config

        config = Config(
            metadata_db_type="postgres",
            metadata_db_url="postgresql://user:pass@localhost:5432/testdb",
        )

        # Note: This test doesn't actually connect - just verifies URL resolution
        url = _resolve_database_url(config, None)

        assert url == "postgresql://user:pass@localhost:5432/testdb"

    def test_env_var_fallback(self):
        """Test falling back to environment variables."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            with patch.dict(os.environ, {"METADATA_DB_URL": f"sqlite:///{db_path}"}):
                url = _resolve_database_url(None, None)

            assert db_path in url
        finally:
            os.unlink(db_path)

    def test_explicit_url_takes_precedence(self):
        """Test that explicit URL takes precedence over config."""
        from mysql_to_sheets.core.config import Config

        config = Config(
            metadata_db_type="postgres",
            metadata_db_url="postgresql://user:pass@host/db1",
        )

        url = _resolve_database_url(config, "postgresql://other:pass@host/db2")

        assert url == "postgresql://other:pass@host/db2"


class TestGetMetadataDbType:
    """Tests for get_metadata_db_type function."""

    def test_sqlite_type(self):
        """Test detecting SQLite type."""
        assert get_metadata_db_type("sqlite:///test.db") == "sqlite"

    def test_postgres_type(self):
        """Test detecting PostgreSQL type."""
        assert get_metadata_db_type("postgresql://localhost/db") == "postgres"
        assert get_metadata_db_type("postgres://localhost/db") == "postgres"

    def test_unknown_type(self):
        """Test unknown database type."""
        assert get_metadata_db_type("mysql://localhost/db") == "unknown"


class TestMaskUrl:
    """Tests for URL masking function."""

    def test_mask_password(self):
        """Test that passwords are masked."""
        url = "postgresql://user:secret123@localhost:5432/db"
        masked = _mask_url(url)

        assert "secret123" not in masked
        assert "***" in masked
        assert "user" in masked

    def test_no_password(self):
        """Test URL without password."""
        url = "sqlite:///test.db"
        masked = _mask_url(url)

        assert masked == url


class TestGetEngineForJobs:
    """Tests for get_engine_for_jobs convenience function."""

    def setup_method(self):
        """Reset engines before each test."""
        reset_engines()

    def teardown_method(self):
        """Clean up after each test."""
        reset_engines()

    def test_with_file_path(self):
        """Test with a file path (backward compatibility)."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = get_engine_for_jobs(db_path=db_path)

            assert engine is not None
            assert "sqlite" in str(engine.url)
        finally:
            os.unlink(db_path)

    def test_with_url(self):
        """Test with an explicit URL."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = get_engine_for_jobs(db_path=f"sqlite:///{db_path}")

            assert engine is not None
            assert "sqlite" in str(engine.url)
        finally:
            os.unlink(db_path)


class TestResetEngines:
    """Tests for engine cleanup."""

    def test_reset_clears_cache(self):
        """Test that reset clears the engine cache."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine1 = get_metadata_engine(db_url=f"sqlite:///{db_path}")
            reset_engines()
            engine2 = get_metadata_engine(db_url=f"sqlite:///{db_path}")

            # After reset, we should get a new engine
            assert engine1 is not engine2
        finally:
            os.unlink(db_path)
