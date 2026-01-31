"""Tests for snapshot model and service."""

import hashlib
import json
import tempfile
import zlib
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.models.snapshots import (
    Snapshot,
    SnapshotRepository,
    reset_snapshot_repository,
)


class TestSnapshot:
    """Tests for Snapshot dataclass."""

    def test_create_snapshot(self):
        """Test creating a snapshot."""
        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=100,
            column_count=5,
            size_bytes=1024,
            checksum="abc123def456",
            headers=["id", "name", "email"],
        )

        assert snapshot.sheet_id == "abc123"
        assert snapshot.row_count == 100
        assert len(snapshot.headers) == 3

    def test_to_dict(self):
        """Test converting snapshot to dictionary."""
        snapshot = Snapshot(
            id=1,
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=100,
            column_count=5,
            size_bytes=1024,
            checksum="abc123def456",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )

        data = snapshot.to_dict()

        assert data["id"] == 1
        assert data["sheet_id"] == "abc123"
        assert "2024-01-15" in data["created_at"]

    def test_from_dict(self):
        """Test creating snapshot from dictionary."""
        data = {
            "id": 1,
            "organization_id": 1,
            "sheet_id": "abc123",
            "worksheet_name": "Sheet1",
            "row_count": 100,
            "column_count": 5,
            "size_bytes": 1024,
            "checksum": "abc123",
            "created_at": "2024-01-15T10:30:00",
            "headers": ["id", "name"],
        }

        snapshot = Snapshot.from_dict(data)

        assert snapshot.id == 1
        assert snapshot.row_count == 100
        assert snapshot.headers == ["id", "name"]

    def test_get_data(self):
        """Test decompressing snapshot data."""
        headers = ["id", "name"]
        rows = [["1", "Alice"], ["2", "Bob"]]
        data = {"headers": headers, "rows": rows}
        compressed = zlib.compress(json.dumps(data).encode("utf-8"))

        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=2,
            column_count=2,
            size_bytes=len(compressed),
            checksum=hashlib.sha256(compressed).hexdigest(),
            data_compressed=compressed,
        )

        result_headers, result_rows = snapshot.get_data()

        assert result_headers == headers
        assert result_rows == rows

    def test_get_data_not_loaded(self):
        """Test error when data not loaded."""
        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=2,
            column_count=2,
            size_bytes=0,
            checksum="abc",
            data_compressed=None,
        )

        with pytest.raises(ValueError, match="data not loaded"):
            snapshot.get_data()

    def test_verify_checksum_valid(self):
        """Test checksum verification passes for valid data."""
        data = b"test data"
        compressed = zlib.compress(data)
        checksum = hashlib.sha256(compressed).hexdigest()

        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=0,
            column_count=0,
            size_bytes=len(compressed),
            checksum=checksum,
            data_compressed=compressed,
        )

        assert snapshot.verify_checksum() is True

    def test_verify_checksum_invalid(self):
        """Test checksum verification fails for corrupted data."""
        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=0,
            column_count=0,
            size_bytes=10,
            checksum="invalid_checksum",
            data_compressed=b"some data",
        )

        assert snapshot.verify_checksum() is False


class TestSnapshotRepository:
    """Tests for SnapshotRepository."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        reset_snapshot_repository()
        with tempfile.TemporaryDirectory() as tmpdir:
            yield str(Path(tmpdir) / "test_snapshots.db")

    def test_add_snapshot(self, temp_db):
        """Test adding a snapshot."""
        repo = SnapshotRepository(temp_db)

        headers = ["id", "name"]
        rows = [["1", "Alice"]]
        data = {"headers": headers, "rows": rows}
        compressed = zlib.compress(json.dumps(data).encode("utf-8"))
        checksum = hashlib.sha256(compressed).hexdigest()

        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=1,
            column_count=2,
            size_bytes=len(compressed),
            checksum=checksum,
            data_compressed=compressed,
            headers=headers,
        )

        result = repo.add(snapshot)

        assert result.id is not None
        assert result.created_at is not None

    def test_get_snapshot(self, temp_db):
        """Test retrieving a snapshot by ID."""
        repo = SnapshotRepository(temp_db)

        compressed = zlib.compress(b'{"headers":[],"rows":[]}')
        checksum = hashlib.sha256(compressed).hexdigest()

        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=0,
            column_count=0,
            size_bytes=len(compressed),
            checksum=checksum,
            data_compressed=compressed,
        )

        added = repo.add(snapshot)
        result = repo.get(added.id, organization_id=1, include_data=False)

        assert result is not None
        assert result.sheet_id == "abc123"

    def test_get_snapshot_with_data(self, temp_db):
        """Test retrieving snapshot with compressed data."""
        repo = SnapshotRepository(temp_db)

        compressed = zlib.compress(b'{"headers":["id"],"rows":[["1"]]}')
        checksum = hashlib.sha256(compressed).hexdigest()

        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=1,
            column_count=1,
            size_bytes=len(compressed),
            checksum=checksum,
            data_compressed=compressed,
        )

        added = repo.add(snapshot)
        result = repo.get(added.id, organization_id=1, include_data=True)

        assert result is not None
        assert result.data_compressed is not None

    def test_get_snapshot_wrong_org(self, temp_db):
        """Test access control by organization."""
        repo = SnapshotRepository(temp_db)

        compressed = zlib.compress(b'{"headers":[],"rows":[]}')
        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=0,
            column_count=0,
            size_bytes=len(compressed),
            checksum=hashlib.sha256(compressed).hexdigest(),
            data_compressed=compressed,
        )

        added = repo.add(snapshot)
        result = repo.get(added.id, organization_id=2)  # Different org

        assert result is None

    def test_list_snapshots(self, temp_db):
        """Test listing snapshots."""
        repo = SnapshotRepository(temp_db)

        for i in range(5):
            compressed = zlib.compress(b'{"headers":[],"rows":[]}')
            snapshot = Snapshot(
                sheet_id="abc123",
                worksheet_name="Sheet1",
                organization_id=1,
                row_count=i,
                column_count=0,
                size_bytes=len(compressed),
                checksum=hashlib.sha256(compressed).hexdigest(),
                data_compressed=compressed,
            )
            repo.add(snapshot)

        results = repo.list(organization_id=1)

        assert len(results) == 5

    def test_list_snapshots_with_filter(self, temp_db):
        """Test filtering snapshots by sheet ID."""
        repo = SnapshotRepository(temp_db)

        for sheet_id in ["sheet1", "sheet2", "sheet1"]:
            compressed = zlib.compress(b'{"headers":[],"rows":[]}')
            snapshot = Snapshot(
                sheet_id=sheet_id,
                worksheet_name="Sheet1",
                organization_id=1,
                row_count=0,
                column_count=0,
                size_bytes=len(compressed),
                checksum=hashlib.sha256(compressed).hexdigest(),
                data_compressed=compressed,
            )
            repo.add(snapshot)

        results = repo.list(organization_id=1, sheet_id="sheet1")

        assert len(results) == 2

    def test_delete_snapshot(self, temp_db):
        """Test deleting a snapshot."""
        repo = SnapshotRepository(temp_db)

        compressed = zlib.compress(b'{"headers":[],"rows":[]}')
        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=0,
            column_count=0,
            size_bytes=len(compressed),
            checksum=hashlib.sha256(compressed).hexdigest(),
            data_compressed=compressed,
        )

        added = repo.add(snapshot)
        deleted = repo.delete(added.id, organization_id=1)

        assert deleted is True
        assert repo.get(added.id, organization_id=1) is None

    def test_delete_oldest(self, temp_db):
        """Test deleting oldest snapshots beyond retention count."""
        repo = SnapshotRepository(temp_db)

        for i in range(10):
            compressed = zlib.compress(b'{"headers":[],"rows":[]}')
            snapshot = Snapshot(
                sheet_id="abc123",
                worksheet_name="Sheet1",
                organization_id=1,
                row_count=i,
                column_count=0,
                size_bytes=len(compressed),
                checksum=hashlib.sha256(compressed).hexdigest(),
                data_compressed=compressed,
            )
            repo.add(snapshot)

        deleted = repo.delete_oldest(
            organization_id=1,
            sheet_id="abc123",
            keep_count=5,
        )

        assert deleted == 5
        assert repo.count(organization_id=1) == 5

    def test_get_total_size(self, temp_db):
        """Test calculating total storage size."""
        repo = SnapshotRepository(temp_db)

        for i in range(3):
            compressed = zlib.compress(b'{"headers":[],"rows":[]}')
            snapshot = Snapshot(
                sheet_id="abc123",
                worksheet_name="Sheet1",
                organization_id=1,
                row_count=0,
                column_count=0,
                size_bytes=100,  # Fixed size for test
                checksum=hashlib.sha256(compressed).hexdigest(),
                data_compressed=compressed,
            )
            repo.add(snapshot)

        total = repo.get_total_size(organization_id=1)

        assert total == 300

    def test_get_stats(self, temp_db):
        """Test getting statistics."""
        repo = SnapshotRepository(temp_db)

        for sheet_id in ["sheet1", "sheet2", "sheet1"]:
            compressed = zlib.compress(b'{"headers":[],"rows":[]}')
            snapshot = Snapshot(
                sheet_id=sheet_id,
                worksheet_name="Sheet1",
                organization_id=1,
                row_count=0,
                column_count=0,
                size_bytes=100,
                checksum=hashlib.sha256(compressed).hexdigest(),
                data_compressed=compressed,
            )
            repo.add(snapshot)

        stats = repo.get_stats(organization_id=1)

        assert stats["total_snapshots"] == 3
        assert stats["total_size_bytes"] == 300
        assert "sheet1" in stats["by_sheet"]
        assert stats["by_sheet"]["sheet1"]["count"] == 2


class TestSnapshotService:
    """Tests for snapshot service functions."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        reset_snapshot_repository()
        with tempfile.TemporaryDirectory() as tmpdir:
            yield str(Path(tmpdir) / "test_snapshots.db")

    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = MagicMock()
        config.google_sheet_id = "test_sheet_id"
        config.google_worksheet_name = "Sheet1"
        config.service_account_file = "/path/to/sa.json"
        config.tenant_db_path = "/tmp/test.db"
        return config

    @patch("mysql_to_sheets.core.history.snapshots.gspread")
    def test_create_snapshot(self, mock_gspread, temp_db, mock_config):
        """Test creating a snapshot from sheet data."""
        from mysql_to_sheets.core.snapshots import create_snapshot

        # Setup mock
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_values.return_value = [
            ["id", "name", "email"],
            ["1", "Alice", "alice@example.com"],
            ["2", "Bob", "bob@example.com"],
        ]
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_gc = MagicMock()
        mock_gc.open_by_key.return_value = mock_spreadsheet
        mock_gspread.service_account.return_value = mock_gc

        mock_config.tenant_db_path = temp_db

        snapshot = create_snapshot(
            config=mock_config,
            organization_id=1,
            db_path=temp_db,
        )

        assert snapshot.id is not None
        assert snapshot.row_count == 2
        assert snapshot.column_count == 3
        assert snapshot.headers == ["id", "name", "email"]

    def test_list_snapshots(self, temp_db):
        """Test listing snapshots."""
        from mysql_to_sheets.core.snapshots import list_snapshots

        repo = SnapshotRepository(temp_db)

        for i in range(5):
            compressed = zlib.compress(b'{"headers":[],"rows":[]}')
            snapshot = Snapshot(
                sheet_id="abc123",
                worksheet_name="Sheet1",
                organization_id=1,
                row_count=i,
                column_count=0,
                size_bytes=len(compressed),
                checksum=hashlib.sha256(compressed).hexdigest(),
                data_compressed=compressed,
            )
            repo.add(snapshot)

        results = list_snapshots(
            organization_id=1,
            db_path=temp_db,
            limit=3,
        )

        assert len(results) == 3

    def test_delete_snapshot(self, temp_db):
        """Test deleting a snapshot."""
        from mysql_to_sheets.core.snapshots import delete_snapshot

        repo = SnapshotRepository(temp_db)

        compressed = zlib.compress(b'{"headers":[],"rows":[]}')
        snapshot = Snapshot(
            sheet_id="abc123",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=0,
            column_count=0,
            size_bytes=len(compressed),
            checksum=hashlib.sha256(compressed).hexdigest(),
            data_compressed=compressed,
        )
        added = repo.add(snapshot)

        deleted = delete_snapshot(
            snapshot_id=added.id,
            organization_id=1,
            db_path=temp_db,
        )

        assert deleted is True
