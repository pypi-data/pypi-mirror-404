"""Tests for history module."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mysql_to_sheets.core.history import (
    HistoryEntry,
    InMemoryHistoryRepository,
    SQLiteHistoryRepository,
    get_history_repository,
    reset_history_repository,
)


class TestHistoryEntry:
    """Tests for HistoryEntry dataclass."""

    def test_create_entry(self):
        """Test creating a history entry."""
        entry = HistoryEntry(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            success=True,
            rows_synced=100,
            columns=5,
            headers=["id", "name", "email"],
            message="Sync completed",
            sheet_id="abc123",
            worksheet="Sheet1",
            duration_ms=1500.5,
            source="cli",
        )

        assert entry.success is True
        assert entry.rows_synced == 100
        assert len(entry.headers) == 3

    def test_to_dict(self):
        """Test converting entry to dictionary."""
        entry = HistoryEntry(
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            success=True,
            rows_synced=100,
        )

        data = entry.to_dict()

        assert data["success"] is True
        assert data["rows_synced"] == 100
        assert "2024-01-15" in data["timestamp"]

    def test_from_dict(self):
        """Test creating entry from dictionary."""
        data = {
            "timestamp": "2024-01-15T10:30:00",
            "success": True,
            "rows_synced": 50,
            "message": "Test",
        }

        entry = HistoryEntry.from_dict(data)

        assert entry.success is True
        assert entry.rows_synced == 50
        assert entry.message == "Test"

    def test_from_dict_with_iso_timestamp(self):
        """Test parsing ISO timestamp with timezone."""
        data = {
            "timestamp": "2024-01-15T10:30:00Z",
            "success": True,
        }

        entry = HistoryEntry.from_dict(data)

        assert entry.timestamp.year == 2024
        assert entry.timestamp.month == 1


class TestInMemoryHistoryRepository:
    """Tests for InMemoryHistoryRepository."""

    def test_add_entry(self):
        """Test adding an entry."""
        repo = InMemoryHistoryRepository()

        entry = HistoryEntry(
            timestamp=datetime.now(timezone.utc),
            success=True,
            rows_synced=100,
        )

        result = repo.add(entry)

        assert result.id == 1
        assert repo.count() == 1

    def test_get_all_ordered(self):
        """Test entries are returned most recent first."""
        repo = InMemoryHistoryRepository()

        for i in range(3):
            repo.add(
                HistoryEntry(
                    timestamp=datetime.now(timezone.utc),
                    success=True,
                    rows_synced=i * 10,
                )
            )

        entries = repo.get_all()

        # Most recent (highest rows_synced) should be first
        assert entries[0].rows_synced == 20
        assert entries[2].rows_synced == 0

    def test_get_all_with_limit(self):
        """Test limiting results."""
        repo = InMemoryHistoryRepository()

        for i in range(10):
            repo.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=True))

        entries = repo.get_all(limit=5)

        assert len(entries) == 5

    def test_get_all_with_offset(self):
        """Test offset for pagination."""
        repo = InMemoryHistoryRepository()

        for i in range(10):
            repo.add(
                HistoryEntry(
                    timestamp=datetime.now(timezone.utc),
                    success=True,
                    rows_synced=i,
                )
            )

        entries = repo.get_all(offset=5)

        assert len(entries) == 5
        # After offset, should get entries 4, 3, 2, 1, 0
        assert entries[0].rows_synced == 4

    def test_get_by_id(self):
        """Test getting entry by ID."""
        repo = InMemoryHistoryRepository()

        entry = repo.add(
            HistoryEntry(
                timestamp=datetime.now(timezone.utc),
                success=True,
                message="Test entry",
            )
        )

        result = repo.get_by_id(entry.id)

        assert result is not None
        assert result.message == "Test entry"

    def test_get_by_id_not_found(self):
        """Test getting non-existent entry."""
        repo = InMemoryHistoryRepository()

        result = repo.get_by_id(999)

        assert result is None

    def test_get_by_request_id(self):
        """Test getting entry by request ID."""
        repo = InMemoryHistoryRepository()

        repo.add(
            HistoryEntry(
                timestamp=datetime.now(timezone.utc),
                success=True,
                request_id="req-123",
            )
        )

        result = repo.get_by_request_id("req-123")

        assert result is not None
        assert result.request_id == "req-123"

    def test_get_by_sheet_id(self):
        """Test filtering by sheet ID."""
        repo = InMemoryHistoryRepository()

        repo.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=True, sheet_id="sheet1"))
        repo.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=True, sheet_id="sheet2"))
        repo.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=True, sheet_id="sheet1"))

        entries = repo.get_by_sheet_id("sheet1")

        assert len(entries) == 2

    def test_clear(self):
        """Test clearing all entries."""
        repo = InMemoryHistoryRepository()

        for i in range(5):
            repo.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=True))

        deleted = repo.clear()

        assert deleted == 5
        assert repo.count() == 0

    def test_max_entries_limit(self):
        """Test max entries limit is enforced."""
        repo = InMemoryHistoryRepository(max_entries=5)

        for i in range(10):
            repo.add(
                HistoryEntry(
                    timestamp=datetime.now(timezone.utc),
                    success=True,
                    rows_synced=i,
                )
            )

        assert repo.count() == 5

        # Should have only the most recent 5
        entries = repo.get_all()
        assert entries[0].rows_synced == 9


class TestSQLiteHistoryRepository:
    """Tests for SQLiteHistoryRepository."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_history.db"

    def test_add_entry(self, temp_db):
        """Test adding an entry to SQLite."""
        repo = SQLiteHistoryRepository(str(temp_db))

        entry = HistoryEntry(
            timestamp=datetime.now(timezone.utc),
            success=True,
            rows_synced=100,
            headers=["id", "name"],
        )

        result = repo.add(entry)

        assert result.id is not None
        assert repo.count() == 1

    def test_persistence(self, temp_db):
        """Test entries persist across repository instances."""
        # Add entries
        repo1 = SQLiteHistoryRepository(str(temp_db))
        repo1.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=True))
        repo1.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=False))

        # New repository instance
        repo2 = SQLiteHistoryRepository(str(temp_db))

        assert repo2.count() == 2

    def test_get_all_ordered(self, temp_db):
        """Test entries are returned most recent first."""
        repo = SQLiteHistoryRepository(str(temp_db))

        import time

        for i in range(3):
            repo.add(
                HistoryEntry(
                    timestamp=datetime.now(timezone.utc),
                    success=True,
                    rows_synced=i * 10,
                )
            )
            time.sleep(0.01)  # Ensure different timestamps

        entries = repo.get_all()

        assert entries[0].rows_synced == 20  # Most recent

    def test_get_by_id(self, temp_db):
        """Test getting entry by ID."""
        repo = SQLiteHistoryRepository(str(temp_db))

        entry = repo.add(
            HistoryEntry(
                timestamp=datetime.now(timezone.utc),
                success=True,
                message="Test",
            )
        )

        result = repo.get_by_id(entry.id)

        assert result is not None
        assert result.message == "Test"

    def test_get_by_sheet_id(self, temp_db):
        """Test filtering by sheet ID."""
        repo = SQLiteHistoryRepository(str(temp_db))

        repo.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=True, sheet_id="A"))
        repo.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=True, sheet_id="B"))
        repo.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=True, sheet_id="A"))

        entries = repo.get_by_sheet_id("A")

        assert len(entries) == 2

    def test_headers_json_serialization(self, temp_db):
        """Test headers are properly serialized and deserialized."""
        repo = SQLiteHistoryRepository(str(temp_db))

        entry = repo.add(
            HistoryEntry(
                timestamp=datetime.now(timezone.utc),
                success=True,
                headers=["id", "name", "email"],
            )
        )

        result = repo.get_by_id(entry.id)

        assert result.headers == ["id", "name", "email"]

    def test_clear(self, temp_db):
        """Test clearing all entries."""
        repo = SQLiteHistoryRepository(str(temp_db))

        for i in range(5):
            repo.add(HistoryEntry(timestamp=datetime.now(timezone.utc), success=True))

        deleted = repo.clear()

        assert deleted == 5
        assert repo.count() == 0


class TestGetHistoryRepository:
    """Tests for get_history_repository factory function."""

    def setup_method(self):
        """Reset repository singleton."""
        reset_history_repository()

    def test_memory_backend(self):
        """Test creating in-memory repository."""
        repo = get_history_repository(backend="memory")

        assert isinstance(repo, InMemoryHistoryRepository)

    def test_sqlite_backend(self):
        """Test creating SQLite repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            reset_history_repository()
            repo = get_history_repository(backend="sqlite", db_path=str(db_path))

            assert isinstance(repo, SQLiteHistoryRepository)

    def test_invalid_backend(self):
        """Test error for invalid backend."""
        with pytest.raises(ValueError, match="Unknown history backend"):
            get_history_repository(backend="invalid")

    def test_sqlite_requires_path(self):
        """Test SQLite backend requires db_path."""
        with pytest.raises(ValueError, match="db_path is required"):
            get_history_repository(backend="sqlite")

    def test_singleton_behavior(self):
        """Test repository is reused."""
        repo1 = get_history_repository(backend="memory")
        repo2 = get_history_repository()

        assert repo1 is repo2
