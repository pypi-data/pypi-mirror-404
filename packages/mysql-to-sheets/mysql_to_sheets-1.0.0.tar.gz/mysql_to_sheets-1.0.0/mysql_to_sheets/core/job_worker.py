"""Job worker for processing queued jobs.

Provides a polling-based worker that claims and processes jobs from
the queue. Supports graceful shutdown, heartbeat for distributed workers,
and configurable polling interval.
"""

import logging
import os
import signal
import socket
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from mysql_to_sheets.models.jobs import Job

if TYPE_CHECKING:
    from mysql_to_sheets.core.job_backend import JobQueueBackend

logger = logging.getLogger(__name__)


def generate_worker_id() -> str:
    """Generate a unique worker ID.

    Combines hostname and a short UUID for uniqueness across machines.

    Returns:
        Worker ID string.
    """
    hostname = socket.gethostname()[:20]
    unique = uuid.uuid4().hex[:8]
    return f"{hostname}-{unique}"


class JobWorker:
    """Worker for processing queued jobs.

    Uses polling to claim and process jobs from the queue.
    Supports graceful shutdown via stop() or SIGTERM/SIGINT.

    For distributed deployments, includes:
    - Unique worker ID for job claiming
    - Background heartbeat thread to signal liveness
    - Graceful job release on shutdown

    Attributes:
        worker_id: Unique identifier for this worker.
    """

    def __init__(
        self,
        db_path: str | None = None,
        poll_interval: float = 1.0,
        stale_check_interval: int = 60,
        worker_id: str | None = None,
        heartbeat_interval: int = 30,
        backend: "JobQueueBackend | None" = None,
    ) -> None:
        """Initialize job worker.

        Args:
            db_path: Path to jobs database (for SQLite backend).
            poll_interval: Seconds between job polls.
            stale_check_interval: Seconds between stale job cleanup checks.
            worker_id: Unique worker identifier. Auto-generated if not provided.
            heartbeat_interval: Seconds between heartbeat updates.
            backend: Optional pre-configured job backend (for testing).
        """
        self._db_path = db_path
        self._poll_interval = poll_interval
        self._stale_check_interval = stale_check_interval
        self._heartbeat_interval = heartbeat_interval
        self._running = False
        self._last_stale_check = 0.0

        # Worker identification
        self._worker_id = worker_id or os.getenv("WORKER_ID") or generate_worker_id()

        # Current job being processed (for graceful shutdown)
        self._current_job: Job | None = None
        self._current_job_lock = threading.Lock()

        # Heartbeat thread
        self._heartbeat_thread: threading.Thread | None = None
        self._heartbeat_stop = threading.Event()

        # Backend (lazy-loaded)
        self._backend = backend

    @property
    def worker_id(self) -> str:
        """Get the worker ID."""
        return self._worker_id

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    @property
    def current_job(self) -> Job | None:
        """Get the current job being processed."""
        with self._current_job_lock:
            return self._current_job

    def _get_backend(self) -> "JobQueueBackend":
        """Get or create the job backend."""
        if self._backend is None:
            from mysql_to_sheets.core.config import get_config
            from mysql_to_sheets.core.job_factory import get_job_backend

            config = get_config()
            self._backend = get_job_backend(
                config=config,
                db_path=self._db_path,
            )
        return self._backend

    def start(self) -> None:
        """Start the worker (blocking).

        Runs until stop() is called or a shutdown signal is received.
        """
        self._running = True
        self._setup_signal_handlers()
        self._start_heartbeat_thread()

        logger.info(
            f"Job worker started (id={self._worker_id}, poll_interval={self._poll_interval}s)"
        )

        try:
            while self._running:
                self._check_stale_jobs()
                job = self._poll_for_job()

                if job:
                    self._process_job(job)
                else:
                    time.sleep(self._poll_interval)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self._graceful_shutdown()

    def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info(f"Stopping job worker {self._worker_id}...")
        self._running = False

    def _graceful_shutdown(self) -> None:
        """Perform graceful shutdown tasks."""
        self._running = False

        # Stop heartbeat thread
        self._heartbeat_stop.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=5.0)

        # Release current job if any
        with self._current_job_lock:
            if self._current_job:
                logger.info(f"Releasing job {self._current_job.id} on shutdown")
                try:
                    backend = self._get_backend()
                    if self._current_job.id is not None:
                        backend.release_job(self._current_job.id)
                except (OSError, RuntimeError) as e:
                    logger.error(f"Failed to release job: {e}")
                self._current_job = None

        logger.info(f"Job worker {self._worker_id} stopped")

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""

        def handle_signal(signum: int, frame: Any) -> None:
            logger.info(f"Received signal {signum}")
            self.stop()

        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

    def _start_heartbeat_thread(self) -> None:
        """Start the background heartbeat thread."""
        self._heartbeat_stop.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"heartbeat-{self._worker_id}",
            daemon=True,
        )
        self._heartbeat_thread.start()
        logger.debug(f"Started heartbeat thread (interval={self._heartbeat_interval}s)")

    def _heartbeat_loop(self) -> None:
        """Background loop to send heartbeats for the current job."""
        while not self._heartbeat_stop.wait(timeout=self._heartbeat_interval):
            with self._current_job_lock:
                if self._current_job and self._current_job.id is not None:
                    try:
                        backend = self._get_backend()
                        backend.heartbeat(self._current_job.id, self._worker_id)
                        logger.debug(f"Sent heartbeat for job {self._current_job.id}")
                    except (OSError, RuntimeError) as e:
                        logger.warning(f"Failed to send heartbeat: {e}")

    def _poll_for_job(self) -> Job | None:
        """Poll for the next available job.

        Returns:
            Job if available, None otherwise.
        """
        try:
            backend = self._get_backend()
            job = backend.get_next_pending(worker_id=self._worker_id)

            if job:
                with self._current_job_lock:
                    self._current_job = job
                logger.debug(f"Claimed job {job.id} (type={job.job_type}, attempt={job.attempts})")

            return job
        except (OSError, RuntimeError) as e:
            logger.error(f"Error polling for job: {e}")
            return None

    def _check_stale_jobs(self) -> None:
        """Periodically clean up stale jobs."""
        now = time.time()
        if now - self._last_stale_check >= self._stale_check_interval:
            try:
                from mysql_to_sheets.core.config import get_config

                config = get_config()
                timeout = config.worker_steal_timeout_seconds

                backend = self._get_backend()
                count = backend.cleanup_stale(timeout_seconds=timeout)
                if count > 0:
                    logger.info(f"Cleaned up {count} stale jobs")
            except (OSError, RuntimeError) as e:
                logger.error(f"Error cleaning up stale jobs: {e}")
            finally:
                self._last_stale_check = now

    def _process_job(self, job: Job) -> None:
        """Process a single job.

        Args:
            job: Job to process.
        """
        logger.info(
            f"Processing job {job.id} (type={job.job_type}, "
            f"attempt={job.attempts}/{job.max_attempts})"
        )

        start_time = datetime.now(timezone.utc)

        try:
            result = self._execute_job(job)
            backend = self._get_backend()
            if job.id is not None:
                backend.complete(job.id, result)

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"Completed job {job.id} in {elapsed:.2f}s")

        except Exception as e:  # Job boundary: catch all to mark job failed
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            error_msg = str(e)

            logger.error(f"Job {job.id} failed after {elapsed:.2f}s: {error_msg}")
            backend = self._get_backend()
            if job.id is not None:
                backend.fail(job.id, error_msg, requeue=True)

        finally:
            with self._current_job_lock:
                self._current_job = None

    def _execute_job(self, job: Job) -> dict[str, Any]:
        """Execute a job based on its type.

        Args:
            job: Job to execute.

        Returns:
            Result dictionary.

        Raises:
            ValueError: If job type is unknown.
            Exception: Any error during job execution.
        """
        if job.job_type == "sync":
            return self._execute_sync_job(job)
        elif job.job_type == "export":
            return self._execute_export_job(job)
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")

    def _execute_sync_job(self, job: Job) -> dict[str, Any]:
        """Execute a sync job.

        Args:
            job: Sync job to execute.

        Returns:
            Sync result dictionary.
        """
        from mysql_to_sheets.core.config import get_config
        from mysql_to_sheets.core.sync import run_sync

        payload = job.payload
        config = get_config()

        # Apply payload overrides to config
        overrides = {}
        if "sheet_id" in payload:
            overrides["google_sheet_id"] = payload["sheet_id"]
        if "worksheet_name" in payload:
            overrides["google_worksheet_name"] = payload["worksheet_name"]
        if "sql_query" in payload:
            overrides["sql_query"] = payload["sql_query"]
        if "sync_mode" in payload:
            overrides["sync_mode"] = payload["sync_mode"]

        if overrides:
            config = config.with_overrides(**overrides)

        # Get config_id for freshness tracking
        config_id = payload.get("config_id")

        # Run sync
        result = run_sync(
            config=config,
            dry_run=payload.get("dry_run", False),
            preview=payload.get("preview", False),
        )

        # Update freshness if we have a config_id
        if config_id and result.success:
            try:
                from mysql_to_sheets.core.freshness import update_freshness

                update_freshness(
                    config_id=config_id,
                    organization_id=job.organization_id,
                    success=True,
                    row_count=result.rows_synced,
                    db_path=config.tenant_db_path,
                )
            except (OSError, RuntimeError, ImportError) as e:
                logger.debug(f"Failed to update freshness: {e}")

        return result.to_dict()

    def _execute_export_job(self, job: Job) -> dict[str, Any]:
        """Execute an export job (audit log export).

        Args:
            job: Export job to execute.

        Returns:
            Export result dictionary.
        """
        payload = job.payload
        export_type = payload.get("export_type", "audit")

        if export_type == "audit":
            import io

            from mysql_to_sheets.core.audit_export import export_audit_logs
            from mysql_to_sheets.core.config import get_config
            from mysql_to_sheets.core.metadata_db import get_metadata_engine

            config = get_config()
            engine = get_metadata_engine(config)
            db_path = str(engine.url)

            output_path = payload.get("output_path")
            if output_path:
                with open(output_path, "w") as f:
                    result = export_audit_logs(
                        organization_id=job.organization_id,
                        output=f,
                        db_path=db_path,
                        format=payload.get("format", "json"),
                    )
            else:
                output = io.StringIO()
                result = export_audit_logs(
                    organization_id=job.organization_id,
                    output=output,
                    db_path=db_path,
                    format=payload.get("format", "json"),
                )
                output_path = None

            return {
                "export_type": export_type,
                "success": True,
                "output_path": output_path,
                "record_count": result.record_count,
            }
        else:
            raise ValueError(f"Unknown export type: {export_type}")


def run_worker(
    db_path: str | None = None,
    poll_interval: float = 1.0,
    stale_check_interval: int = 60,
    worker_id: str | None = None,
    heartbeat_interval: int | None = None,
) -> None:
    """Run a job worker (blocking).

    Convenience function to create and start a worker.

    Args:
        db_path: Path to jobs database.
        poll_interval: Seconds between job polls.
        stale_check_interval: Seconds between stale job cleanup checks.
        worker_id: Optional worker ID. Auto-generated if not provided.
        heartbeat_interval: Seconds between heartbeat updates.
    """
    # Get heartbeat interval from config if not provided
    if heartbeat_interval is None:
        from mysql_to_sheets.core.config import get_config

        config = get_config()
        heartbeat_interval = config.worker_heartbeat_seconds

    worker = JobWorker(
        db_path=db_path,
        poll_interval=poll_interval,
        stale_check_interval=stale_check_interval,
        worker_id=worker_id,
        heartbeat_interval=heartbeat_interval,
    )
    worker.start()
