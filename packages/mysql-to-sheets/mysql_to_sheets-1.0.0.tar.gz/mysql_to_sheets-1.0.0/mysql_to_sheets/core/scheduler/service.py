"""Scheduler service wrapping APScheduler.

This module provides the SchedulerService class that manages
scheduled sync jobs using APScheduler as the underlying scheduler.
"""

import time
from typing import Any

from mysql_to_sheets.core.config import Config, get_config
from mysql_to_sheets.core.exceptions import SchedulerError
from mysql_to_sheets.core.logging_utils import get_module_logger
from mysql_to_sheets.core.scheduler.models import ScheduledJob
from mysql_to_sheets.core.scheduler.repository import (
    SQLiteScheduleRepository,
    get_schedule_repository,
)

logger = get_module_logger(__name__)


class SchedulerService:
    """Service for managing scheduled sync jobs.

    This class wraps APScheduler to provide cron and interval-based
    scheduling of sync operations. It loads job configurations from
    the database and manages the scheduler lifecycle.
    """

    def __init__(
        self,
        config: Config | None = None,
        repository: SQLiteScheduleRepository | None = None,
    ) -> None:
        """Initialize scheduler service.

        Args:
            config: Configuration object. If None, loads from environment.
            repository: Schedule repository. If None, creates from config.
        """
        self.config = config or get_config()
        self.repository = repository or get_schedule_repository(self.config.scheduler_db_path)
        self._scheduler: Any = None  # APScheduler instance
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running.

        Returns:
            True if scheduler is running.
        """
        return self._running and self._scheduler is not None

    def _get_scheduler(self) -> Any:
        """Get or create APScheduler instance.

        Returns:
            APScheduler BackgroundScheduler instance.

        Raises:
            SchedulerError: If APScheduler is not installed.
        """
        if self._scheduler is None:
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from apscheduler.triggers.cron import CronTrigger
                from apscheduler.triggers.interval import IntervalTrigger
            except ImportError as e:
                raise SchedulerError(
                    message="APScheduler is required for scheduling. Install with: pip install APScheduler",
                    original_error=e,
                ) from e

            self._scheduler = BackgroundScheduler(
                timezone=self.config.scheduler_timezone,
            )

        return self._scheduler

    def start(self) -> None:
        """Start the scheduler.

        Loads all enabled jobs from the database and starts the
        APScheduler background thread.
        """
        if self._running:
            logger.warning("Scheduler is already running")
            return

        logger.info("Starting scheduler...")
        scheduler = self._get_scheduler()

        # Load all enabled jobs
        jobs = self.repository.get_all(include_disabled=False)
        for job in jobs:
            self._add_job_to_scheduler(job)

        # Add freshness check job if configured
        self._add_freshness_check_job()

        # Add trial expiration check job
        self._add_trial_check_job()

        # Add agent stale cleanup job
        self._add_agent_cleanup_job()

        # Add crash report retention cleanup job
        self._add_crash_report_cleanup_job()

        scheduler.start()
        self._running = True
        logger.info(f"Scheduler started with {len(jobs)} job(s)")

    def stop(self, wait: bool = True) -> None:
        """Stop the scheduler.

        Args:
            wait: Whether to wait for running jobs to complete.
        """
        if not self._running or self._scheduler is None:
            return

        logger.info("Stopping scheduler...")
        self._scheduler.shutdown(wait=wait)
        self._running = False
        self._scheduler = None
        logger.info("Scheduler stopped")

    def _add_job_to_scheduler(self, job: ScheduledJob) -> None:
        """Add a job to the APScheduler.

        Args:
            job: Job to add.
        """
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = self._get_scheduler()
        job_id = f"sync_job_{job.id}"

        # Remove existing job if present
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        if not job.enabled:
            return

        # Create trigger based on job type
        if job.cron_expression:
            trigger = CronTrigger.from_crontab(
                job.cron_expression,
                timezone=self.config.scheduler_timezone,
            )
        elif job.interval_minutes:
            trigger = IntervalTrigger(
                minutes=job.interval_minutes,
                timezone=self.config.scheduler_timezone,
            )
        else:
            logger.warning(f"Job {job.name} has no schedule configured")
            return

        # Add job to scheduler
        # misfire_grace_time: allow missed jobs to run if within 15 minutes of schedule
        # coalesce: if multiple runs were missed, execute only once
        scheduler.add_job(
            self._execute_job,
            trigger=trigger,
            id=job_id,
            name=job.name,
            args=[job.id],
            replace_existing=True,
            misfire_grace_time=900,
            coalesce=True,
        )

        # Update next run time
        apscheduler_job = scheduler.get_job(job_id)
        if apscheduler_job and apscheduler_job.next_run_time and job.id is not None:
            next_run = apscheduler_job.next_run_time.replace(tzinfo=None)
            self.repository.update_next_run(job.id, next_run)

        logger.info(f"Added job '{job.name}' to scheduler")

    def _add_freshness_check_job(self) -> None:
        """Add the freshness check job to the scheduler.

        This job runs periodically to check data freshness and send alerts.
        """
        from apscheduler.triggers.interval import IntervalTrigger

        if self.config.freshness_check_interval_minutes <= 0:
            logger.debug("Freshness check disabled (interval <= 0)")
            return

        scheduler = self._get_scheduler()
        job_id = "freshness_check"

        # Remove existing job if present
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        trigger = IntervalTrigger(
            minutes=self.config.freshness_check_interval_minutes,
            timezone=self.config.scheduler_timezone,
        )

        scheduler.add_job(
            self._execute_freshness_check,
            trigger=trigger,
            id=job_id,
            name="Freshness Check",
            replace_existing=True,
        )

        logger.info(
            f"Added freshness check job (every {self.config.freshness_check_interval_minutes} minutes)"
        )

    def _execute_freshness_check(self) -> None:
        """Execute the freshness check job.

        Checks all organizations for stale sync configs and sends alerts.
        """
        logger.debug("Running freshness check...")
        try:
            from mysql_to_sheets.core.freshness_alerts import check_and_alert_all
            from mysql_to_sheets.core.tenant import get_tenant_db_path

            db_path = get_tenant_db_path()
            all_alerts = check_and_alert_all(db_path=db_path, send_notifications=True)

            total_alerts = sum(len(a) for a in all_alerts.values())
            if total_alerts > 0:
                logger.info(f"Freshness check: {total_alerts} alert(s) triggered")
            else:
                logger.debug("Freshness check: no alerts")

        except (ImportError, OSError, RuntimeError) as e:
            logger.error(f"Freshness check failed: {e}")

    def _add_trial_check_job(self) -> None:
        """Add the trial expiration check job to the scheduler.

        This job runs daily at 9 AM to check for expiring trials
        and auto-expire trials that have ended.
        """
        from apscheduler.triggers.cron import CronTrigger

        scheduler = self._get_scheduler()
        job_id = "trial_expiration_check"

        # Remove existing job if present
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        # Run daily at 9 AM in configured timezone
        trigger = CronTrigger(
            hour=9,
            minute=0,
            timezone=self.config.scheduler_timezone,
        )

        scheduler.add_job(
            self._execute_trial_expiration_check,
            trigger=trigger,
            id=job_id,
            name="Trial Expiration Check",
            replace_existing=True,
        )

        logger.info("Added trial expiration check job (daily at 9 AM)")

    def _execute_trial_expiration_check(self) -> None:
        """Execute the trial expiration check job.

        Checks for trials expiring in 3, 1, or 0 days and sends
        appropriate notifications. Auto-expires trials that have ended.
        """
        logger.debug("Running trial expiration check...")
        try:
            from datetime import datetime, timezone

            from mysql_to_sheets.core.tenant import get_tenant_db_path
            from mysql_to_sheets.core.trial import check_expiring_trials, expire_trial
            from mysql_to_sheets.models.organizations import get_organization_repository

            db_path = get_tenant_db_path()

            # Check for trials expiring in 3 days (sends webhook notification)
            expiring_3d = check_expiring_trials(days_threshold=3, db_path=db_path)
            if expiring_3d:
                logger.info(f"Trial check: {len(expiring_3d)} trial(s) expiring within 3 days")

            # Check for trials expiring in 1 day
            expiring_1d = check_expiring_trials(days_threshold=1, db_path=db_path)
            if expiring_1d:
                logger.info(f"Trial check: {len(expiring_1d)} trial(s) expiring within 1 day")

            # Auto-expire trials that have ended
            org_repo = get_organization_repository(db_path)
            orgs = org_repo.get_all(include_inactive=False)
            now = datetime.now(timezone.utc)
            expired_count = 0

            for org in orgs:
                if org.billing_status == "trialing" and org.trial_ends_at:
                    trial_end = org.trial_ends_at
                    if trial_end.tzinfo is None:
                        trial_end = trial_end.replace(tzinfo=timezone.utc)

                    if trial_end <= now:
                        try:
                            if org.id is not None:
                                expire_trial(org.id, db_path=db_path)
                                expired_count += 1
                                logger.info(f"Auto-expired trial for org {org.id} ({org.slug})")
                        except (ImportError, OSError, RuntimeError) as e:
                            logger.error(f"Failed to expire trial for org {org.id}: {e}")

            if expired_count > 0:
                logger.info(f"Trial check: auto-expired {expired_count} trial(s)")
            else:
                logger.debug("Trial check: no trials to expire")

        except (ImportError, OSError, RuntimeError) as e:
            logger.error(f"Trial expiration check failed: {e}")

    def _add_agent_cleanup_job(self) -> None:
        """Add the agent stale cleanup job to the scheduler.

        This job runs periodically to mark agents that haven't sent
        a heartbeat as offline. Emits webhooks for state changes.
        """
        from apscheduler.triggers.interval import IntervalTrigger

        if self.config.agent_cleanup_interval_seconds <= 0:
            logger.debug("Agent cleanup disabled (interval <= 0)")
            return

        scheduler = self._get_scheduler()
        job_id = "agent_cleanup"

        # Remove existing job if present
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        trigger = IntervalTrigger(
            seconds=self.config.agent_cleanup_interval_seconds,
            timezone=self.config.scheduler_timezone,
        )

        scheduler.add_job(
            self._execute_agent_cleanup,
            trigger=trigger,
            id=job_id,
            name="Agent Stale Cleanup",
            replace_existing=True,
        )

        logger.info(
            f"Added agent cleanup job (every {self.config.agent_cleanup_interval_seconds}s)"
        )

    def _execute_agent_cleanup(self) -> None:
        """Execute the agent stale cleanup job.

        Marks agents that haven't sent a heartbeat within the timeout
        as offline and emits webhooks for state transitions.
        """
        logger.debug("Running agent stale cleanup...")
        try:
            from mysql_to_sheets.core.tenant import get_tenant_db_path
            from mysql_to_sheets.models.agents import get_agent_repository

            db_path = get_tenant_db_path()
            repo = get_agent_repository(db_path)

            # Get stale agents and mark them offline
            stale_agents = repo.cleanup_stale_with_list(
                self.config.agent_stale_timeout_seconds
            )

            if stale_agents:
                logger.info(f"Agent cleanup: marked {len(stale_agents)} agent(s) as offline")

                # Emit webhooks for each stale agent
                self._emit_agent_stale_webhooks(stale_agents, db_path)
            else:
                logger.debug("Agent cleanup: no stale agents")

        except (ImportError, OSError, RuntimeError) as e:
            logger.error(f"Agent cleanup failed: {e}")

    def _emit_agent_stale_webhooks(
        self, agents: list[Any], db_path: str
    ) -> None:
        """Emit webhooks for agents that went stale.

        Args:
            agents: List of Agent dataclasses that were marked offline.
            db_path: Path to tenant database.
        """
        try:
            from mysql_to_sheets.core.webhooks.delivery import deliver_webhook
            from mysql_to_sheets.core.webhooks.payload import create_agent_payload
            from mysql_to_sheets.models.webhooks import get_webhook_repository

            webhook_repo = get_webhook_repository(db_path)

            for agent in agents:
                org_id = agent.organization_id

                # Get webhooks for this organization that listen to agent events
                org_webhooks = webhook_repo.get_all(
                    organization_id=org_id,
                    enabled=True,
                )

                for webhook in org_webhooks:
                    events = webhook.events or []
                    if "agent.stale" in events or "agent.*" in events:
                        payload = create_agent_payload(
                            event="agent.stale",
                            agent_id=agent.agent_id,
                            organization_id=org_id,
                            hostname=agent.hostname,
                            previous_status="online" if agent.status != "busy" else "busy",
                            new_status="offline",
                            last_seen_at=agent.last_seen_at,
                            offline_reason="heartbeat_timeout",
                        )
                        try:
                            deliver_webhook(
                                webhook=webhook,
                                payload=payload,
                                db_path=db_path,
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to deliver agent.stale webhook for {agent.agent_id}: {e}"
                            )

        except (ImportError, OSError) as e:
            logger.debug(f"Webhook delivery skipped: {e}")

    def _add_crash_report_cleanup_job(self) -> None:
        """Add the crash report retention cleanup job to the scheduler.

        This job runs daily at 3 AM to delete crash reports older than
        the configured retention period.
        """
        from apscheduler.triggers.cron import CronTrigger

        if self.config.crash_report_retention_days <= 0:
            logger.debug("Crash report cleanup disabled (retention <= 0)")
            return

        scheduler = self._get_scheduler()
        job_id = "crash_report_cleanup"

        # Remove existing job if present
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        # Run daily at 3 AM in configured timezone
        trigger = CronTrigger(
            hour=3,
            minute=0,
            timezone=self.config.scheduler_timezone,
        )

        scheduler.add_job(
            self._execute_crash_report_cleanup,
            trigger=trigger,
            id=job_id,
            name="Crash Report Cleanup",
            replace_existing=True,
        )

        logger.info(
            f"Added crash report cleanup job (daily at 3 AM, retention={self.config.crash_report_retention_days} days)"
        )

    def _execute_crash_report_cleanup(self) -> None:
        """Execute the crash report retention cleanup job.

        Deletes crash reports older than the configured retention period.
        """
        logger.debug("Running crash report cleanup...")
        try:
            from mysql_to_sheets.core.tenant import get_tenant_db_path
            from mysql_to_sheets.models.crash_reports import get_crash_report_repository

            db_path = get_tenant_db_path()
            repo = get_crash_report_repository(db_path)

            deleted = repo.cleanup_old(self.config.crash_report_retention_days)

            if deleted > 0:
                logger.info(f"Crash report cleanup: deleted {deleted} old report(s)")
            else:
                logger.debug("Crash report cleanup: no old reports to delete")

        except (ImportError, OSError, RuntimeError) as e:
            logger.error(f"Crash report cleanup failed: {e}")

    def _execute_job(self, job_id: int) -> None:
        """Execute a scheduled job.

        Args:
            job_id: ID of the job to execute.
        """
        from mysql_to_sheets.core.scheduler.locks import (
            get_scheduler_lock_backend,
            is_lock_enabled,
            job_lock,
        )

        job = self.repository.get_by_id(job_id)
        if job is None:
            logger.error(f"Job {job_id} not found")
            return

        if not job.enabled:
            logger.info(f"Job '{job.name}' is disabled, skipping")
            return

        # Attempt to acquire lock if locking is enabled
        if is_lock_enabled():
            backend = get_scheduler_lock_backend(self.config.scheduler_db_path)
            with job_lock(
                job_id,
                backend=backend,
                ttl_seconds=self.config.scheduler_lock_ttl_seconds,
                heartbeat_interval=self.config.scheduler_lock_heartbeat_interval,
            ) as lock:
                if lock is None:
                    logger.info(f"Job '{job.name}' is already running (locked), skipping")
                    return
                self._execute_job_impl(job)
        else:
            self._execute_job_impl(job)

    def _execute_job_impl(self, job: ScheduledJob) -> None:
        """Implementation of job execution (called with or without lock).

        Args:
            job: The job to execute.
        """
        logger.info(f"Executing scheduled job: {job.name}")
        start_time = time.time()

        try:
            # Run sync with job overrides
            from mysql_to_sheets.core.sync import run_sync

            # Build config overrides from job
            overrides: dict[str, Any] = {}
            if job.sheet_id:
                overrides["google_sheet_id"] = job.sheet_id
            if job.worksheet_name:
                overrides["google_worksheet_name"] = job.worksheet_name
            if job.sql_query:
                overrides["sql_query"] = job.sql_query

            # Handle notification overrides
            if job.notify_on_success is not None:
                overrides["notify_on_success"] = job.notify_on_success
            if job.notify_on_failure is not None:
                overrides["notify_on_failure"] = job.notify_on_failure

            # Apply overrides to config
            config = self.config
            if overrides:
                config = config.with_overrides(**overrides)

            result = run_sync(
                config=config,
                source="scheduler",
            )

            duration_ms = (time.time() - start_time) * 1000
            job_id = job.id

            # Update job status
            if job_id is not None:
                self.repository.update_last_run(
                    job_id=job_id,
                    success=result.success,
                    message=result.message,
                    rows=result.rows_synced,
                    duration_ms=duration_ms,
                )

                # Update next run time
                scheduler = self._get_scheduler()
                apscheduler_job = scheduler.get_job(f"sync_job_{job_id}")
                if apscheduler_job and apscheduler_job.next_run_time:
                    next_run = apscheduler_job.next_run_time.replace(tzinfo=None)
                    self.repository.update_next_run(job_id, next_run)

            if result.success:
                logger.info(
                    f"Job '{job.name}' completed: {result.rows_synced} rows in {duration_ms:.1f}ms"
                )
            else:
                logger.error(f"Job '{job.name}' failed: {result.error}")

        except Exception as e:  # Scheduler boundary: catch all to record failure
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(f"Job '{job.name}' raised exception: {e}")
            if job.id is not None:
                self.repository.update_last_run(
                    job_id=job.id,
                    success=False,
                    message=str(e),
                    duration_ms=duration_ms,
                )

    def add_job(self, job: ScheduledJob) -> ScheduledJob:
        """Add a new scheduled job.

        Args:
            job: Job configuration.

        Returns:
            Created job with ID.

        Raises:
            SchedulerError: If job validation fails.
        """
        # Validate job
        errors = job.validate()
        if errors:
            raise SchedulerError(
                message=f"Invalid job configuration: {', '.join(errors)}",
                job_name=job.name,
            )

        # Check for duplicate name
        existing = self.repository.get_by_name(job.name)
        if existing:
            raise SchedulerError(
                message=f"Job with name '{job.name}' already exists",
                job_name=job.name,
            )

        # Validate cron expression if provided
        if job.cron_expression:
            try:
                from apscheduler.triggers.cron import CronTrigger

                CronTrigger.from_crontab(job.cron_expression)
            except (ImportError, ValueError) as e:
                raise SchedulerError(
                    message=f"Invalid cron expression: {job.cron_expression}",
                    job_name=job.name,
                    original_error=e,
                )

        # Save to database
        job = self.repository.create(job)

        # Add to scheduler if running
        if self._running:
            self._add_job_to_scheduler(job)

        logger.info(f"Created job '{job.name}' (ID: {job.id})")
        return job

    def update_job(self, job: ScheduledJob) -> ScheduledJob:
        """Update an existing job.

        Args:
            job: Job with updated values.

        Returns:
            Updated job.

        Raises:
            SchedulerError: If job not found or validation fails.
        """
        if job.id is None:
            raise SchedulerError(message="Job ID is required for update")

        # Validate job
        errors = job.validate()
        if errors:
            raise SchedulerError(
                message=f"Invalid job configuration: {', '.join(errors)}",
                job_id=job.id,
                job_name=job.name,
            )

        # Check for duplicate name (excluding this job)
        existing = self.repository.get_by_name(job.name)
        if existing and existing.id != job.id:
            raise SchedulerError(
                message=f"Job with name '{job.name}' already exists",
                job_id=job.id,
                job_name=job.name,
            )

        # Validate cron expression if provided
        if job.cron_expression:
            try:
                from apscheduler.triggers.cron import CronTrigger

                CronTrigger.from_crontab(job.cron_expression)
            except (ImportError, ValueError) as e:
                raise SchedulerError(
                    message=f"Invalid cron expression: {job.cron_expression}",
                    job_id=job.id,
                    job_name=job.name,
                    original_error=e,
                )

        # Update in database
        job = self.repository.update(job)

        # Update in scheduler if running
        if self._running:
            self._add_job_to_scheduler(job)

        logger.info(f"Updated job '{job.name}' (ID: {job.id})")
        return job

    def delete_job(self, job_id: int) -> bool:
        """Delete a job.

        Args:
            job_id: ID of job to delete.

        Returns:
            True if deleted, False if not found.
        """
        job = self.repository.get_by_id(job_id)
        if job is None:
            return False

        # Remove from scheduler if running
        if self._running and self._scheduler:
            scheduler_job_id = f"sync_job_{job_id}"
            if self._scheduler.get_job(scheduler_job_id):
                self._scheduler.remove_job(scheduler_job_id)

        # Delete from database
        result = self.repository.delete(job_id)
        if result:
            logger.info(f"Deleted job '{job.name}' (ID: {job_id})")

        return result

    def enable_job(self, job_id: int) -> ScheduledJob:
        """Enable a job.

        Args:
            job_id: ID of job to enable.

        Returns:
            Updated job.

        Raises:
            SchedulerError: If job not found.
        """
        job = self.repository.get_by_id(job_id)
        if job is None:
            raise SchedulerError(
                message=f"Job with ID {job_id} not found",
                job_id=job_id,
            )

        job.enabled = True
        return self.update_job(job)

    def disable_job(self, job_id: int) -> ScheduledJob:
        """Disable a job.

        Args:
            job_id: ID of job to disable.

        Returns:
            Updated job.

        Raises:
            SchedulerError: If job not found.
        """
        job = self.repository.get_by_id(job_id)
        if job is None:
            raise SchedulerError(
                message=f"Job with ID {job_id} not found",
                job_id=job_id,
            )

        job.enabled = False
        return self.update_job(job)

    def trigger_job(self, job_id: int) -> None:
        """Manually trigger a job to run immediately.

        Args:
            job_id: ID of job to trigger.

        Raises:
            SchedulerError: If job not found.
        """
        job = self.repository.get_by_id(job_id)
        if job is None:
            raise SchedulerError(
                message=f"Job with ID {job_id} not found",
                job_id=job_id,
            )

        logger.info(f"Manually triggering job '{job.name}'")
        self._execute_job(job_id)

    def get_job(self, job_id: int) -> ScheduledJob | None:
        """Get a job by ID.

        Args:
            job_id: Job ID.

        Returns:
            ScheduledJob if found, None otherwise.
        """
        return self.repository.get_by_id(job_id)

    def get_job_by_name(self, name: str) -> ScheduledJob | None:
        """Get a job by name.

        Args:
            name: Job name.

        Returns:
            ScheduledJob if found, None otherwise.
        """
        return self.repository.get_by_name(name)

    def get_all_jobs(self, include_disabled: bool = False) -> list[ScheduledJob]:
        """Get all jobs.

        Args:
            include_disabled: Whether to include disabled jobs.

        Returns:
            List of scheduled jobs.
        """
        return self.repository.get_all(include_disabled=include_disabled)

    def get_status(self) -> dict[str, Any]:
        """Get scheduler status.

        Returns:
            Dictionary with scheduler status information.
        """
        jobs = self.repository.get_all(include_disabled=True)
        enabled_count = sum(1 for j in jobs if j.enabled)
        disabled_count = len(jobs) - enabled_count

        return {
            "running": self.is_running,
            "timezone": self.config.scheduler_timezone,
            "total_jobs": len(jobs),
            "enabled_jobs": enabled_count,
            "disabled_jobs": disabled_count,
        }


# Singleton instance
_service: SchedulerService | None = None


def get_scheduler_service(
    config: Config | None = None,
) -> SchedulerService:
    """Get the scheduler service singleton.

    Args:
        config: Configuration object. If None, loads from environment.

    Returns:
        SchedulerService instance.
    """
    global _service
    if _service is None:
        _service = SchedulerService(config)
    return _service


def reset_scheduler_service() -> None:
    """Reset the scheduler service singleton.

    Useful for testing. Also stops the scheduler if running.
    """
    global _service
    if _service is not None:
        if _service.is_running:
            _service.stop()
        _service = None
