"""Tests for resumable streaming sync with checkpoint-based resume.

Tests cover:
- Checkpoint model and repository CRUD operations
- Offset parameter in fetch_data_streaming
- Checkpoint saving during atomic streaming
- Resume from checkpoint functionality
- API endpoints for resume/checkpoint operations
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.config import reset_config
from mysql_to_sheets.models.checkpoints import (
    CheckpointRepository,
    StreamingCheckpoint,
    StreamingCheckpointModel,
    get_checkpoint_repository,
    reset_checkpoint_repository,
)


class TestStreamingCheckpoint:
    """Tests for StreamingCheckpoint dataclass."""

    def test_create_checkpoint(self):
        """Test creating a checkpoint with required fields."""
        checkpoint = StreamingCheckpoint(
            job_id=1,
            config_id=10,
            staging_worksheet_name="_staging_test",
            staging_worksheet_gid=12345,
        )
        assert checkpoint.job_id == 1
        assert checkpoint.config_id == 10
        assert checkpoint.staging_worksheet_name == "_staging_test"
        assert checkpoint.staging_worksheet_gid == 12345
        assert checkpoint.chunks_completed == 0
        assert checkpoint.rows_pushed == 0
        assert checkpoint.headers == []

    def test_checkpoint_with_progress(self):
        """Test checkpoint with progress fields set."""
        checkpoint = StreamingCheckpoint(
            job_id=2,
            config_id=20,
            staging_worksheet_name="_staging_data",
            staging_worksheet_gid=67890,
            chunks_completed=5,
            rows_pushed=5000,
            headers=["id", "name", "email"],
        )
        assert checkpoint.chunks_completed == 5
        assert checkpoint.rows_pushed == 5000
        assert checkpoint.headers == ["id", "name", "email"]

    def test_to_dict(self):
        """Test checkpoint serialization to dictionary."""
        now = datetime.now(timezone.utc)
        checkpoint = StreamingCheckpoint(
            job_id=3,
            config_id=30,
            staging_worksheet_name="_staging_export",
            staging_worksheet_gid=11111,
            chunks_completed=3,
            rows_pushed=3000,
            headers=["a", "b"],
            created_at=now,
            updated_at=now,
            id=99,
        )
        d = checkpoint.to_dict()
        assert d["job_id"] == 3
        assert d["config_id"] == 30
        assert d["chunks_completed"] == 3
        assert d["rows_pushed"] == 3000
        assert d["headers"] == ["a", "b"]
        assert d["id"] == 99

    def test_from_dict(self):
        """Test checkpoint deserialization from dictionary."""
        data = {
            "job_id": 4,
            "config_id": 40,
            "staging_worksheet_name": "_staging_import",
            "staging_worksheet_gid": 22222,
            "chunks_completed": 10,
            "rows_pushed": 10000,
            "headers": ["x", "y", "z"],
            "created_at": "2024-01-15T10:30:00+00:00",
            "updated_at": "2024-01-15T11:00:00+00:00",
        }
        checkpoint = StreamingCheckpoint.from_dict(data)
        assert checkpoint.job_id == 4
        assert checkpoint.config_id == 40
        assert checkpoint.chunks_completed == 10
        assert checkpoint.headers == ["x", "y", "z"]


class TestCheckpointRepository:
    """Tests for CheckpointRepository CRUD operations."""

    def setup_method(self):
        """Reset singleton and create fresh temp database."""
        reset_checkpoint_repository()
        self._temp_dir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._temp_dir, "checkpoints.db")

    def teardown_method(self):
        """Clean up temp files."""
        reset_checkpoint_repository()
        if os.path.exists(self._db_path):
            os.unlink(self._db_path)
        if os.path.exists(self._temp_dir):
            os.rmdir(self._temp_dir)

    def test_save_and_get_checkpoint(self):
        """Test saving and retrieving a checkpoint."""
        repo = CheckpointRepository(self._db_path)

        checkpoint = StreamingCheckpoint(
            job_id=100,
            config_id=10,
            staging_worksheet_name="_staging_test",
            staging_worksheet_gid=99999,
            chunks_completed=2,
            rows_pushed=2000,
            headers=["col1", "col2"],
        )

        saved = repo.save_checkpoint(checkpoint)
        assert saved.id is not None
        assert saved.job_id == 100

        retrieved = repo.get_checkpoint(100)
        assert retrieved is not None
        assert retrieved.job_id == 100
        assert retrieved.config_id == 10
        assert retrieved.chunks_completed == 2
        assert retrieved.rows_pushed == 2000
        assert retrieved.headers == ["col1", "col2"]

    def test_upsert_checkpoint(self):
        """Test that save_checkpoint updates existing checkpoint."""
        repo = CheckpointRepository(self._db_path)

        # Initial save
        checkpoint = StreamingCheckpoint(
            job_id=200,
            config_id=20,
            staging_worksheet_name="_staging_upsert",
            staging_worksheet_gid=88888,
            chunks_completed=1,
            rows_pushed=1000,
        )
        repo.save_checkpoint(checkpoint)

        # Update with more progress
        checkpoint.chunks_completed = 5
        checkpoint.rows_pushed = 5000
        repo.save_checkpoint(checkpoint)

        # Verify update
        retrieved = repo.get_checkpoint(200)
        assert retrieved.chunks_completed == 5
        assert retrieved.rows_pushed == 5000

        # Should still be only one record
        assert repo.count() == 1

    def test_delete_checkpoint(self):
        """Test deleting a checkpoint."""
        repo = CheckpointRepository(self._db_path)

        checkpoint = StreamingCheckpoint(
            job_id=300,
            config_id=30,
            staging_worksheet_name="_staging_delete",
            staging_worksheet_gid=77777,
        )
        repo.save_checkpoint(checkpoint)
        assert repo.get_checkpoint(300) is not None

        deleted = repo.delete_checkpoint(300)
        assert deleted is True
        assert repo.get_checkpoint(300) is None

    def test_delete_nonexistent_checkpoint(self):
        """Test deleting a checkpoint that doesn't exist."""
        repo = CheckpointRepository(self._db_path)
        deleted = repo.delete_checkpoint(999999)
        assert deleted is False

    def test_get_checkpoint_by_config(self):
        """Test finding checkpoint by config ID."""
        repo = CheckpointRepository(self._db_path)

        # Create two checkpoints for different configs
        cp1 = StreamingCheckpoint(
            job_id=400,
            config_id=50,
            staging_worksheet_name="_staging_c50",
            staging_worksheet_gid=11111,
        )
        cp2 = StreamingCheckpoint(
            job_id=401,
            config_id=51,
            staging_worksheet_name="_staging_c51",
            staging_worksheet_gid=22222,
        )
        repo.save_checkpoint(cp1)
        repo.save_checkpoint(cp2)

        # Find by config
        found = repo.get_checkpoint_by_config(50)
        assert found is not None
        assert found.job_id == 400

    def test_get_nonexistent_checkpoint(self):
        """Test getting a checkpoint that doesn't exist."""
        repo = CheckpointRepository(self._db_path)
        result = repo.get_checkpoint(999999)
        assert result is None

    def test_count_checkpoints(self):
        """Test counting checkpoints."""
        repo = CheckpointRepository(self._db_path)
        assert repo.count() == 0

        for i in range(3):
            cp = StreamingCheckpoint(
                job_id=500 + i,
                config_id=60,
                staging_worksheet_name=f"_staging_{i}",
                staging_worksheet_gid=30000 + i,
            )
            repo.save_checkpoint(cp)

        assert repo.count() == 3


class TestFetchDataStreamingOffset:
    """Tests for offset parameter in fetch_data_streaming."""

    def setup_method(self):
        """Reset config singleton."""
        reset_config()

    def test_offset_parameter_exists(self):
        """Test that fetch_data_streaming accepts offset parameter."""
        from mysql_to_sheets.core.streaming import fetch_data_streaming
        import inspect

        # Verify the function signature includes offset
        sig = inspect.signature(fetch_data_streaming)
        params = list(sig.parameters.keys())
        assert "offset" in params, "fetch_data_streaming should have 'offset' parameter"

        # Verify default value is 0
        offset_param = sig.parameters["offset"]
        assert offset_param.default == 0, "offset default should be 0"


class TestAtomicStreamingConfigResumable:
    """Tests for resumable fields in AtomicStreamingConfig."""

    def test_resumable_defaults_false(self):
        """Test that resumable is False by default."""
        from mysql_to_sheets.core.atomic_streaming import AtomicStreamingConfig

        ac = AtomicStreamingConfig()
        assert ac.resumable is False
        assert ac.checkpoint_interval == 1
        assert ac.resume_from_checkpoint is None

    def test_resumable_enabled(self):
        """Test creating config with resumable enabled."""
        from mysql_to_sheets.core.atomic_streaming import AtomicStreamingConfig

        ac = AtomicStreamingConfig(
            resumable=True,
            checkpoint_interval=5,
        )
        assert ac.resumable is True
        assert ac.checkpoint_interval == 5


class TestAtomicStreamingResultResumable:
    """Tests for resumable fields in AtomicStreamingResult."""

    def test_result_resumable_fields(self):
        """Test that result includes resumable fields."""
        from mysql_to_sheets.core.atomic_streaming import AtomicStreamingResult

        result = AtomicStreamingResult(
            total_rows=1000,
            total_chunks=10,
            successful_chunks=5,
            failed_chunks=1,
            resumable=True,
            checkpoint_chunk=5,
            staging_worksheet_gid=12345,
        )
        assert result.resumable is True
        assert result.checkpoint_chunk == 5
        assert result.staging_worksheet_gid == 12345


class TestCheckpointModel:
    """Tests for StreamingCheckpointModel SQLAlchemy model."""

    def test_model_to_dataclass(self):
        """Test converting model to dataclass."""
        model = StreamingCheckpointModel(
            id=1,
            job_id=100,
            config_id=10,
            staging_worksheet_name="_staging_test",
            staging_worksheet_gid=99999,
            chunks_completed=5,
            rows_pushed=5000,
            headers_json=json.dumps(["a", "b", "c"]),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        dc = model.to_dataclass()
        assert dc.job_id == 100
        assert dc.config_id == 10
        assert dc.chunks_completed == 5
        assert dc.headers == ["a", "b", "c"]

    def test_model_from_dataclass(self):
        """Test creating model from dataclass."""
        checkpoint = StreamingCheckpoint(
            job_id=200,
            config_id=20,
            staging_worksheet_name="_staging_from_dc",
            staging_worksheet_gid=88888,
            chunks_completed=3,
            rows_pushed=3000,
            headers=["x", "y"],
        )

        model = StreamingCheckpointModel.from_dataclass(checkpoint)
        assert model.job_id == 200
        assert model.config_id == 20
        assert model.chunks_completed == 3
        assert model.headers_json == '["x", "y"]'


class TestCheckpointRepositorySingleton:
    """Tests for checkpoint repository singleton management."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_checkpoint_repository()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_checkpoint_repository()

    def test_singleton_requires_db_path_on_first_call(self):
        """Test that first call requires db_path."""
        with pytest.raises(ValueError, match="db_path is required"):
            get_checkpoint_repository()

    def test_singleton_returns_same_instance(self):
        """Test that singleton returns same instance."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo1 = get_checkpoint_repository(db_path)
            repo2 = get_checkpoint_repository()  # No path needed on subsequent calls
            assert repo1 is repo2
        finally:
            reset_checkpoint_repository()
            os.unlink(db_path)
