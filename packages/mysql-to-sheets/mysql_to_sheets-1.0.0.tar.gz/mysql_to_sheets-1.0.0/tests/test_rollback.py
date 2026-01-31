"""Tests for rollback and retention functionality."""

import hashlib
import json
import tempfile
import zlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.rollback import (
    RollbackPreview,
    RollbackResult,
    can_rollback,
    preview_rollback,
    rollback_to_snapshot,
)
from mysql_to_sheets.core.snapshot_retention import (
    CleanupResult,
    RetentionConfig,
    StorageStats,
    cleanup_old_snapshots,
    get_retention_config_from_config,
    should_create_snapshot,
)
from mysql_to_sheets.models.snapshots import (
    Snapshot,
    SnapshotRepository,
    reset_snapshot_repository,
)


class TestRollbackResult:
    """Tests for RollbackResult dataclass."""

    def test_create_success_result(self):
        """Test creating a successful rollback result."""
        result = RollbackResult(
            success=True,
            snapshot_id=1,
            rows_restored=100,
            columns_restored=5,
            backup_snapshot_id=2,
            message="Rollback completed",
        )

        assert result.success is True
        assert result.rows_restored == 100
        assert result.backup_snapshot_id == 2

    def test_create_failure_result(self):
        """Test creating a failed rollback result."""
        result = RollbackResult(
            success=False,
            snapshot_id=1,
            error="Sheet not accessible",
            message="Rollback failed",
        )

        assert result.success is False
        assert result.error == "Sheet not accessible"

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = RollbackResult(
            success=True,
            snapshot_id=1,
            rows_restored=50,
            columns_restored=3,
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["rows_restored"] == 50


class TestRollbackPreview:
    """Tests for RollbackPreview dataclass."""

    def test_create_preview(self):
        """Test creating a rollback preview."""
        preview = RollbackPreview(
            snapshot_id=1,
            snapshot_created_at="2024-01-15T10:30:00",
            current_row_count=100,
            snapshot_row_count=80,
            current_column_count=5,
            snapshot_column_count=5,
            message="Preview generated",
        )

        assert preview.snapshot_id == 1
        assert preview.current_row_count == 100

    def test_to_dict(self):
        """Test converting preview to dictionary."""
        preview = RollbackPreview(
            snapshot_id=1,
            current_row_count=100,
            snapshot_row_count=80,
        )

        data = preview.to_dict()

        assert data["snapshot_id"] == 1
        assert data["current_row_count"] == 100


class TestRetentionConfig:
    """Tests for RetentionConfig dataclass."""

    def test_default_values(self):
        """Test default retention config values."""
        config = RetentionConfig()

        assert config.retention_count == 10
        assert config.retention_days == 30
        assert config.max_size_mb == 50

    def test_max_size_bytes(self):
        """Test max size in bytes property."""
        config = RetentionConfig(max_size_mb=10)

        assert config.max_size_bytes == 10 * 1024 * 1024


class TestCleanupResult:
    """Tests for CleanupResult dataclass."""

    def test_create_result(self):
        """Test creating a cleanup result."""
        result = CleanupResult(
            deleted_by_count=5,
            deleted_by_age=3,
            total_deleted=8,
            sheets_processed=2,
            message="Cleaned up 8 snapshots",
        )

        assert result.total_deleted == 8
        assert result.sheets_processed == 2


class TestStorageStats:
    """Tests for StorageStats dataclass."""

    def test_create_stats(self):
        """Test creating storage stats."""
        stats = StorageStats(
            total_snapshots=10,
            total_size_bytes=1024 * 1024,  # 1 MB
        )

        assert stats.total_snapshots == 10
        assert stats.total_size_mb == 1.0

    def test_to_dict(self):
        """Test converting stats to dictionary."""
        stats = StorageStats(
            total_snapshots=5,
            total_size_bytes=512 * 1024,  # 0.5 MB
        )

        data = stats.to_dict()

        assert data["total_snapshots"] == 5
        assert data["total_size_mb"] == 0.5


class TestShouldCreateSnapshot:
    """Tests for should_create_snapshot function."""

    def test_under_limit(self):
        """Test snapshot creation allowed under size limit."""
        config = RetentionConfig(max_size_mb=50)

        should_create, reason = should_create_snapshot(
            estimated_size_bytes=10 * 1024 * 1024,  # 10 MB
            retention_config=config,
        )

        assert should_create is True
        assert "within limits" in reason

    def test_over_limit(self):
        """Test snapshot creation skipped over size limit."""
        config = RetentionConfig(max_size_mb=5)

        should_create, reason = should_create_snapshot(
            estimated_size_bytes=10 * 1024 * 1024,  # 10 MB
            retention_config=config,
        )

        assert should_create is False
        assert "exceeds limit" in reason


class TestCleanupOldSnapshots:
    """Tests for cleanup_old_snapshots function."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        reset_snapshot_repository()
        with tempfile.TemporaryDirectory() as tmpdir:
            yield str(Path(tmpdir) / "test_snapshots.db")

    def test_cleanup_by_count(self, temp_db):
        """Test cleanup removes oldest beyond retention count."""
        repo = SnapshotRepository(temp_db)

        # Add 10 snapshots
        for i in range(10):
            compressed = zlib.compress(f'{{"headers":[],"rows":[{i}]}}'.encode())
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

        config = RetentionConfig(retention_count=5, retention_days=365)
        result = cleanup_old_snapshots(
            organization_id=1,
            db_path=temp_db,
            retention_config=config,
        )

        assert result.deleted_by_count == 5
        assert repo.count(organization_id=1) == 5


class TestCanRollback:
    """Tests for can_rollback function."""

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

    def test_snapshot_not_found(self, temp_db, mock_config):
        """Test rollback check fails if snapshot not found."""
        mock_config.tenant_db_path = temp_db

        can_proceed, reason = can_rollback(
            snapshot_id=999,
            organization_id=1,
            config=mock_config,
            db_path=temp_db,
        )

        assert can_proceed is False
        assert "not found" in reason

    @patch("mysql_to_sheets.core.history.rollback.gspread")
    def test_can_rollback_success(self, mock_gspread, temp_db, mock_config):
        """Test rollback check passes when all conditions met."""
        mock_config.tenant_db_path = temp_db

        # Add a snapshot
        repo = SnapshotRepository(temp_db)
        data = {"headers": ["id"], "rows": [["1"]]}
        compressed = zlib.compress(json.dumps(data).encode())
        checksum = hashlib.sha256(compressed).hexdigest()

        snapshot = Snapshot(
            sheet_id="test_sheet_id",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=1,
            column_count=1,
            size_bytes=len(compressed),
            checksum=checksum,
            data_compressed=compressed,
        )
        added = repo.add(snapshot)

        # Mock sheet access
        mock_worksheet = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_gc = MagicMock()
        mock_gc.open_by_key.return_value = mock_spreadsheet
        mock_gspread.service_account.return_value = mock_gc

        can_proceed, reason = can_rollback(
            snapshot_id=added.id,
            organization_id=1,
            config=mock_config,
            db_path=temp_db,
        )

        assert can_proceed is True
        assert "can proceed" in reason


class TestPreviewRollback:
    """Tests for preview_rollback function."""

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

    @patch("mysql_to_sheets.core.history.rollback.fetch_sheet_data")
    def test_preview_rollback(self, mock_fetch, temp_db, mock_config):
        """Test preview rollback generates diff."""
        mock_config.tenant_db_path = temp_db

        # Add a snapshot
        repo = SnapshotRepository(temp_db)
        data = {"headers": ["id", "name"], "rows": [["1", "Alice"], ["2", "Bob"]]}
        compressed = zlib.compress(json.dumps(data).encode())
        checksum = hashlib.sha256(compressed).hexdigest()

        snapshot = Snapshot(
            sheet_id="test_sheet_id",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=2,
            column_count=2,
            size_bytes=len(compressed),
            checksum=checksum,
            data_compressed=compressed,
        )
        added = repo.add(snapshot)

        # Mock current sheet data
        mock_fetch.return_value = (
            ["id", "name"],
            [["1", "Alice"], ["3", "Charlie"]],  # Different data
        )

        preview = preview_rollback(
            snapshot_id=added.id,
            organization_id=1,
            config=mock_config,
            db_path=temp_db,
        )

        assert preview.snapshot_id == added.id
        assert preview.current_row_count == 2
        assert preview.snapshot_row_count == 2
        assert preview.diff is not None


class TestRollbackToSnapshot:
    """Tests for rollback_to_snapshot function."""

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

    @patch("mysql_to_sheets.core.history.rollback.gspread")
    @patch("mysql_to_sheets.core.history.rollback.create_snapshot")
    def test_rollback_success(self, mock_create, mock_gspread, temp_db, mock_config):
        """Test successful rollback execution."""
        mock_config.tenant_db_path = temp_db

        # Add a snapshot
        repo = SnapshotRepository(temp_db)
        data = {"headers": ["id", "name"], "rows": [["1", "Alice"]]}
        compressed = zlib.compress(json.dumps(data).encode())
        checksum = hashlib.sha256(compressed).hexdigest()

        snapshot = Snapshot(
            sheet_id="test_sheet_id",
            worksheet_name="Sheet1",
            organization_id=1,
            row_count=1,
            column_count=2,
            size_bytes=len(compressed),
            checksum=checksum,
            data_compressed=compressed,
        )
        added = repo.add(snapshot)

        # Mock backup creation
        backup_snapshot = MagicMock()
        backup_snapshot.id = 99
        mock_create.return_value = backup_snapshot

        # Mock gspread
        mock_worksheet = MagicMock()
        mock_worksheet.row_count = 10  # Set to int to avoid MagicMock comparison issues
        mock_worksheet.col_count = 5
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_gc = MagicMock()
        mock_gc.open_by_key.return_value = mock_spreadsheet
        mock_gspread.service_account.return_value = mock_gc

        result = rollback_to_snapshot(
            snapshot_id=added.id,
            organization_id=1,
            config=mock_config,
            db_path=temp_db,
            create_backup=True,
        )

        assert result.success is True
        assert result.rows_restored == 1
        assert result.columns_restored == 2
        assert result.backup_snapshot_id == 99
        # Phase 5 update: batch_clear is used instead of clear when there's data to restore
        # and the current sheet has more rows/columns than the snapshot
        mock_worksheet.batch_clear.assert_called_once()
        mock_worksheet.update.assert_called_once()

    def test_rollback_snapshot_not_found(self, temp_db, mock_config):
        """Test rollback fails gracefully when snapshot not found."""
        mock_config.tenant_db_path = temp_db

        result = rollback_to_snapshot(
            snapshot_id=999,
            organization_id=1,
            config=mock_config,
            db_path=temp_db,
        )

        assert result.success is False
        assert "not found" in result.error


class TestGetRetentionConfigFromConfig:
    """Tests for get_retention_config_from_config function."""

    def test_extracts_config_values(self):
        """Test extracting retention config from main config."""
        mock_config = MagicMock()
        mock_config.snapshot_retention_count = 15
        mock_config.snapshot_retention_days = 60
        mock_config.snapshot_max_size_mb = 100

        retention = get_retention_config_from_config(mock_config)

        assert retention.retention_count == 15
        assert retention.retention_days == 60
        assert retention.max_size_mb == 100

    def test_uses_defaults_for_missing_attrs(self):
        """Test using defaults when config attrs missing."""
        mock_config = MagicMock(spec=[])  # Empty spec = no attributes

        retention = get_retention_config_from_config(mock_config)

        assert retention.retention_count == 10
        assert retention.retention_days == 30
        assert retention.max_size_mb == 50
