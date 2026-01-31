"""Agent worker for polling and executing jobs from the control plane.

The AgentWorker:
1. Authenticates to control plane using LINK_TOKEN
2. Long-polls for available jobs
3. Claims jobs atomically
4. Executes sync operations locally
5. Reports results back to control plane
6. Sends periodic heartbeats during execution

Based on JobWorker patterns but adapted for HTTP polling instead
of direct database access.
"""

import json
import logging
import os
import signal
import socket
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mysql_to_sheets import __version__
from mysql_to_sheets.agent.link_config_provider import LinkConfigProvider
from mysql_to_sheets.agent.link_token import (
    LinkTokenInfo,
    LinkTokenStatus,
    add_revoked_token,
    validate_link_token,
)

logger = logging.getLogger(__name__)


def generate_agent_id() -> str:
    """Generate a unique agent ID.

    Combines hostname and a short UUID for uniqueness across machines.

    Returns:
        Agent ID string.
    """
    hostname = socket.gethostname()[:20]
    unique = uuid.uuid4().hex[:8]
    return f"agent-{hostname}-{unique}"


@dataclass
class AgentJob:
    """Job received from control plane."""

    id: int
    organization_id: int
    job_type: str
    payload: dict[str, Any]
    config_id: int | None = None
    priority: int = 0
    max_attempts: int = 3
    created_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentJob":
        """Create AgentJob from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        payload = data.get("payload", {})
        if isinstance(payload, str):
            payload = json.loads(payload)

        return cls(
            id=data["id"],
            organization_id=data["organization_id"],
            job_type=data.get("job_type", "sync"),
            payload=payload,
            config_id=data.get("config_id"),
            priority=data.get("priority", 0),
            max_attempts=data.get("max_attempts", 3),
            created_at=created_at,
        )


@dataclass
class AgentStatus:
    """Current agent status for reporting."""

    agent_id: str
    status: str = "idle"  # idle, running, stopping
    current_job_id: int | None = None
    jobs_completed: int = 0
    jobs_failed: int = 0
    last_poll_at: datetime | None = None
    last_heartbeat_at: datetime | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API reporting."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "current_job_id": self.current_job_id,
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "last_poll_at": self.last_poll_at.isoformat() if self.last_poll_at else None,
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            "started_at": self.started_at.isoformat(),
            "version": __version__,
        }


class AgentWorker:
    """Worker that polls control plane for jobs and executes them locally.

    Uses HTTP long-polling to receive jobs, with exponential backoff
    on errors. Maintains a heartbeat thread during job execution to
    signal liveness.

    Attributes:
        agent_id: Unique identifier for this agent.
        control_plane_url: Base URL of the control plane API.
    """

    def __init__(
        self,
        control_plane_url: str | None = None,
        link_token: str | None = None,
        agent_id: str | None = None,
        poll_interval: float = 5.0,
        poll_timeout: float = 30.0,
        heartbeat_interval: int = 30,
        max_backoff: float = 300.0,
    ) -> None:
        """Initialize agent worker.

        Args:
            control_plane_url: Base URL of the control plane API.
            link_token: RS256 JWT for authentication.
            agent_id: Unique agent identifier. Auto-generated if not provided.
            poll_interval: Seconds between polls when no job available.
            poll_timeout: HTTP timeout for long-poll requests.
            heartbeat_interval: Seconds between heartbeat updates.
            max_backoff: Maximum backoff delay on errors.
        """
        self._control_plane_url = (
            control_plane_url
            or os.getenv("CONTROL_PLANE_URL", "https://app.mysql-to-sheets.com")
        ).rstrip("/")

        self._link_token = link_token or os.getenv("LINK_TOKEN", "")
        self._agent_id = agent_id or os.getenv("AGENT_ID") or generate_agent_id()

        self._poll_interval = poll_interval
        self._poll_timeout = poll_timeout
        self._heartbeat_interval = heartbeat_interval
        self._max_backoff = max_backoff

        # State
        self._running = False
        self._current_backoff = poll_interval
        self._status = AgentStatus(agent_id=self._agent_id)

        # Current job tracking
        self._current_job: AgentJob | None = None
        self._current_job_lock = threading.Lock()

        # Heartbeat thread
        self._heartbeat_thread: threading.Thread | None = None
        self._heartbeat_stop = threading.Event()

        # Token info (validated on start)
        self._token_info: LinkTokenInfo | None = None

    @property
    def agent_id(self) -> str:
        """Get the agent ID."""
        return self._agent_id

    @property
    def control_plane_url(self) -> str:
        """Get the control plane URL."""
        return self._control_plane_url

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    @property
    def status(self) -> AgentStatus:
        """Get current agent status."""
        return self._status

    def start(self) -> None:
        """Start the agent worker (blocking).

        Runs until stop() is called or a shutdown signal is received.
        """
        # Validate token first
        if not self._validate_token():
            return

        # Install crash handler for automatic crash reporting
        self._setup_crash_handler()

        # Register with control plane
        if not self._register():
            logger.error("Failed to register with control plane")
            return

        self._running = True
        self._status.status = "idle"
        self._setup_signal_handlers()
        self._start_heartbeat_thread()

        logger.info(
            f"Agent worker started (id={self._agent_id}, "
            f"control_plane={self._control_plane_url})"
        )

        try:
            while self._running:
                job = self._poll_for_job()

                if job:
                    self._current_backoff = self._poll_interval  # Reset backoff
                    self._process_job(job)
                else:
                    # Exponential backoff on empty poll
                    time.sleep(self._current_backoff)
                    self._current_backoff = min(
                        self._current_backoff * 1.5,
                        self._max_backoff,
                    )

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self._graceful_shutdown()

    def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info(f"Stopping agent worker {self._agent_id}...")
        self._running = False

    def _validate_token(self) -> bool:
        """Validate the link token.

        Returns:
            True if token is valid.
        """
        if not self._link_token:
            logger.error("LINK_TOKEN is required")
            return False

        self._token_info = validate_link_token(self._link_token)

        if self._token_info.status != LinkTokenStatus.VALID:
            logger.error(f"Invalid LINK_TOKEN: {self._token_info.error}")
            return False

        logger.info(
            f"Token validated: org={self._token_info.organization_id}, "
            f"permissions={self._token_info.permissions}"
        )
        return True

    def _setup_crash_handler(self) -> None:
        """Set up crash handler for automatic crash reporting.

        Installs as sys.excepthook to catch unhandled exceptions.
        """
        try:
            from mysql_to_sheets.agent.crash_handler import setup_crash_handler

            setup_crash_handler(
                agent_id=self._agent_id,
                control_plane_url=self._control_plane_url,
                link_token=self._link_token,
                version=__version__,
            )
            logger.debug("Crash handler installed")
        except ImportError as e:
            logger.warning(f"Crash handler not available: {e}")

    def _register(self) -> bool:
        """Register agent with control plane.

        Returns:
            True if registration successful.
        """
        url = f"{self._control_plane_url}/api/agent/register"

        payload = {
            "agent_id": self._agent_id,
            "version": __version__,
            "hostname": socket.gethostname(),
            "capabilities": ["sync"],
        }

        try:
            response = self._api_request("POST", url, payload)
            logger.info(f"Registered with control plane: {response.get('message', 'OK')}")
            return True
        except (HTTPError, URLError) as e:
            logger.error(f"Registration failed: {e}")
            return False

    def _graceful_shutdown(self) -> None:
        """Perform graceful shutdown tasks."""
        self._running = False
        self._status.status = "stopping"

        # Stop heartbeat thread
        self._heartbeat_stop.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=5.0)

        # Release current job if any
        with self._current_job_lock:
            if self._current_job:
                logger.info(f"Releasing job {self._current_job.id} on shutdown")
                try:
                    self._report_job_released(self._current_job.id)
                except (HTTPError, URLError) as e:
                    logger.error(f"Failed to release job: {e}")
                self._current_job = None

        # Notify control plane of shutdown
        try:
            self._api_request(
                "POST",
                f"{self._control_plane_url}/api/agent/deregister",
                {"agent_id": self._agent_id},
            )
        except (HTTPError, URLError):
            pass  # Best effort

        logger.info(f"Agent worker {self._agent_id} stopped")

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
            name=f"heartbeat-{self._agent_id}",
            daemon=True,
        )
        self._heartbeat_thread.start()
        logger.debug(f"Started heartbeat thread (interval={self._heartbeat_interval}s)")

    def _heartbeat_loop(self) -> None:
        """Background loop to send heartbeats."""
        while not self._heartbeat_stop.wait(timeout=self._heartbeat_interval):
            with self._current_job_lock:
                job_id = self._current_job.id if self._current_job else None

            try:
                self._send_heartbeat(job_id)
                self._status.last_heartbeat_at = datetime.now(timezone.utc)
            except (HTTPError, URLError) as e:
                logger.warning(f"Failed to send heartbeat: {e}")
                # Check for token revocation
                if isinstance(e, HTTPError) and e.code == 401:
                    logger.error("Token rejected, stopping agent")
                    self.stop()

    def _send_heartbeat(self, job_id: int | None) -> None:
        """Send heartbeat to control plane.

        Args:
            job_id: Current job ID if processing.
        """
        url = f"{self._control_plane_url}/api/agent/heartbeat"
        payload = {
            "agent_id": self._agent_id,
            "job_id": job_id,
            "status": self._status.to_dict(),
        }
        self._api_request("POST", url, payload)
        logger.debug(f"Sent heartbeat (job_id={job_id})")

    def _poll_for_job(self) -> AgentJob | None:
        """Poll control plane for next available job.

        Uses long-polling with the configured timeout.

        Returns:
            AgentJob if available, None otherwise.
        """
        url = f"{self._control_plane_url}/api/agent/poll?agent_id={self._agent_id}"

        try:
            response = self._api_request(
                "GET",
                url,
                timeout=self._poll_timeout,
            )

            self._status.last_poll_at = datetime.now(timezone.utc)

            if not response or response.get("job") is None:
                return None

            job_data = response["job"]
            job = AgentJob.from_dict(job_data)

            # Claim the job
            if not self._claim_job(job.id):
                logger.warning(f"Failed to claim job {job.id}")
                return None

            with self._current_job_lock:
                self._current_job = job
                self._status.current_job_id = job.id
                self._status.status = "running"

            logger.info(f"Claimed job {job.id} (type={job.job_type})")
            return job

        except HTTPError as e:
            if e.code == 401:
                # Token may be revoked
                logger.error("Authentication failed during poll")
                if self._token_info and self._token_info.jti:
                    add_revoked_token(self._token_info.jti)
                self.stop()
            elif e.code != 204:  # 204 = no jobs available
                logger.error(f"Poll error: HTTP {e.code}")
            return None
        except URLError as e:
            logger.error(f"Poll error: {e.reason}")
            return None

    def _claim_job(self, job_id: int) -> bool:
        """Atomically claim a job.

        Args:
            job_id: ID of job to claim.

        Returns:
            True if claim successful.
        """
        url = f"{self._control_plane_url}/api/agent/jobs/{job_id}/claim"
        payload = {"agent_id": self._agent_id}

        try:
            self._api_request("POST", url, payload)
            return True
        except HTTPError as e:
            if e.code == 409:  # Conflict - already claimed
                logger.debug(f"Job {job_id} already claimed by another agent")
            else:
                logger.error(f"Claim failed: HTTP {e.code}")
            return False
        except URLError as e:
            logger.error(f"Claim failed: {e.reason}")
            return False

    def _process_job(self, job: AgentJob) -> None:
        """Process a single job.

        Args:
            job: Job to process.
        """
        logger.info(f"Processing job {job.id} (type={job.job_type})")
        start_time = datetime.now(timezone.utc)

        try:
            result = self._execute_job(job)
            self._report_job_result(job.id, success=True, result=result)

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"Completed job {job.id} in {elapsed:.2f}s")
            self._status.jobs_completed += 1

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            error_msg = str(e)

            logger.error(f"Job {job.id} failed after {elapsed:.2f}s: {error_msg}")
            self._report_job_result(job.id, success=False, error=error_msg)
            self._status.jobs_failed += 1

            # Report crash via crash handler
            self._report_crash(e, job_id=job.id, context={"config_id": job.config_id})

        finally:
            with self._current_job_lock:
                self._current_job = None
                self._status.current_job_id = None
                self._status.status = "idle"

    def _execute_job(self, job: AgentJob) -> dict[str, Any]:
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
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")

    def _execute_sync_job(self, job: AgentJob) -> dict[str, Any]:
        """Execute a sync job.

        Args:
            job: Sync job to execute.

        Returns:
            Sync result dictionary.
        """
        from mysql_to_sheets.core.sync import run_sync

        # Get config from control plane + local credentials
        provider = LinkConfigProvider(
            control_plane_url=self._control_plane_url,
            link_token=self._link_token,
            config_id=job.config_id,
        )
        config = provider.get_config()

        # Apply payload overrides
        payload = job.payload
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

        # Run sync
        result = run_sync(
            config=config,
            dry_run=payload.get("dry_run", False),
            preview=payload.get("preview", False),
        )

        return result.to_dict()

    def _report_job_result(
        self,
        job_id: int,
        success: bool,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Report job result to control plane.

        Args:
            job_id: Job ID.
            success: Whether job succeeded.
            result: Result data if successful.
            error: Error message if failed.
        """
        url = f"{self._control_plane_url}/api/agent/jobs/{job_id}/result"
        payload = {
            "agent_id": self._agent_id,
            "success": success,
            "result": result,
            "error": error,
        }

        try:
            self._api_request("POST", url, payload)
        except (HTTPError, URLError) as e:
            logger.error(f"Failed to report result for job {job_id}: {e}")

    def _report_job_released(self, job_id: int) -> None:
        """Report that a job was released (not completed).

        Args:
            job_id: Job ID.
        """
        url = f"{self._control_plane_url}/api/agent/jobs/{job_id}/release"
        payload = {"agent_id": self._agent_id}

        self._api_request("POST", url, payload)

    def _report_crash(
        self,
        exc: Exception,
        job_id: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Report an exception via the crash handler.

        Args:
            exc: Exception to report.
            job_id: Job ID if processing a job.
            context: Additional context.
        """
        try:
            from mysql_to_sheets.agent.crash_handler import get_crash_reporter

            reporter = get_crash_reporter()
            if reporter:
                reporter.report_exception(exc, job_id=job_id, context=context)
        except Exception as e:
            logger.debug(f"Failed to report crash: {e}")

    def _api_request(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST).
            url: Request URL.
            payload: JSON payload for POST requests.
            timeout: Request timeout in seconds.

        Returns:
            Response JSON as dictionary.

        Raises:
            HTTPError: On HTTP error response.
            URLError: On connection error.
        """
        headers = {
            "Authorization": f"Bearer {self._link_token}",
            "Accept": "application/json",
            "User-Agent": f"mysql-to-sheets-agent/{__version__}",
        }

        data = None
        if payload and method == "POST":
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")

        request = Request(url, data=data, headers=headers, method=method)
        response = urlopen(request, timeout=timeout or 30)

        response_data = response.read().decode("utf-8")
        if response_data:
            return json.loads(response_data)
        return {}


def run_agent(
    control_plane_url: str | None = None,
    link_token: str | None = None,
    agent_id: str | None = None,
    poll_interval: float = 5.0,
    heartbeat_interval: int = 30,
) -> None:
    """Run an agent worker (blocking).

    Convenience function to create and start a worker.

    Args:
        control_plane_url: Base URL of the control plane API.
        link_token: RS256 JWT for authentication.
        agent_id: Optional agent ID. Auto-generated if not provided.
        poll_interval: Seconds between job polls.
        heartbeat_interval: Seconds between heartbeat updates.
    """
    worker = AgentWorker(
        control_plane_url=control_plane_url,
        link_token=link_token,
        agent_id=agent_id,
        poll_interval=poll_interval,
        heartbeat_interval=heartbeat_interval,
    )
    worker.start()
