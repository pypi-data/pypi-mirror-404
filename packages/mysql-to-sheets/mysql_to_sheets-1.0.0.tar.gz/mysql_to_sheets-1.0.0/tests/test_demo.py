"""Tests for core/demo.py — demo SQLite database for evaluation."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from mysql_to_sheets.core.demo import (
    SAMPLE_CUSTOMERS,
    SAMPLE_ORDERS,
    SAMPLE_PRODUCTS,
    cleanup_demo_database,
    create_demo_database,
    demo_database_exists,
    get_demo_queries,
)


@pytest.fixture
def demo_dir(tmp_path: Path):
    """Redirect demo DB to a temp directory."""
    with patch("mysql_to_sheets.core.demo.get_demo_db_path", return_value=tmp_path / "demo.db"):
        yield tmp_path


class TestCreateDemoDatabase:
    def test_creates_db(self, demo_dir):
        db_path = create_demo_database()
        assert db_path.exists()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sample_customers")
        assert cursor.fetchone()[0] == len(SAMPLE_CUSTOMERS)
        cursor.execute("SELECT COUNT(*) FROM sample_products")
        assert cursor.fetchone()[0] == len(SAMPLE_PRODUCTS)
        cursor.execute("SELECT COUNT(*) FROM sample_orders")
        assert cursor.fetchone()[0] == len(SAMPLE_ORDERS)
        conn.close()

    def test_skips_if_exists(self, demo_dir):
        path1 = create_demo_database()
        path2 = create_demo_database()
        assert path1 == path2

    def test_force_recreate(self, demo_dir):
        create_demo_database()
        path = create_demo_database(force=True)
        assert path.exists()


class TestCleanupDemoDatabase:
    def test_removes_existing(self, demo_dir):
        create_demo_database()
        assert cleanup_demo_database() is True
        assert not (demo_dir / "demo.db").exists()

    def test_returns_false_when_missing(self, demo_dir):
        assert cleanup_demo_database() is False


class TestDemoDatabaseExists:
    def test_false_initially(self, demo_dir):
        assert demo_database_exists() is False

    def test_true_after_create(self, demo_dir):
        create_demo_database()
        assert demo_database_exists() is True


class TestGetDemoQueries:
    def test_returns_list(self):
        queries = get_demo_queries()
        assert len(queries) >= 5
        for q in queries:
            assert "name" in q
            assert "query" in q
            assert q["query"].strip().upper().startswith("SELECT")
