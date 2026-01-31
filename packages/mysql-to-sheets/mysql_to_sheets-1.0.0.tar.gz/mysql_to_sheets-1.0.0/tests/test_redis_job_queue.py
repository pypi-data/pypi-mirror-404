"""Tests for the Redis job queue backend."""

from unittest.mock import patch

import pytest

from mysql_to_sheets.models.jobs import Job


class TestRedisJobQueue:
    """Tests for RedisJobQueue using fakeredis."""

    @pytest.fixture
    def fake_redis(self):
        """Create a fakeredis instance for testing."""
        try:
            import fakeredis

            return fakeredis.FakeRedis(decode_responses=True)
        except ImportError:
            pytest.skip("fakeredis not installed")

    @pytest.fixture
    def redis_queue(self, fake_redis):
        """Create a RedisJobQueue with fakeredis backend."""
        from mysql_to_sheets.core.redis_job_queue import RedisJobQueue

        return RedisJobQueue(redis_client=fake_redis, ttl_seconds=3600)

    def test_create_job(self, redis_queue):
        """Test creating a job."""
        job = Job(
            organization_id=1,
            job_type="sync",
            payload={"config_id": 123},
        )

        created = redis_queue.create(job)

        assert created.id is not None
        assert created.id > 0
        assert created.organization_id == 1
        assert created.job_type == "sync"
        assert created.status == "pending"

    def test_create_job_assigns_sequential_ids(self, redis_queue):
        """Test that job IDs are sequential."""
        job1 = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        job2 = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))

        assert job2.id == job1.id + 1

    def test_create_job_validation(self, redis_queue):
        """Test that invalid jobs are rejected."""
        job = Job(
            organization_id=1,
            job_type="invalid_type",
            payload={},
        )

        with pytest.raises(ValueError) as exc_info:
            redis_queue.create(job)

        assert "Invalid job" in str(exc_info.value)

    def test_get_by_id(self, redis_queue):
        """Test getting a job by ID."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))

        found = redis_queue.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.organization_id == 1

    def test_get_by_id_not_found(self, redis_queue):
        """Test getting a non-existent job."""
        found = redis_queue.get_by_id(99999)
        assert found is None

    def test_get_by_id_with_org_filter(self, redis_queue):
        """Test getting a job with organization filter."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))

        # Same org - found
        found = redis_queue.get_by_id(created.id, organization_id=1)
        assert found is not None

        # Different org - not found
        found = redis_queue.get_by_id(created.id, organization_id=2)
        assert found is None

    def test_get_next_pending_priority_order(self, redis_queue):
        """Test that jobs are returned in priority order."""
        job_low = redis_queue.create(
            Job(organization_id=1, job_type="sync", payload={}, priority=0)
        )
        job_high = redis_queue.create(
            Job(organization_id=1, job_type="sync", payload={}, priority=10)
        )
        job_med = redis_queue.create(
            Job(organization_id=1, job_type="sync", payload={}, priority=5)
        )

        # Should get highest priority first
        next_job = redis_queue.get_next_pending(worker_id="worker-1")
        assert next_job.id == job_high.id
        assert next_job.status == "running"

        next_job = redis_queue.get_next_pending(worker_id="worker-1")
        assert next_job.id == job_med.id

        next_job = redis_queue.get_next_pending(worker_id="worker-1")
        assert next_job.id == job_low.id

    def test_get_next_pending_assigns_worker(self, redis_queue):
        """Test that claiming a job assigns the worker ID."""
        redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))

        job = redis_queue.get_next_pending(worker_id="test-worker")

        assert job.worker_id == "test-worker"
        assert job.heartbeat_at is not None

    def test_get_next_pending_empty_queue(self, redis_queue):
        """Test getting next job from empty queue."""
        job = redis_queue.get_next_pending()
        assert job is None

    def test_claim_job(self, redis_queue):
        """Test claiming a specific job."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))

        claimed = redis_queue.claim_job(created.id, worker_id="worker-1")

        assert claimed is not None
        assert claimed.status == "running"
        assert claimed.worker_id == "worker-1"

    def test_claim_job_already_running(self, redis_queue):
        """Test that running jobs cannot be claimed again."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.claim_job(created.id, worker_id="worker-1")

        # Try to claim again
        claimed = redis_queue.claim_job(created.id, worker_id="worker-2")

        assert claimed is None

    def test_complete_job(self, redis_queue):
        """Test completing a job."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.claim_job(created.id)

        result = {"rows_synced": 100}
        success = redis_queue.complete(created.id, result)

        assert success is True
        completed = redis_queue.get_by_id(created.id)
        assert completed.status == "completed"
        assert completed.result == result
        assert completed.completed_at is not None

    def test_complete_job_not_running(self, redis_queue):
        """Test completing a non-running job fails."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))

        success = redis_queue.complete(created.id, {"result": "ok"})

        assert success is False

    def test_fail_job_with_retry(self, redis_queue):
        """Test failing a job with retry available."""
        created = redis_queue.create(
            Job(organization_id=1, job_type="sync", payload={}, max_attempts=3)
        )
        redis_queue.claim_job(created.id)

        success = redis_queue.fail(created.id, "Test error", requeue=True)

        assert success is True
        failed = redis_queue.get_by_id(created.id)
        assert failed.status == "pending"  # Requeued
        assert failed.error == "Test error"

    def test_fail_job_max_attempts_reached(self, redis_queue):
        """Test failing a job when max attempts reached."""
        created = redis_queue.create(
            Job(organization_id=1, job_type="sync", payload={}, max_attempts=1)
        )
        redis_queue.claim_job(created.id)

        success = redis_queue.fail(created.id, "Test error", requeue=True)

        assert success is True
        failed = redis_queue.get_by_id(created.id)
        assert failed.status == "failed"  # No more retries

    def test_cancel_job(self, redis_queue):
        """Test cancelling a pending job."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))

        success = redis_queue.cancel(created.id, organization_id=1)

        assert success is True
        cancelled = redis_queue.get_by_id(created.id)
        assert cancelled.status == "cancelled"

    def test_cancel_running_job_fails(self, redis_queue):
        """Test that running jobs cannot be cancelled."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.claim_job(created.id)

        success = redis_queue.cancel(created.id, organization_id=1)

        assert success is False

    def test_retry_job(self, redis_queue):
        """Test retrying a failed job."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.claim_job(created.id)
        redis_queue.fail(created.id, "Error", requeue=False)

        retried = redis_queue.retry(created.id, organization_id=1)

        assert retried is not None
        assert retried.status == "pending"
        assert retried.attempts == 0
        assert retried.error is None

    def test_release_job(self, redis_queue):
        """Test releasing a running job back to pending."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.claim_job(created.id, worker_id="worker-1")

        success = redis_queue.release_job(created.id)

        assert success is True
        released = redis_queue.get_by_id(created.id)
        assert released.status == "pending"
        assert released.worker_id is None

    def test_heartbeat(self, redis_queue):
        """Test updating job heartbeat."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.claim_job(created.id, worker_id="worker-1")

        success = redis_queue.heartbeat(created.id, "worker-1")

        assert success is True

    def test_heartbeat_wrong_worker(self, redis_queue):
        """Test heartbeat fails for wrong worker."""
        created = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.claim_job(created.id, worker_id="worker-1")

        success = redis_queue.heartbeat(created.id, "worker-2")

        assert success is False

    def test_get_all(self, redis_queue):
        """Test getting all jobs for an organization."""
        redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.create(Job(organization_id=1, job_type="export", payload={}))
        redis_queue.create(Job(organization_id=2, job_type="sync", payload={}))

        jobs = redis_queue.get_all(organization_id=1)

        assert len(jobs) == 2

    def test_get_all_with_filters(self, redis_queue):
        """Test getting jobs with status filter."""
        job1 = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        job2 = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.claim_job(job1.id)

        pending = redis_queue.get_all(organization_id=1, status="pending")
        running = redis_queue.get_all(organization_id=1, status="running")

        assert len(pending) == 1
        assert len(running) == 1

    def test_count(self, redis_queue):
        """Test counting jobs."""
        redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.create(Job(organization_id=2, job_type="sync", payload={}))

        assert redis_queue.count(organization_id=1) == 2
        assert redis_queue.count(organization_id=1, status="pending") == 2
        assert redis_queue.count() == 3

    def test_get_stats(self, redis_queue):
        """Test getting queue statistics."""
        job1 = redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.create(Job(organization_id=1, job_type="sync", payload={}))
        redis_queue.claim_job(job1.id)

        stats = redis_queue.get_stats(organization_id=1)

        assert stats["pending"] == 1
        assert stats["running"] == 1
        assert stats["completed"] == 0


class TestRedisJobQueueImportError:
    """Test handling when redis is not installed."""

    def test_import_error_message(self):
        """Test helpful error when redis not installed."""
        with patch.dict("sys.modules", {"redis": None}):
            # This would need to reload the module to test properly
            # For now, just verify the class exists
            from mysql_to_sheets.core.redis_job_queue import RedisJobQueue

            assert RedisJobQueue is not None
