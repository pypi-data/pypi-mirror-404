"""Tests for the scheduler system."""

import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from mysql_to_sheets.core.exceptions import SchedulerError
from mysql_to_sheets.core.scheduler.models import JobStatus, ScheduledJob
from mysql_to_sheets.core.scheduler.repository import (
    SQLiteScheduleRepository,
    get_schedule_repository,
    reset_schedule_repository,
)
from mysql_to_sheets.core.scheduler.service import (
    SchedulerService,
    reset_scheduler_service,
)


class TestScheduledJob:
    """Tests for ScheduledJob dataclass."""

    def test_create_cron_job(self):
        """Test creating a cron-scheduled job."""
        job = ScheduledJob(
            name="daily-sync",
            cron_expression="0 6 * * *",
        )

        assert job.name == "daily-sync"
        assert job.cron_expression == "0 6 * * *"
        assert job.interval_minutes is None
        assert job.enabled is True
        assert job.schedule_type == "cron"

    def test_create_interval_job(self):
        """Test creating an interval-scheduled job."""
        job = ScheduledJob(
            name="hourly-sync",
            interval_minutes=60,
        )

        assert job.name == "hourly-sync"
        assert job.interval_minutes == 60
        assert job.cron_expression is None
        assert job.schedule_type == "interval"

    def test_schedule_display_cron(self):
        """Test schedule display for cron job."""
        job = ScheduledJob(
            name="test",
            cron_expression="0 6 * * *",
        )
        assert "Cron:" in job.schedule_display

    def test_schedule_display_interval_minutes(self):
        """Test schedule display for interval job in minutes."""
        job = ScheduledJob(
            name="test",
            interval_minutes=30,
        )
        assert "30 minutes" in job.schedule_display

    def test_schedule_display_interval_hours(self):
        """Test schedule display for interval job in hours."""
        job = ScheduledJob(
            name="test",
            interval_minutes=120,
        )
        assert "2 hour" in job.schedule_display

    def test_status_pending(self):
        """Test pending status for new job."""
        job = ScheduledJob(name="test", cron_expression="* * * * *")
        assert job.status == JobStatus.PENDING

    def test_status_success(self):
        """Test success status after successful run."""
        job = ScheduledJob(
            name="test",
            cron_expression="* * * * *",
            last_run_at=datetime.now(timezone.utc),
            last_run_success=True,
        )
        assert job.status == JobStatus.SUCCESS

    def test_status_failed(self):
        """Test failed status after failed run."""
        job = ScheduledJob(
            name="test",
            cron_expression="* * * * *",
            last_run_at=datetime.now(timezone.utc),
            last_run_success=False,
        )
        assert job.status == JobStatus.FAILED

    def test_status_disabled(self):
        """Test disabled status."""
        job = ScheduledJob(
            name="test",
            cron_expression="* * * * *",
            enabled=False,
        )
        assert job.status == JobStatus.DISABLED

    def test_validate_valid_cron(self):
        """Test validation of valid cron job."""
        job = ScheduledJob(
            name="test",
            cron_expression="0 6 * * *",
        )
        errors = job.validate()
        assert len(errors) == 0

    def test_validate_valid_interval(self):
        """Test validation of valid interval job."""
        job = ScheduledJob(
            name="test",
            interval_minutes=60,
        )
        errors = job.validate()
        assert len(errors) == 0

    def test_validate_missing_name(self):
        """Test validation error for missing name."""
        job = ScheduledJob(
            name="",
            cron_expression="* * * * *",
        )
        errors = job.validate()
        assert any("name" in e.lower() for e in errors)

    def test_validate_missing_schedule(self):
        """Test validation error for missing schedule."""
        job = ScheduledJob(name="test")
        errors = job.validate()
        assert any("cron" in e.lower() or "interval" in e.lower() for e in errors)

    def test_validate_both_schedules(self):
        """Test validation error for both cron and interval."""
        job = ScheduledJob(
            name="test",
            cron_expression="* * * * *",
            interval_minutes=60,
        )
        errors = job.validate()
        assert any("both" in e.lower() for e in errors)

    def test_validate_invalid_interval(self):
        """Test validation error for invalid interval."""
        job = ScheduledJob(
            name="test",
            interval_minutes=0,
        )
        errors = job.validate()
        assert any("interval" in e.lower() for e in errors)

    def test_to_dict(self):
        """Test converting job to dictionary."""
        job = ScheduledJob(
            id=1,
            name="test",
            cron_expression="0 6 * * *",
            sheet_id="abc123",
        )
        data = job.to_dict()

        assert data["id"] == 1
        assert data["name"] == "test"
        assert data["cron_expression"] == "0 6 * * *"
        assert data["sheet_id"] == "abc123"
        assert "status" in data

    def test_from_dict(self):
        """Test creating job from dictionary."""
        data = {
            "id": 1,
            "name": "test",
            "cron_expression": "0 6 * * *",
            "enabled": True,
        }
        job = ScheduledJob.from_dict(data)

        assert job.id == 1
        assert job.name == "test"
        assert job.cron_expression == "0 6 * * *"


class TestSQLiteScheduleRepository:
    """Tests for SQLiteScheduleRepository."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass

    @pytest.fixture
    def repository(self, temp_db):
        """Create a repository with temporary database."""
        return SQLiteScheduleRepository(temp_db)

    def test_create_job(self, repository):
        """Test creating a job."""
        job = ScheduledJob(
            name="test-job",
            cron_expression="0 6 * * *",
        )

        created = repository.create(job)

        assert created.id is not None
        assert created.name == "test-job"
        assert created.cron_expression == "0 6 * * *"

    def test_get_by_id(self, repository):
        """Test getting job by ID."""
        job = ScheduledJob(name="test", cron_expression="* * * * *")
        created = repository.create(job)

        retrieved = repository.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "test"

    def test_get_by_id_not_found(self, repository):
        """Test getting non-existent job."""
        retrieved = repository.get_by_id(9999)
        assert retrieved is None

    def test_get_by_name(self, repository):
        """Test getting job by name."""
        job = ScheduledJob(name="unique-name", cron_expression="* * * * *")
        repository.create(job)

        retrieved = repository.get_by_name("unique-name")

        assert retrieved is not None
        assert retrieved.name == "unique-name"

    def test_get_all(self, repository):
        """Test getting all jobs."""
        repository.create(ScheduledJob(name="job1", cron_expression="* * * * *"))
        repository.create(ScheduledJob(name="job2", cron_expression="* * * * *"))
        repository.create(ScheduledJob(name="job3", cron_expression="* * * * *", enabled=False))

        all_enabled = repository.get_all(include_disabled=False)
        all_jobs = repository.get_all(include_disabled=True)

        assert len(all_enabled) == 2
        assert len(all_jobs) == 3

    def test_update_job(self, repository):
        """Test updating a job."""
        job = ScheduledJob(name="original", cron_expression="* * * * *")
        created = repository.create(job)

        created.name = "updated"
        created.interval_minutes = 60
        created.cron_expression = None

        updated = repository.update(created)

        assert updated.name == "updated"
        assert updated.interval_minutes == 60
        assert updated.cron_expression is None

    def test_delete_job(self, repository):
        """Test deleting a job."""
        job = ScheduledJob(name="to-delete", cron_expression="* * * * *")
        created = repository.create(job)

        result = repository.delete(created.id)
        retrieved = repository.get_by_id(created.id)

        assert result is True
        assert retrieved is None

    def test_delete_nonexistent(self, repository):
        """Test deleting non-existent job."""
        result = repository.delete(9999)
        assert result is False

    def test_update_last_run(self, repository):
        """Test updating last run information."""
        job = ScheduledJob(name="test", cron_expression="* * * * *")
        created = repository.create(job)

        repository.update_last_run(
            job_id=created.id,
            success=True,
            message="Synced 100 rows",
            rows=100,
            duration_ms=1500.5,
        )

        retrieved = repository.get_by_id(created.id)

        assert retrieved.last_run_at is not None
        assert retrieved.last_run_success is True
        assert retrieved.last_run_message == "Synced 100 rows"
        assert retrieved.last_run_rows == 100
        assert retrieved.last_run_duration_ms == 1500.5

    def test_update_next_run(self, repository):
        """Test updating next run time."""
        job = ScheduledJob(name="test", cron_expression="* * * * *")
        created = repository.create(job)

        next_run = datetime(2025, 1, 1, 6, 0, 0)
        repository.update_next_run(created.id, next_run)

        retrieved = repository.get_by_id(created.id)
        assert retrieved.next_run_at == next_run


class TestSchedulerService:
    """Tests for SchedulerService."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass

    @pytest.fixture
    def mock_config(self, temp_db):
        """Create a mock config."""
        config = MagicMock()
        config.scheduler_db_path = temp_db
        config.scheduler_timezone = "UTC"
        return config

    @pytest.fixture
    def service(self, mock_config):
        """Create a scheduler service."""
        reset_scheduler_service()
        repository = SQLiteScheduleRepository(mock_config.scheduler_db_path)
        return SchedulerService(config=mock_config, repository=repository)

    def test_add_job(self, service):
        """Test adding a job."""
        job = ScheduledJob(
            name="test-job",
            cron_expression="0 6 * * *",
        )

        created = service.add_job(job)

        assert created.id is not None
        assert created.name == "test-job"

    def test_add_job_invalid(self, service):
        """Test adding invalid job raises error."""
        job = ScheduledJob(name="")  # Invalid: no name

        with pytest.raises(SchedulerError):
            service.add_job(job)

    def test_add_job_duplicate_name(self, service):
        """Test adding job with duplicate name raises error."""
        job1 = ScheduledJob(name="unique", cron_expression="* * * * *")
        job2 = ScheduledJob(name="unique", interval_minutes=60)

        service.add_job(job1)

        with pytest.raises(SchedulerError) as exc_info:
            service.add_job(job2)

        assert "already exists" in str(exc_info.value)

    def test_get_job(self, service):
        """Test getting a job."""
        job = ScheduledJob(name="test", cron_expression="* * * * *")
        created = service.add_job(job)

        retrieved = service.get_job(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_job_by_name(self, service):
        """Test getting a job by name."""
        job = ScheduledJob(name="findme", cron_expression="* * * * *")
        service.add_job(job)

        retrieved = service.get_job_by_name("findme")

        assert retrieved is not None
        assert retrieved.name == "findme"

    def test_get_all_jobs(self, service):
        """Test getting all jobs."""
        service.add_job(ScheduledJob(name="job1", cron_expression="* * * * *"))
        service.add_job(ScheduledJob(name="job2", cron_expression="* * * * *"))

        jobs = service.get_all_jobs()

        assert len(jobs) == 2

    def test_update_job(self, service):
        """Test updating a job."""
        job = ScheduledJob(name="original", cron_expression="* * * * *")
        created = service.add_job(job)

        created.name = "updated"
        updated = service.update_job(created)

        assert updated.name == "updated"

    def test_delete_job(self, service):
        """Test deleting a job."""
        job = ScheduledJob(name="to-delete", cron_expression="* * * * *")
        created = service.add_job(job)

        result = service.delete_job(created.id)

        assert result is True
        assert service.get_job(created.id) is None

    def test_enable_job(self, service):
        """Test enabling a job."""
        job = ScheduledJob(name="test", cron_expression="* * * * *", enabled=False)
        created = service.add_job(job)

        enabled = service.enable_job(created.id)

        assert enabled.enabled is True

    def test_disable_job(self, service):
        """Test disabling a job."""
        job = ScheduledJob(name="test", cron_expression="* * * * *", enabled=True)
        created = service.add_job(job)

        disabled = service.disable_job(created.id)

        assert disabled.enabled is False

    def test_enable_nonexistent_raises(self, service):
        """Test enabling non-existent job raises error."""
        with pytest.raises(SchedulerError):
            service.enable_job(9999)

    def test_get_status(self, service):
        """Test getting scheduler status."""
        service.add_job(ScheduledJob(name="job1", cron_expression="* * * * *"))
        service.add_job(ScheduledJob(name="job2", cron_expression="* * * * *", enabled=False))

        status = service.get_status()

        assert "running" in status
        assert status["total_jobs"] == 2
        assert status["enabled_jobs"] == 1
        assert status["disabled_jobs"] == 1

    def test_is_running_initially_false(self, service):
        """Test that scheduler is not running initially."""
        assert service.is_running is False


class TestSchedulerSingleton:
    """Tests for scheduler singleton functions."""

    def setup_method(self):
        """Reset singletons before each test."""
        reset_schedule_repository()
        reset_scheduler_service()

    def test_get_schedule_repository_singleton(self):
        """Test that get_schedule_repository returns singleton."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo1 = get_schedule_repository(db_path)
            repo2 = get_schedule_repository(db_path)

            assert repo1 is repo2
        finally:
            reset_schedule_repository()
            try:
                os.unlink(db_path)
            except OSError:
                pass
