"""Tests for the job queue system."""

import os
import tempfile
from datetime import datetime

import pytest

from mysql_to_sheets.core.job_queue import (
    cancel_job,
    complete_job,
    enqueue_job,
    fail_job,
    get_job_status,
    get_next_job,
    get_queue_stats,
    reset_queue,
)
from mysql_to_sheets.core.job_worker import JobWorker
from mysql_to_sheets.models.jobs import (
    Job,
    JobRepository,
    reset_job_repository,
)


class TestJobModel:
    """Tests for Job dataclass."""

    def test_create_job(self):
        """Test creating a job with required fields."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={"config_id": 123},
        )

        assert job.organization_id == 1
        assert job.job_type == "sync"
        assert job.status == "pending"
        assert job.priority == 0
        assert job.attempts == 0
        assert job.max_attempts == 3

    def test_job_with_priority(self):
        """Test creating a job with priority."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={},
            priority=5,
        )

        assert job.priority == 5

    def test_job_to_dict(self):
        """Test converting job to dictionary."""
        job = Job(
            id=1,
            organization_id=1,
            user_id=2,
            job_type="sync",
            payload={"foo": "bar"},
            status="pending",
            priority=0,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        data = job.to_dict()

        assert data["id"] == 1
        assert data["organization_id"] == 1
        assert data["user_id"] == 2
        assert data["job_type"] == "sync"
        assert data["payload"] == {"foo": "bar"}
        assert "2024-01-01" in data["created_at"]

    def test_job_from_dict(self):
        """Test creating job from dictionary."""
        data = {
            "id": 1,
            "organization_id": 1,
            "job_type": "sync",
            "payload": {"foo": "bar"},
            "status": "running",
            "created_at": "2024-01-01T12:00:00",
        }

        job = Job.from_dict(data)

        assert job.id == 1
        assert job.organization_id == 1
        assert job.job_type == "sync"
        assert job.payload == {"foo": "bar"}
        assert job.status == "running"

    def test_job_validate_valid(self):
        """Test validation passes for valid job."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={},
        )

        errors = job.validate()
        assert errors == []

    def test_job_validate_invalid_type(self):
        """Test validation fails for invalid job type."""
        job = Job(
            organization_id=1,
            job_type="invalid",
            payload={},
        )

        errors = job.validate()
        assert len(errors) == 1
        assert "job_type" in errors[0]

    def test_job_validate_invalid_status(self):
        """Test validation fails for invalid status."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={},
            status="invalid",
        )

        errors = job.validate()
        assert len(errors) == 1
        assert "status" in errors[0]

    def test_can_retry_true(self):
        """Test can_retry returns true when attempts < max."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={},
            attempts=1,
            max_attempts=3,
        )

        assert job.can_retry is True

    def test_can_retry_false(self):
        """Test can_retry returns false when attempts >= max."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={},
            attempts=3,
            max_attempts=3,
        )

        assert job.can_retry is False

    def test_is_terminal(self):
        """Test is_terminal for various statuses."""
        for status in ["completed", "failed", "cancelled"]:
            job = Job(
                organization_id=1,
                job_type="sync",
                payload={},
                status=status,
            )
            assert job.is_terminal is True

        for status in ["pending", "running"]:
            job = Job(
                organization_id=1,
                job_type="sync",
                payload={},
                status=status,
            )
            assert job.is_terminal is False


class TestJobRepository:
    """Tests for JobRepository."""

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

    @pytest.fixture
    def repo(self, db_path):
        """Create a repository instance."""
        reset_job_repository()
        return JobRepository(db_path)

    def test_create_job(self, repo):
        """Test creating a job."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={"test": True},
        )

        created = repo.create(job)

        assert created.id is not None
        assert created.organization_id == 1
        assert created.job_type == "sync"
        assert created.status == "pending"

    def test_get_by_id(self, repo):
        """Test getting a job by ID."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={},
        )
        created = repo.create(job)

        found = repo.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.organization_id == 1

    def test_get_by_id_with_org_filter(self, repo):
        """Test getting a job by ID with org filter."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={},
        )
        created = repo.create(job)

        # Same org - found
        found = repo.get_by_id(created.id, organization_id=1)
        assert found is not None

        # Different org - not found
        found = repo.get_by_id(created.id, organization_id=2)
        assert found is None

    def test_get_next_pending(self, repo):
        """Test getting and claiming the next pending job."""
        # Create jobs with different priorities
        job1 = repo.create(Job(organization_id=1, job_type="sync", payload={}, priority=0))
        job2 = repo.create(Job(organization_id=1, job_type="sync", payload={}, priority=5))
        job3 = repo.create(Job(organization_id=1, job_type="sync", payload={}, priority=2))

        # Should get highest priority first
        next_job = repo.get_next_pending()
        assert next_job is not None
        assert next_job.id == job2.id
        assert next_job.status == "running"
        assert next_job.attempts == 1

        # Next should be priority 2
        next_job = repo.get_next_pending()
        assert next_job.id == job3.id

    def test_complete_job(self, repo):
        """Test completing a job."""
        job = repo.create(Job(organization_id=1, job_type="sync", payload={}))
        repo.claim_job(job.id)

        result = {"rows_synced": 100}
        success = repo.complete(job.id, result)

        assert success is True
        completed = repo.get_by_id(job.id)
        assert completed.status == "completed"
        assert completed.result == result
        assert completed.completed_at is not None

    def test_fail_job_with_retry(self, repo):
        """Test failing a job with retry."""
        job = repo.create(Job(organization_id=1, job_type="sync", payload={}, max_attempts=3))
        repo.claim_job(job.id)

        success = repo.fail(job.id, "Test error", requeue=True)

        assert success is True
        failed = repo.get_by_id(job.id)
        assert failed.status == "pending"  # Requeued
        assert failed.error == "Test error"

    def test_fail_job_no_retry_to_dlq(self, repo):
        """Test failing a job without retry moves to dead letter queue."""
        job = repo.create(Job(organization_id=1, job_type="sync", payload={}, max_attempts=1))
        repo.claim_job(job.id)

        success = repo.fail(job.id, "Test error", requeue=True)

        assert success is True
        failed = repo.get_by_id(job.id)
        assert failed.status == "dead_letter"  # No more retries, moved to DLQ

    def test_fail_job_no_retry_to_failed(self, repo):
        """Test failing a job with move_to_dlq=False keeps failed status."""
        job = repo.create(Job(organization_id=1, job_type="sync", payload={}, max_attempts=1))
        repo.claim_job(job.id)

        success = repo.fail(job.id, "Test error", requeue=True, move_to_dlq=False)

        assert success is True
        failed = repo.get_by_id(job.id)
        assert failed.status == "failed"  # No more retries, stays as failed

    def test_cancel_job(self, repo):
        """Test cancelling a pending job."""
        job = repo.create(Job(organization_id=1, job_type="sync", payload={}))

        success = repo.cancel(job.id, organization_id=1)

        assert success is True
        cancelled = repo.get_by_id(job.id)
        assert cancelled.status == "cancelled"

    def test_cancel_running_job_fails(self, repo):
        """Test that running jobs cannot be cancelled."""
        job = repo.create(Job(organization_id=1, job_type="sync", payload={}))
        repo.claim_job(job.id)

        success = repo.cancel(job.id, organization_id=1)

        assert success is False

    def test_retry_job(self, repo):
        """Test retrying a failed job."""
        job = repo.create(Job(organization_id=1, job_type="sync", payload={}, max_attempts=3))
        repo.claim_job(job.id)
        # Use move_to_dlq=False so job stays as "failed" instead of "dead_letter"
        repo.fail(job.id, "Error", requeue=False, move_to_dlq=False)

        retried = repo.retry(job.id, organization_id=1)

        assert retried is not None
        assert retried.status == "pending"
        assert retried.attempts == 0
        assert retried.error is None

    def test_retry_dead_letter_job(self, repo):
        """Test retrying a job from dead letter queue."""
        job = repo.create(Job(organization_id=1, job_type="sync", payload={}, max_attempts=1))
        repo.claim_job(job.id)
        # Exhaust retries, job goes to DLQ
        repo.fail(job.id, "Error", requeue=True)

        # Verify it's in DLQ
        failed_job = repo.get_by_id(job.id)
        assert failed_job.status == "dead_letter"

        # Retry from DLQ
        retried = repo.retry_dead_letter(job.id, organization_id=1)

        assert retried is not None
        assert retried.status == "pending"
        assert retried.attempts == 0
        assert retried.error is None

    def test_get_all_with_filters(self, repo):
        """Test getting all jobs with filters."""
        repo.create(Job(organization_id=1, job_type="sync", payload={}))
        repo.create(Job(organization_id=1, job_type="export", payload={}))
        repo.create(Job(organization_id=2, job_type="sync", payload={}))

        # Filter by org
        jobs = repo.get_all(organization_id=1)
        assert len(jobs) == 2

        # Filter by type
        jobs = repo.get_all(organization_id=1, job_type="sync")
        assert len(jobs) == 1

    def test_count(self, repo):
        """Test counting jobs."""
        repo.create(Job(organization_id=1, job_type="sync", payload={}))
        repo.create(Job(organization_id=1, job_type="sync", payload={}))
        repo.create(Job(organization_id=2, job_type="sync", payload={}))

        count = repo.count(organization_id=1)
        assert count == 2

        count = repo.count()
        assert count == 3


class TestJobQueueService:
    """Tests for job queue service functions."""

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
        reset_queue()

    def test_enqueue_job(self, db_path):
        """Test enqueuing a job."""
        job = enqueue_job(
            job_type="sync",
            payload={"test": True},
            organization_id=1,
            user_id=2,
            max_attempts=3,
            db_path=db_path,
        )

        assert job.id is not None
        assert job.job_type == "sync"
        assert job.status == "pending"

    def test_get_next_job(self, db_path):
        """Test getting the next job."""
        enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            max_attempts=3,
            db_path=db_path,
        )

        job = get_next_job(db_path=db_path)

        assert job is not None
        assert job.status == "running"

    def test_complete_job(self, db_path):
        """Test completing a job."""
        created = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            max_attempts=3,
            db_path=db_path,
        )
        get_next_job(db_path=db_path)

        success = complete_job(created.id, {"result": "ok"}, db_path=db_path)

        assert success is True
        job = get_job_status(created.id, db_path=db_path)
        assert job.status == "completed"

    def test_fail_job(self, db_path):
        """Test failing a job."""
        created = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            max_attempts=3,
            db_path=db_path,
        )
        get_next_job(db_path=db_path)

        success = fail_job(created.id, "Test error", db_path=db_path)

        assert success is True

    def test_cancel_job(self, db_path):
        """Test cancelling a job."""
        created = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            max_attempts=3,
            db_path=db_path,
        )

        success = cancel_job(created.id, organization_id=1, db_path=db_path)

        assert success is True

    def test_get_queue_stats(self, db_path):
        """Test getting queue statistics."""
        enqueue_job(job_type="sync", payload={}, organization_id=1, max_attempts=3, db_path=db_path)
        enqueue_job(job_type="sync", payload={}, organization_id=1, max_attempts=3, db_path=db_path)

        stats = get_queue_stats(organization_id=1, db_path=db_path)

        assert stats["pending"] == 2
        assert stats["running"] == 0


class TestJobWorker:
    """Tests for JobWorker."""

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
        reset_queue()

    def test_worker_creation(self, db_path):
        """Test creating a worker."""
        worker = JobWorker(db_path=db_path)

        assert worker._db_path == db_path
        assert worker._running is False
        assert worker._poll_interval == 1.0

    def test_worker_start_stop(self, db_path):
        """Test worker start and stop."""
        worker = JobWorker(db_path=db_path)

        # Stop before start (should be safe)
        worker.stop()
        assert worker.is_running is False
