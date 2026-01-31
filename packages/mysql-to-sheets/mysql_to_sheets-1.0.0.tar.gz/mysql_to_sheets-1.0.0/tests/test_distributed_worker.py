"""Tests for distributed job worker functionality.

Uses freezegun for time-sensitive tests where possible.
Some threading tests require real time.sleep and are marked @pytest.mark.slow.
"""

import os
import tempfile
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from freezegun import freeze_time
import pytest

from mysql_to_sheets.core.job_factory import reset_job_backend
from mysql_to_sheets.core.job_worker import (
    JobWorker,
    generate_worker_id,
)
from mysql_to_sheets.models.jobs import Job


class TestGenerateWorkerId:
    """Tests for worker ID generation."""

    def test_generates_unique_ids(self):
        """Test that generated IDs are unique."""
        ids = [generate_worker_id() for _ in range(10)]
        assert len(set(ids)) == 10

    def test_includes_hostname(self):
        """Test that worker ID includes hostname."""
        import socket

        hostname = socket.gethostname()[:20]

        worker_id = generate_worker_id()

        assert hostname in worker_id

    def test_format(self):
        """Test worker ID format."""
        worker_id = generate_worker_id()

        # Should be hostname-uuid format
        parts = worker_id.split("-")
        assert len(parts) >= 2


class TestJobWorkerInit:
    """Tests for JobWorker initialization."""

    def test_default_worker_id(self):
        """Test that worker ID is auto-generated."""
        worker = JobWorker()

        assert worker.worker_id is not None
        assert len(worker.worker_id) > 0

    def test_custom_worker_id(self):
        """Test using a custom worker ID."""
        worker = JobWorker(worker_id="test-worker-1")

        assert worker.worker_id == "test-worker-1"

    def test_env_worker_id(self):
        """Test worker ID from environment variable."""
        with patch.dict(os.environ, {"WORKER_ID": "env-worker"}):
            worker = JobWorker()

        assert worker.worker_id == "env-worker"

    def test_explicit_overrides_env(self):
        """Test explicit worker ID overrides environment."""
        with patch.dict(os.environ, {"WORKER_ID": "env-worker"}):
            worker = JobWorker(worker_id="explicit-worker")

        assert worker.worker_id == "explicit-worker"

    def test_default_intervals(self):
        """Test default interval values."""
        worker = JobWorker()

        assert worker._poll_interval == 1.0
        assert worker._stale_check_interval == 60
        assert worker._heartbeat_interval == 30

    def test_custom_intervals(self):
        """Test custom interval values."""
        worker = JobWorker(
            poll_interval=0.5,
            stale_check_interval=30,
            heartbeat_interval=15,
        )

        assert worker._poll_interval == 0.5
        assert worker._stale_check_interval == 30
        assert worker._heartbeat_interval == 15


class TestJobWorkerWithBackend:
    """Tests for JobWorker with actual backend."""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
        reset_job_backend()

    @pytest.fixture
    def mock_backend(self):
        """Create a mock job backend."""
        backend = MagicMock()
        backend.get_next_pending.return_value = None
        backend.cleanup_stale.return_value = 0
        return backend

    def test_worker_claims_job_with_worker_id(self, mock_backend):
        """Test that worker passes its ID when claiming jobs."""
        worker = JobWorker(
            worker_id="test-worker",
            backend=mock_backend,
        )

        worker._poll_for_job()

        mock_backend.get_next_pending.assert_called_with(worker_id="test-worker")

    @pytest.mark.slow
    def test_worker_heartbeat_during_processing(self, mock_backend):
        """Test that heartbeat is sent during job processing.

        This test requires real threading and cannot use freezegun.
        """
        job = Job(
            id=1,
            organization_id=1,
            job_type="sync",
            payload={},
            status="running",
            attempts=1,
        )
        mock_backend.get_next_pending.return_value = job
        mock_backend.heartbeat.return_value = True

        worker = JobWorker(
            worker_id="test-worker",
            heartbeat_interval=1,  # 1 second for test
            backend=mock_backend,
        )

        # Start heartbeat thread manually
        worker._start_heartbeat_thread()

        # Simulate having a current job
        with worker._current_job_lock:
            worker._current_job = job

        # Wait for at least one heartbeat cycle
        time.sleep(1.5)

        # Stop the heartbeat thread
        worker._heartbeat_stop.set()
        worker._heartbeat_thread.join(timeout=2.0)

        # Verify heartbeat was called
        mock_backend.heartbeat.assert_called_with(1, "test-worker")

    def test_graceful_shutdown_releases_job(self, mock_backend):
        """Test that graceful shutdown releases current job."""
        job = Job(
            id=1,
            organization_id=1,
            job_type="sync",
            payload={},
            status="running",
        )
        mock_backend.release_job.return_value = True

        worker = JobWorker(
            worker_id="test-worker",
            backend=mock_backend,
        )

        # Simulate having a current job
        with worker._current_job_lock:
            worker._current_job = job

        # Start heartbeat thread so we can test cleanup
        worker._start_heartbeat_thread()

        # Perform graceful shutdown
        worker._graceful_shutdown()

        # Verify job was released
        mock_backend.release_job.assert_called_once_with(1)

        # Verify current job is cleared
        assert worker.current_job is None

    def test_stale_job_cleanup(self, mock_backend):
        """Test that stale jobs are cleaned up periodically."""
        mock_backend.cleanup_stale.return_value = 2

        worker = JobWorker(
            worker_id="test-worker",
            stale_check_interval=0,  # Force immediate check
            backend=mock_backend,
        )

        # Trigger stale check
        worker._check_stale_jobs()

        # Verify cleanup was called
        mock_backend.cleanup_stale.assert_called()


class TestJobWorkerProperties:
    """Tests for JobWorker properties."""

    def test_is_running_false_by_default(self):
        """Test is_running is False by default."""
        worker = JobWorker()
        assert worker.is_running is False

    def test_current_job_none_by_default(self):
        """Test current_job is None by default."""
        worker = JobWorker()
        assert worker.current_job is None


class TestDistributedWorkerFields:
    """Tests for worker fields in Job model."""

    def test_job_with_worker_fields(self):
        """Test Job dataclass includes worker fields."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={},
            worker_id="worker-1",
            heartbeat_at=datetime.now(timezone.utc),
        )

        assert job.worker_id == "worker-1"
        assert job.heartbeat_at is not None

    def test_job_to_dict_includes_worker_fields(self):
        """Test Job.to_dict includes worker fields."""
        now = datetime.now(timezone.utc)
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={},
            worker_id="worker-1",
            heartbeat_at=now,
        )

        data = job.to_dict()

        assert data["worker_id"] == "worker-1"
        assert data["heartbeat_at"] is not None

    def test_job_from_dict_with_worker_fields(self):
        """Test Job.from_dict handles worker fields."""
        data = {
            "organization_id": 1,
            "job_type": "sync",
            "payload": {},
            "worker_id": "worker-1",
            "heartbeat_at": "2024-01-01T12:00:00",
        }

        job = Job.from_dict(data)

        assert job.worker_id == "worker-1"
        assert job.heartbeat_at is not None


class TestSQLiteBackendWorkerSupport:
    """Tests for SQLite backend worker support."""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass

    def test_claim_job_sets_worker_id(self, db_path):
        """Test that claiming a job sets the worker ID."""
        from mysql_to_sheets.core.sqlite_job_queue import SQLiteJobQueue

        backend = SQLiteJobQueue(db_path=db_path)
        job = backend.create(Job(organization_id=1, job_type="sync", payload={}))

        claimed = backend.get_next_pending(worker_id="worker-1")

        assert claimed is not None
        assert claimed.worker_id == "worker-1"
        assert claimed.heartbeat_at is not None

    def test_heartbeat_updates_timestamp(self, db_path):
        """Test that heartbeat updates the timestamp."""
        from mysql_to_sheets.core.sqlite_job_queue import SQLiteJobQueue

        backend = SQLiteJobQueue(db_path=db_path)

        with freeze_time("2024-01-15 10:00:00") as frozen_time:
            job = backend.create(Job(organization_id=1, job_type="sync", payload={}))
            claimed = backend.get_next_pending(worker_id="worker-1")

            initial_heartbeat = claimed.heartbeat_at

            # Move time forward
            frozen_time.move_to("2024-01-15 10:00:01")

            success = backend.heartbeat(claimed.id, "worker-1")

            assert success is True
            updated = backend.get_by_id(claimed.id)
            assert updated.heartbeat_at >= initial_heartbeat

    def test_heartbeat_wrong_worker_fails(self, db_path):
        """Test that heartbeat fails for wrong worker."""
        from mysql_to_sheets.core.sqlite_job_queue import SQLiteJobQueue

        backend = SQLiteJobQueue(db_path=db_path)
        job = backend.create(Job(organization_id=1, job_type="sync", payload={}))
        backend.get_next_pending(worker_id="worker-1")

        success = backend.heartbeat(job.id, "worker-2")

        assert success is False

    def test_release_job(self, db_path):
        """Test releasing a job back to pending."""
        from mysql_to_sheets.core.sqlite_job_queue import SQLiteJobQueue

        backend = SQLiteJobQueue(db_path=db_path)
        job = backend.create(Job(organization_id=1, job_type="sync", payload={}))
        backend.get_next_pending(worker_id="worker-1")

        success = backend.release_job(job.id)

        assert success is True
        released = backend.get_by_id(job.id)
        assert released.status == "pending"
        assert released.worker_id is None
        assert released.heartbeat_at is None

    def test_cleanup_stale_by_heartbeat(self, db_path):
        """Test cleaning up stale jobs based on heartbeat."""
        from mysql_to_sheets.core.sqlite_job_queue import SQLiteJobQueue

        backend = SQLiteJobQueue(db_path=db_path)
        job = backend.create(Job(organization_id=1, job_type="sync", payload={}))
        backend.get_next_pending(worker_id="worker-1")

        # Manually set old heartbeat
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=backend._engine)
        session = Session()
        from mysql_to_sheets.models.jobs import JobModel

        model = session.query(JobModel).filter(JobModel.id == job.id).first()
        model.heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=600)
        session.commit()
        session.close()

        # Cleanup with 300 second timeout
        count = backend.cleanup_stale(timeout_seconds=300)

        assert count == 1
        cleaned = backend.get_by_id(job.id)
        assert cleaned.status == "pending"  # Released back to pending
