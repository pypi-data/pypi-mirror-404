"""Agent API routes for Hybrid Agent communication.

These endpoints allow Hybrid Agents to:
- Register with the control plane
- Poll for available jobs
- Claim jobs for execution
- Report job results
- Send heartbeats during execution
- Fetch sync configurations (without credentials)

All endpoints require LINK_TOKEN authentication via Bearer token.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from mysql_to_sheets import __version__

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])


# Pydantic schemas for request/response validation


class AgentRegisterRequest(BaseModel):
    """Request to register an agent."""

    agent_id: str = Field(..., min_length=1, max_length=100)
    version: str = Field(default="unknown")
    hostname: str = Field(default="unknown")
    capabilities: list[str] = Field(default_factory=list)


class AgentRegisterResponse(BaseModel):
    """Response after agent registration."""

    message: str
    agent_id: str
    organization_id: int


class AgentHeartbeatRequest(BaseModel):
    """Request to send heartbeat."""

    agent_id: str = Field(..., min_length=1, max_length=100)
    job_id: int | None = None
    status: dict[str, Any] = Field(default_factory=dict)


class AgentHeartbeatResponse(BaseModel):
    """Response to heartbeat."""

    message: str
    server_time: str


class JobClaimRequest(BaseModel):
    """Request to claim a job."""

    agent_id: str = Field(..., min_length=1, max_length=100)


class JobClaimResponse(BaseModel):
    """Response after claiming a job."""

    message: str
    job_id: int


class JobResultRequest(BaseModel):
    """Request to report job result."""

    agent_id: str = Field(..., min_length=1, max_length=100)
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None


class JobResultResponse(BaseModel):
    """Response after reporting job result."""

    message: str
    job_id: int
    status: str


class JobReleaseRequest(BaseModel):
    """Request to release a job without completing it."""

    agent_id: str = Field(..., min_length=1, max_length=100)


class PollResponse(BaseModel):
    """Response from job polling."""

    job: dict[str, Any] | None = None
    message: str = "No jobs available"


class ConfigResponse(BaseModel):
    """Sync configuration (without credentials)."""

    id: int
    name: str
    sql_query: str
    google_sheet_id: str
    google_worksheet_name: str | None = None
    sync_mode: str = "replace"
    chunk_size: int = 1000
    column_map: dict[str, str] | None = None
    columns: list[str] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AgentHealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    server_time: str


class AgentVersionResponse(BaseModel):
    """Version check response."""

    latest_version: str
    current_version: str
    update_available: bool
    release_url: str | None = None


class CrashReportRequest(BaseModel):
    """Request to submit a crash report."""

    agent_id: str = Field(..., min_length=1, max_length=100)
    exception_type: str = Field(..., min_length=1, max_length=255)
    exception_message: str = Field(..., min_length=1)
    traceback: str | None = None
    job_id: int | None = None
    version: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class CrashReportResponse(BaseModel):
    """Response after submitting a crash report."""

    message: str
    report_id: int


# Authentication dependency


async def verify_link_token(request: Request) -> dict[str, Any]:
    """Verify LINK_TOKEN from Authorization header.

    Args:
        request: FastAPI request object.

    Returns:
        Decoded token information.

    Raises:
        HTTPException: If token is missing or invalid.
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    link_token = auth_header[7:]  # Remove "Bearer " prefix

    # Import here to avoid circular dependency
    from mysql_to_sheets.agent.link_token import LinkTokenStatus, validate_link_token

    token_info = validate_link_token(link_token)

    if token_info.status == LinkTokenStatus.REVOKED:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    if token_info.status != LinkTokenStatus.VALID:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {token_info.error}",
        )

    return token_info.to_dict()


# Helper functions


def get_organization_id_from_token(token_info: dict[str, Any]) -> int:
    """Extract organization ID from token info.

    Args:
        token_info: Decoded token information.

    Returns:
        Organization ID as integer.

    Raises:
        HTTPException: If organization ID is invalid.
    """
    org_str = token_info.get("organization_id", "")
    try:
        if org_str.startswith("org_"):
            return int(org_str[4:])
        return int(org_str)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid organization ID in token")


def hash_link_token(token: str) -> str:
    """Hash a link token for storage/comparison.

    Args:
        token: Raw link token string.

    Returns:
        SHA256 hash of the token.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _emit_agent_webhook(
    event: str,
    agent_id: str,
    organization_id: int,
    hostname: str | None = None,
    version: str | None = None,
    previous_status: str | None = None,
    new_status: str | None = None,
    offline_reason: str | None = None,
    db_path: str | None = None,
) -> None:
    """Emit agent state change webhook.

    Args:
        event: Event type (agent.online, agent.offline).
        agent_id: Agent identifier.
        organization_id: Organization ID.
        hostname: Agent hostname.
        version: Agent version.
        previous_status: Status before change.
        new_status: Status after change.
        offline_reason: Reason for going offline.
        db_path: Path to tenant database.
    """
    try:
        from mysql_to_sheets.core.webhooks.delivery import deliver_webhook
        from mysql_to_sheets.core.webhooks.payload import create_agent_payload
        from mysql_to_sheets.models.webhooks import get_webhook_repository

        if not db_path:
            return

        webhook_repo = get_webhook_repository(db_path)
        org_webhooks = webhook_repo.get_all(
            organization_id=organization_id,
            enabled=True,
        )

        for webhook in org_webhooks:
            events = webhook.events or []
            if event in events or "agent.*" in events:
                payload = create_agent_payload(
                    event=event,
                    agent_id=agent_id,
                    organization_id=organization_id,
                    hostname=hostname,
                    version=version,
                    previous_status=previous_status,
                    new_status=new_status,
                    offline_reason=offline_reason,
                )
                try:
                    deliver_webhook(
                        webhook=webhook,
                        payload=payload,
                        db_path=db_path,
                    )
                except Exception as e:
                    logger.warning(f"Failed to deliver {event} webhook for {agent_id}: {e}")

    except (ImportError, OSError) as e:
        logger.debug(f"Webhook delivery skipped: {e}")


# Routes


@router.post("/register", response_model=AgentRegisterResponse)
async def register_agent(
    body: AgentRegisterRequest,
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> AgentRegisterResponse:
    """Register a new agent with the control plane.

    Creates or updates the agent record. Agents must register
    before polling for jobs. Emits agent.online webhook.
    """
    org_id = get_organization_id_from_token(token_info)

    # Get or create agent record
    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.agents import get_agent_repository

    config = get_config()
    repo = get_agent_repository(config.tenant_db_path)

    # Check if agent existed before to determine if this is a new registration
    existing = repo.get_by_agent_id(body.agent_id, organization_id=org_id)
    was_offline = existing is None or existing.status == "offline"

    agent = repo.upsert(
        agent_id=body.agent_id,
        organization_id=org_id,
        version=body.version,
        hostname=body.hostname,
        capabilities=body.capabilities,
    )

    logger.info(
        f"Agent registered: {body.agent_id} (org={org_id}, version={body.version})"
    )

    # Emit agent.online webhook if agent was offline or new
    if was_offline:
        _emit_agent_webhook(
            event="agent.online",
            agent_id=body.agent_id,
            organization_id=org_id,
            hostname=body.hostname,
            version=body.version,
            previous_status="offline" if existing else None,
            new_status="online",
            db_path=config.tenant_db_path,
        )

    return AgentRegisterResponse(
        message="Agent registered successfully",
        agent_id=agent.agent_id,
        organization_id=org_id,
    )


@router.post("/deregister")
async def deregister_agent(
    body: AgentRegisterRequest,
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> dict[str, str]:
    """Deregister an agent (graceful shutdown). Emits agent.offline webhook."""
    org_id = get_organization_id_from_token(token_info)

    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.agents import get_agent_repository

    config = get_config()
    repo = get_agent_repository(config.tenant_db_path)

    # Get current state before updating
    existing = repo.get_by_agent_id(body.agent_id, organization_id=org_id)
    previous_status = existing.status if existing else "unknown"

    repo.update_status(body.agent_id, org_id, status="offline")

    logger.info(f"Agent deregistered: {body.agent_id} (org={org_id})")

    # Emit agent.offline webhook
    _emit_agent_webhook(
        event="agent.offline",
        agent_id=body.agent_id,
        organization_id=org_id,
        hostname=existing.hostname if existing else None,
        version=existing.version if existing else None,
        previous_status=previous_status,
        new_status="offline",
        offline_reason="graceful_shutdown",
        db_path=config.tenant_db_path,
    )

    return {"message": "Agent deregistered"}


@router.get("/poll", response_model=PollResponse)
async def poll_for_job(
    agent_id: str = Query(..., min_length=1, max_length=100),
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> PollResponse:
    """Long-poll for the next available job.

    Returns a job if one is available, otherwise returns 204 No Content
    after a timeout period. The agent should retry polling after
    receiving a response.
    """
    org_id = get_organization_id_from_token(token_info)

    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.agents import get_agent_repository
    from mysql_to_sheets.models.jobs import get_job_repository

    config = get_config()

    # Update agent last_seen
    agent_repo = get_agent_repository(config.tenant_db_path)
    agent_repo.update_last_seen(agent_id, org_id)

    # Check for pending jobs
    job_repo = get_job_repository(config.tenant_db_path)
    jobs = job_repo.get_all(
        organization_id=org_id,
        status="pending",
        limit=1,
    )

    if not jobs:
        return PollResponse(job=None, message="No jobs available")

    job = jobs[0]

    return PollResponse(
        job=job.to_dict(),
        message="Job available",
    )


@router.post("/jobs/{job_id}/claim", response_model=JobClaimResponse)
async def claim_job(
    job_id: int,
    body: JobClaimRequest,
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> JobClaimResponse:
    """Atomically claim a job for execution.

    Returns 409 Conflict if the job is already claimed.
    """
    org_id = get_organization_id_from_token(token_info)

    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.jobs import get_job_repository

    config = get_config()
    repo = get_job_repository(config.tenant_db_path)

    # Verify job belongs to organization
    job = repo.get_by_id(job_id, organization_id=org_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Job cannot be claimed (status: {job.status})",
        )

    # Claim the job
    claimed_job = repo.claim_job(job_id)
    if not claimed_job:
        raise HTTPException(status_code=409, detail="Job already claimed")

    # Update with worker ID
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from mysql_to_sheets.models.jobs import JobModel

    engine = create_engine(f"sqlite:///{config.tenant_db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        model = session.query(JobModel).filter(JobModel.id == job_id).first()
        if model:
            model.worker_id = body.agent_id
            session.commit()
    finally:
        session.close()

    logger.info(f"Job {job_id} claimed by agent {body.agent_id}")

    return JobClaimResponse(
        message="Job claimed successfully",
        job_id=job_id,
    )


@router.post("/heartbeat", response_model=AgentHeartbeatResponse)
async def send_heartbeat(
    body: AgentHeartbeatRequest,
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> AgentHeartbeatResponse:
    """Send agent heartbeat to signal liveness.

    Should be sent periodically during job execution.
    """
    org_id = get_organization_id_from_token(token_info)

    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.agents import get_agent_repository

    config = get_config()
    repo = get_agent_repository(config.tenant_db_path)

    # Update agent heartbeat
    repo.update_heartbeat(
        agent_id=body.agent_id,
        organization_id=org_id,
        current_job_id=body.job_id,
        status=body.status,
    )

    # Update job heartbeat if processing
    if body.job_id:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from mysql_to_sheets.models.jobs import JobModel

        engine = create_engine(f"sqlite:///{config.tenant_db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            model = session.query(JobModel).filter(JobModel.id == body.job_id).first()
            if model:
                model.heartbeat_at = datetime.now(timezone.utc)
                session.commit()
        finally:
            session.close()

    return AgentHeartbeatResponse(
        message="Heartbeat received",
        server_time=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/jobs/{job_id}/result", response_model=JobResultResponse)
async def report_job_result(
    job_id: int,
    body: JobResultRequest,
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> JobResultResponse:
    """Report the result of a completed job."""
    org_id = get_organization_id_from_token(token_info)

    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.jobs import get_job_repository

    config = get_config()
    repo = get_job_repository(config.tenant_db_path)

    # Verify job belongs to organization
    job = repo.get_by_id(job_id, organization_id=org_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not running (status: {job.status})",
        )

    # Update job status
    if body.success:
        repo.complete(job_id, body.result or {})
        status = "completed"
        logger.info(f"Job {job_id} completed by agent {body.agent_id}")
    else:
        repo.fail(job_id, body.error or "Unknown error", requeue=False)
        status = "failed"
        logger.warning(f"Job {job_id} failed: {body.error}")

    return JobResultResponse(
        message="Result recorded",
        job_id=job_id,
        status=status,
    )


@router.post("/jobs/{job_id}/release")
async def release_job(
    job_id: int,
    body: JobReleaseRequest,
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> dict[str, str]:
    """Release a job without completing it (e.g., on agent shutdown)."""
    org_id = get_organization_id_from_token(token_info)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.jobs import JobModel

    config = get_config()
    engine = create_engine(f"sqlite:///{config.tenant_db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        model = (
            session.query(JobModel)
            .filter(
                JobModel.id == job_id,
                JobModel.organization_id == org_id,
                JobModel.status == "running",
            )
            .first()
        )

        if not model:
            raise HTTPException(status_code=404, detail="Job not found or not running")

        # Reset to pending for another agent to claim
        model.status = "pending"
        model.started_at = None
        model.worker_id = None
        model.heartbeat_at = None
        session.commit()

        logger.info(f"Job {job_id} released by agent {body.agent_id}")

        return {"message": "Job released"}

    finally:
        session.close()


@router.get("/configs", response_model=list[ConfigResponse])
async def list_configs(
    name: str | None = Query(None),
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> list[ConfigResponse]:
    """List sync configurations for the organization.

    Configurations returned do NOT include database credentials.
    The agent should use local credentials from its environment.
    """
    org_id = get_organization_id_from_token(token_info)

    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.sync_configs import get_sync_config_repository

    config = get_config()
    repo = get_sync_config_repository(config.tenant_db_path)

    if name:
        # Get specific config by name
        sync_config = repo.get_by_name(name, org_id)
        if not sync_config:
            raise HTTPException(status_code=404, detail=f"Config '{name}' not found")
        configs = [sync_config]
    else:
        # Get all configs for organization
        configs = repo.get_all(organization_id=org_id)

    return [
        ConfigResponse(
            id=c.id,  # type: ignore
            name=c.name,
            sql_query=c.sql_query,
            google_sheet_id=c.google_sheet_id,
            google_worksheet_name=c.google_worksheet_name,
            sync_mode=c.sync_mode or "replace",
            chunk_size=c.chunk_size or 1000,
            column_map=json.loads(c.column_map) if c.column_map else None,
            columns=c.columns.split(",") if c.columns else None,
            created_at=c.created_at.isoformat() if c.created_at else None,
            updated_at=c.updated_at.isoformat() if c.updated_at else None,
        )
        for c in configs
    ]


@router.get("/configs/{config_id}", response_model=ConfigResponse)
async def get_config_by_id(
    config_id: int,
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> ConfigResponse:
    """Get a specific sync configuration by ID."""
    org_id = get_organization_id_from_token(token_info)

    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.sync_configs import get_sync_config_repository

    config = get_config()
    repo = get_sync_config_repository(config.tenant_db_path)

    sync_config = repo.get_by_id(config_id, organization_id=org_id)
    if not sync_config:
        raise HTTPException(status_code=404, detail="Config not found")

    return ConfigResponse(
        id=sync_config.id,  # type: ignore
        name=sync_config.name,
        sql_query=sync_config.sql_query,
        google_sheet_id=sync_config.google_sheet_id,
        google_worksheet_name=sync_config.google_worksheet_name,
        sync_mode=sync_config.sync_mode or "replace",
        chunk_size=sync_config.chunk_size or 1000,
        column_map=json.loads(sync_config.column_map) if sync_config.column_map else None,
        columns=sync_config.columns.split(",") if sync_config.columns else None,
        created_at=sync_config.created_at.isoformat() if sync_config.created_at else None,
        updated_at=sync_config.updated_at.isoformat() if sync_config.updated_at else None,
    )


@router.get("/health", response_model=AgentHealthResponse)
async def agent_health_check(
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> AgentHealthResponse:
    """Health check endpoint for agents."""
    return AgentHealthResponse(
        status="healthy",
        version=__version__,
        server_time=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/version", response_model=AgentVersionResponse)
async def check_agent_version(
    current_version: str = Query(default=__version__),
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> AgentVersionResponse:
    """Check for agent version updates.

    Compares the provided version against the latest release.
    """
    from mysql_to_sheets.agent.updater import (
        get_agent_update_checker,
        is_newer_version,
    )

    checker = get_agent_update_checker()
    update_info = checker.check_for_updates()

    update_available = False
    release_url = None

    if update_info:
        update_available = is_newer_version(update_info.version, current_version)
        release_url = update_info.release_url

    return AgentVersionResponse(
        latest_version=update_info.version if update_info else current_version,
        current_version=current_version,
        update_available=update_available,
        release_url=release_url,
    )


@router.post("/crash-report", response_model=CrashReportResponse)
async def submit_crash_report(
    body: CrashReportRequest,
    token_info: dict[str, Any] = Depends(verify_link_token),
) -> CrashReportResponse:
    """Submit a crash report from an agent.

    Crash reports are stored for debugging purposes. Tracebacks are
    expected to be pre-sanitized by the agent to remove sensitive data.
    """
    org_id = get_organization_id_from_token(token_info)

    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.crash_reports import (
        CrashReport,
        get_crash_report_repository,
    )

    config = get_config()
    repo = get_crash_report_repository(config.tenant_db_path)

    # Truncate traceback if too large (additional server-side protection)
    max_size = config.crash_report_max_size_kb * 1024
    traceback_text = body.traceback
    if traceback_text and len(traceback_text.encode("utf-8")) > max_size:
        traceback_text = traceback_text.encode("utf-8")[:max_size].decode(
            "utf-8", errors="ignore"
        )
        traceback_text += "\n\n... [SERVER TRUNCATED - exceeded max size]"

    report = CrashReport(
        agent_id=body.agent_id,
        organization_id=org_id,
        exception_type=body.exception_type,
        exception_message=body.exception_message,
        traceback=traceback_text,
        job_id=body.job_id,
        version=body.version,
        context=body.context,
    )

    created = repo.create(report)

    logger.warning(
        f"Crash report received from agent {body.agent_id}: "
        f"{body.exception_type}: {body.exception_message[:100]}..."
    )

    return CrashReportResponse(
        message="Crash report submitted",
        report_id=created.id,  # type: ignore
    )
