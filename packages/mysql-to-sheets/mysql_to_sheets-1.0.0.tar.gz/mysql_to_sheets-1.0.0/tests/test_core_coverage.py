"""Tests for core modules to increase coverage.

Tests for job_queue, scheduler service, and other core modules.
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.config import Config, reset_config
from mysql_to_sheets.core.job_queue import (
    cancel_job,
    cleanup_stale_jobs,
    complete_job,
    count_jobs,
    delete_old_jobs,
    enqueue_job,
    fail_job,
    get_job_status,
    get_next_job,
    get_queue_stats,
    list_jobs,
    reset_queue,
    retry_job,
)
from mysql_to_sheets.models.jobs import reset_job_repository
from mysql_to_sheets.models.repository import clear_tenant, set_tenant


class TestJobQueue:
    """Tests for job queue service functions."""

    def setup_method(self):
        """Create temp database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_jobs.db")
        reset_job_repository()
        reset_config()
        set_tenant(1)

    def teardown_method(self):
        """Clean up temp files."""
        clear_tenant()
        reset_queue()
        reset_config()
        Path(self.db_path).unlink(missing_ok=True)
        Path(self.temp_dir).rmdir()

    def test_enqueue_job(self):
        """Test enqueueing a job."""
        job = enqueue_job(
            job_type="sync",
            payload={"config_id": 1},
            organization_id=1,
            user_id=42,
            priority=5,
            db_path=self.db_path,
        )

        assert job.id is not None
        assert job.job_type == "sync"
        assert job.status == "pending"
        assert job.priority == 5

    def test_enqueue_job_with_custom_max_attempts(self):
        """Test enqueueing job with custom max attempts."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            max_attempts=5,
            db_path=self.db_path,
        )

        assert job.max_attempts == 5

    def test_get_next_job(self):
        """Test getting next pending job."""
        # Enqueue multiple jobs with different priorities
        enqueue_job(
            job_type="sync",
            payload={"config": "low"},
            organization_id=1,
            priority=1,
            db_path=self.db_path,
        )
        high_priority = enqueue_job(
            job_type="sync",
            payload={"config": "high"},
            organization_id=1,
            priority=10,
            db_path=self.db_path,
        )

        # Should get high priority job first
        next_job = get_next_job(db_path=self.db_path)

        assert next_job is not None
        assert next_job.priority == 10
        assert next_job.status == "running"

    def test_get_next_job_when_none_pending(self):
        """Test getting next job when queue is empty."""
        next_job = get_next_job(db_path=self.db_path)
        assert next_job is None

    def test_complete_job(self):
        """Test completing a job."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        next_job = get_next_job(db_path=self.db_path)

        result = complete_job(
            job_id=next_job.id,
            result={"rows_synced": 100},
            db_path=self.db_path,
        )

        assert result is True

        updated = get_job_status(next_job.id, db_path=self.db_path)
        assert updated.status == "completed"
        assert updated.result["rows_synced"] == 100
        assert updated.completed_at is not None

    def test_complete_nonrunning_job_fails(self):
        """Test that completing non-running job fails."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )

        # Try to complete without claiming
        result = complete_job(
            job_id=job.id,
            result={},
            db_path=self.db_path,
        )

        assert result is False

    def test_fail_job_with_requeue(self):
        """Test failing a job with requeue."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            max_attempts=3,
            db_path=self.db_path,
        )
        next_job = get_next_job(db_path=self.db_path)

        result = fail_job(
            job_id=next_job.id,
            error="Connection timeout",
            requeue=True,
            db_path=self.db_path,
        )

        assert result is True

        updated = get_job_status(next_job.id, db_path=self.db_path)
        # Should be requeued since attempts < max_attempts
        assert updated.status == "pending"
        assert updated.attempts == 1
        assert "Connection timeout" in updated.error

    def test_fail_job_exhausted_attempts(self):
        """Test failing job when attempts exhausted."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            max_attempts=1,
            db_path=self.db_path,
        )
        next_job = get_next_job(db_path=self.db_path)

        result = fail_job(
            job_id=next_job.id,
            error="Failed permanently",
            requeue=True,
            db_path=self.db_path,
        )

        assert result is True

        updated = get_job_status(next_job.id, db_path=self.db_path)
        # Should be dead_letter since max_attempts reached (default DLQ behavior)
        assert updated.status == "dead_letter"

    def test_fail_job_without_requeue(self):
        """Test failing job without requeue."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        next_job = get_next_job(db_path=self.db_path)

        result = fail_job(
            job_id=next_job.id,
            error="Fatal error",
            requeue=False,
            db_path=self.db_path,
        )

        assert result is True

        updated = get_job_status(next_job.id, db_path=self.db_path)
        # Default behavior moves to dead_letter queue
        assert updated.status == "dead_letter"

    def test_cancel_job(self):
        """Test cancelling a pending job."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )

        result = cancel_job(job.id, organization_id=1, db_path=self.db_path)

        assert result is True

        updated = get_job_status(job.id, db_path=self.db_path)
        assert updated.status == "cancelled"

    def test_cancel_running_job_fails(self):
        """Test that cancelling running job fails."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        get_next_job(db_path=self.db_path)  # Claim it

        result = cancel_job(job.id, organization_id=1, db_path=self.db_path)

        assert result is False

    def test_retry_job(self):
        """Test retrying a failed job."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        next_job = get_next_job(db_path=self.db_path)
        # Use move_to_dlq=False to keep status as "failed" for retry_job to work
        fail_job(next_job.id, error="Temp error", requeue=False, move_to_dlq=False, db_path=self.db_path)

        retried = retry_job(job.id, organization_id=1, db_path=self.db_path)

        assert retried is not None
        assert retried.status == "pending"
        assert retried.attempts == 0  # Reset attempts
        assert retried.error is None

    def test_retry_nonfailed_job_fails(self):
        """Test that retrying non-failed job fails."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )

        retried = retry_job(job.id, organization_id=1, db_path=self.db_path)

        assert retried is None

    def test_get_job_status(self):
        """Test getting job status."""
        job = enqueue_job(
            job_type="sync",
            payload={"test": "data"},
            organization_id=1,
            db_path=self.db_path,
        )

        status = get_job_status(job.id, organization_id=1, db_path=self.db_path)

        assert status is not None
        assert status.id == job.id
        assert status.payload == {"test": "data"}

    def test_list_jobs(self):
        """Test listing jobs."""
        for i in range(3):
            enqueue_job(
                job_type="sync",
                payload={"index": i},
                organization_id=1,
                db_path=self.db_path,
            )

        jobs = list_jobs(organization_id=1, db_path=self.db_path)

        assert len(jobs) == 3

    def test_list_jobs_with_status_filter(self):
        """Test listing jobs filtered by status."""
        job1 = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        job2 = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )

        # Complete one job
        next_job = get_next_job(db_path=self.db_path)
        complete_job(next_job.id, result={}, db_path=self.db_path)

        pending_jobs = list_jobs(
            organization_id=1,
            status="pending",
            db_path=self.db_path,
        )
        completed_jobs = list_jobs(
            organization_id=1,
            status="completed",
            db_path=self.db_path,
        )

        assert len(pending_jobs) == 1
        assert len(completed_jobs) == 1

    def test_list_jobs_with_type_filter(self):
        """Test listing jobs filtered by type."""
        enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        enqueue_job(
            job_type="export",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )

        sync_jobs = list_jobs(
            organization_id=1,
            job_type="sync",
            db_path=self.db_path,
        )

        assert len(sync_jobs) == 1
        assert sync_jobs[0].job_type == "sync"

    def test_list_jobs_with_pagination(self):
        """Test listing jobs with pagination."""
        for i in range(5):
            enqueue_job(
                job_type="sync",
                payload={},
                organization_id=1,
                db_path=self.db_path,
            )

        page1 = list_jobs(
            organization_id=1,
            limit=2,
            offset=0,
            db_path=self.db_path,
        )
        page2 = list_jobs(
            organization_id=1,
            limit=2,
            offset=2,
            db_path=self.db_path,
        )

        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    def test_count_jobs(self):
        """Test counting jobs."""
        for i in range(3):
            enqueue_job(
                job_type="sync",
                payload={},
                organization_id=1,
                db_path=self.db_path,
            )

        total = count_jobs(organization_id=1, db_path=self.db_path)

        assert total == 3

    def test_count_jobs_by_status(self):
        """Test counting jobs by status."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )

        # Complete one
        next_job = get_next_job(db_path=self.db_path)
        complete_job(next_job.id, result={}, db_path=self.db_path)

        pending_count = count_jobs(
            organization_id=1,
            status="pending",
            db_path=self.db_path,
        )
        completed_count = count_jobs(
            organization_id=1,
            status="completed",
            db_path=self.db_path,
        )

        assert pending_count == 1
        assert completed_count == 1

    def test_cleanup_stale_jobs(self):
        """Test cleaning up stale running jobs."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        next_job = get_next_job(db_path=self.db_path)

        # Manually set started_at to simulate stale job
        from mysql_to_sheets.models.jobs import get_job_repository

        repo = get_job_repository(self.db_path)
        session = repo._get_session()
        from mysql_to_sheets.models.jobs import JobModel

        job_model = session.query(JobModel).filter_by(id=next_job.id).first()
        job_model.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        session.commit()
        session.close()

        # Cleanup with 1 hour timeout
        count = cleanup_stale_jobs(timeout_seconds=3600, db_path=self.db_path)

        assert count == 1

        updated = get_job_status(next_job.id, db_path=self.db_path)
        assert updated.status == "failed"

    def test_delete_old_jobs(self):
        """Test deleting old jobs."""
        job = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        next_job = get_next_job(db_path=self.db_path)
        complete_job(next_job.id, result={}, db_path=self.db_path)

        # Manually set completed_at to simulate old job
        from mysql_to_sheets.models.jobs import get_job_repository

        repo = get_job_repository(self.db_path)
        session = repo._get_session()
        from mysql_to_sheets.models.jobs import JobModel

        job_model = session.query(JobModel).filter_by(id=next_job.id).first()
        job_model.completed_at = datetime.now(timezone.utc) - timedelta(days=60)
        session.commit()
        session.close()

        # Delete jobs older than 30 days
        count = delete_old_jobs(days=30, db_path=self.db_path)

        assert count == 1

    def test_get_queue_stats(self):
        """Test getting queue statistics."""
        # Create jobs with different statuses
        job1 = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        job2 = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )
        job3 = enqueue_job(
            job_type="sync",
            payload={},
            organization_id=1,
            db_path=self.db_path,
        )

        # One running
        next_job = get_next_job(db_path=self.db_path)

        # One completed
        next_job2 = get_next_job(db_path=self.db_path)
        complete_job(next_job2.id, result={}, db_path=self.db_path)

        stats = get_queue_stats(organization_id=1, db_path=self.db_path)

        assert stats["pending"] == 1
        assert stats["running"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 0
        assert stats["cancelled"] == 0


class TestSchedulerService:
    """Tests for SchedulerService."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_scheduler.db")
        reset_config()

    def teardown_method(self):
        """Clean up."""
        from mysql_to_sheets.core.scheduler.service import reset_scheduler_service

        reset_scheduler_service()
        reset_config()
        Path(self.db_path).unlink(missing_ok=True)
        Path(self.temp_dir).rmdir()

    def test_scheduler_service_creation(self):
        """Test creating scheduler service."""
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
        )

        service = SchedulerService(config=config, repository=repo)

        assert service is not None
        assert service.is_running is False

    def test_scheduler_get_status(self):
        """Test getting scheduler status."""
        from mysql_to_sheets.core.scheduler.models import ScheduledJob
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
        )

        service = SchedulerService(config=config, repository=repo)

        # Add some jobs
        job1 = ScheduledJob(
            name="job1",
            cron_expression="0 * * * *",
            sheet_id="ABC",
            sql_query="SELECT 1",
            enabled=True,
        )
        job2 = ScheduledJob(
            name="job2",
            interval_minutes=30,
            sheet_id="DEF",
            sql_query="SELECT 2",
            enabled=False,
        )
        repo.create(job1)
        repo.create(job2)

        status = service.get_status()

        assert status["running"] is False
        assert status["total_jobs"] == 2
        assert status["enabled_jobs"] == 1
        assert status["disabled_jobs"] == 1

    def test_scheduler_start(self):
        """Test starting scheduler."""
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
            freshness_check_interval_minutes=0,  # Disable freshness check
        )

        service = SchedulerService(config=config, repository=repo)

        # Mock the scheduler
        mock_scheduler = MagicMock()
        service._scheduler = mock_scheduler

        service.start()

        assert service.is_running is True
        mock_scheduler.start.assert_called_once()

    def test_scheduler_stop(self):
        """Test stopping scheduler."""
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
            freshness_check_interval_minutes=0,
        )

        service = SchedulerService(config=config, repository=repo)

        # Mock the scheduler
        mock_scheduler = MagicMock()
        service._scheduler = mock_scheduler
        service._running = True

        service.stop()

        assert service.is_running is False
        mock_scheduler.shutdown.assert_called_once()

    def test_scheduler_add_job(self):
        """Test adding a scheduled job."""
        from mysql_to_sheets.core.scheduler.models import ScheduledJob
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
        )

        service = SchedulerService(config=config, repository=repo)

        job = ScheduledJob(
            name="test-job",
            cron_expression="0 6 * * *",
            sheet_id="ABC123",
            sql_query="SELECT * FROM users",
        )

        created = service.add_job(job)

        assert created.id is not None
        assert created.name == "test-job"

    def test_scheduler_add_duplicate_job_fails(self):
        """Test that adding duplicate job name fails."""
        from mysql_to_sheets.core.exceptions import SchedulerError
        from mysql_to_sheets.core.scheduler.models import ScheduledJob
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
        )

        service = SchedulerService(config=config, repository=repo)

        job1 = ScheduledJob(
            name="duplicate",
            cron_expression="0 6 * * *",
            sheet_id="ABC123",
            sql_query="SELECT 1",
        )
        service.add_job(job1)

        job2 = ScheduledJob(
            name="duplicate",
            cron_expression="0 7 * * *",
            sheet_id="DEF456",
            sql_query="SELECT 2",
        )

        with pytest.raises(SchedulerError, match="already exists"):
            service.add_job(job2)

    def test_scheduler_update_job(self):
        """Test updating a scheduled job."""
        from mysql_to_sheets.core.scheduler.models import ScheduledJob
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
        )

        service = SchedulerService(config=config, repository=repo)

        job = ScheduledJob(
            name="update-test",
            cron_expression="0 6 * * *",
            sheet_id="ABC123",
            sql_query="SELECT 1",
        )
        created = service.add_job(job)

        created.cron_expression = "0 7 * * *"
        created.sql_query = "SELECT 2"

        updated = service.update_job(created)

        assert updated.cron_expression == "0 7 * * *"
        assert updated.sql_query == "SELECT 2"

    def test_scheduler_delete_job(self):
        """Test deleting a scheduled job."""
        from mysql_to_sheets.core.scheduler.models import ScheduledJob
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
        )

        service = SchedulerService(config=config, repository=repo)

        job = ScheduledJob(
            name="delete-test",
            cron_expression="0 6 * * *",
            sheet_id="ABC123",
            sql_query="SELECT 1",
        )
        created = service.add_job(job)

        result = service.delete_job(created.id)

        assert result is True
        assert service.get_job(created.id) is None

    def test_scheduler_enable_disable_job(self):
        """Test enabling and disabling jobs."""
        from mysql_to_sheets.core.scheduler.models import ScheduledJob
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
        )

        service = SchedulerService(config=config, repository=repo)

        job = ScheduledJob(
            name="toggle-test",
            cron_expression="0 6 * * *",
            sheet_id="ABC123",
            sql_query="SELECT 1",
            enabled=True,
        )
        created = service.add_job(job)

        # Disable
        disabled = service.disable_job(created.id)
        assert disabled.enabled is False

        # Enable
        enabled = service.enable_job(created.id)
        assert enabled.enabled is True

    def test_scheduler_get_all_jobs(self):
        """Test getting all jobs."""
        from mysql_to_sheets.core.scheduler.models import ScheduledJob
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
        )

        service = SchedulerService(config=config, repository=repo)

        for i in range(3):
            job = ScheduledJob(
                name=f"job-{i}",
                cron_expression="0 6 * * *",
                sheet_id="ABC123",
                sql_query=f"SELECT {i}",
                enabled=(i < 2),
            )
            service.add_job(job)

        all_jobs = service.get_all_jobs(include_disabled=True)
        enabled_only = service.get_all_jobs(include_disabled=False)

        assert len(all_jobs) == 3
        assert len(enabled_only) == 2

    @patch("mysql_to_sheets.core.sync.run_sync")
    def test_scheduler_trigger_job(self, mock_run_sync):
        """Test manually triggering a job."""
        from mysql_to_sheets.core.scheduler.models import ScheduledJob
        from mysql_to_sheets.core.scheduler.repository import SQLiteScheduleRepository
        from mysql_to_sheets.core.scheduler.service import SchedulerService
        from mysql_to_sheets.core.sync import SyncResult

        # Mock successful sync
        mock_run_sync.return_value = SyncResult(
            success=True,
            rows_synced=100,
            message="Success",
        )

        repo = SQLiteScheduleRepository(self.db_path)
        config = Config(
            db_user="test",
            db_password="test",
            db_name="test",
            google_sheet_id="ABC123",
            sql_query="SELECT 1",
            scheduler_db_path=self.db_path,
        )

        service = SchedulerService(config=config, repository=repo)

        job = ScheduledJob(
            name="trigger-test",
            cron_expression="0 6 * * *",
            sheet_id="ABC123",
            sql_query="SELECT 1",
        )
        created = service.add_job(job)

        service.trigger_job(created.id)

        # Verify sync was called
        mock_run_sync.assert_called_once()

        # Verify last run was updated
        updated_job = service.get_job(created.id)
        assert updated_job.last_run_at is not None
