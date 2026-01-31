"""Agents Blueprint for fleet health dashboard.

Provides:
- /agents - Fleet overview page showing all agents
- /agents/<agent_id> - Individual agent detail with job history
- /api/agents/list - JSON list of agents
- /api/agents/stats - Fleet health statistics
- /api/agents/<agent_id>/jobs - Job history for specific agent
"""

import logging
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, render_template, request, session

from mysql_to_sheets.web.decorators import login_required
from mysql_to_sheets.web.utils.pagination import get_bounded_pagination

logger = logging.getLogger(__name__)

# Page blueprint
agents_bp = Blueprint("agents", __name__)

# API blueprint (for AJAX)
agents_api_bp = Blueprint("agents_api", __name__, url_prefix="/api/agents")


# ============================================================================
# Page Routes
# ============================================================================


@agents_bp.route("/agents")
@login_required
def agents_list() -> Any:
    """Fleet overview page showing all agents."""
    from mysql_to_sheets.core.tenant import get_tenant_db_path
    from mysql_to_sheets.models.agents import get_agent_repository

    org_id = session.get("organization_id")
    if not org_id:
        return render_template(
            "error.html",
            error="No organization",
            message="You must be logged in to view agents.",
        )

    db_path = get_tenant_db_path()
    repo = get_agent_repository(db_path)

    # Get all agents including inactive for full history
    agents = repo.get_all(organization_id=org_id, include_inactive=False)
    stats = repo.get_fleet_stats(org_id)

    return render_template(
        "agents.html",
        agents=agents,
        stats=stats,
    )


@agents_bp.route("/agents/<agent_id>")
@login_required
def agent_detail(agent_id: str) -> Any:
    """Individual agent detail page with job history."""
    from mysql_to_sheets.core.tenant import get_tenant_db_path
    from mysql_to_sheets.models.agents import get_agent_repository

    org_id = session.get("organization_id")
    if not org_id:
        return render_template(
            "error.html",
            error="No organization",
            message="You must be logged in to view agent details.",
        )

    db_path = get_tenant_db_path()
    repo = get_agent_repository(db_path)

    agent = repo.get_by_agent_id(agent_id, organization_id=org_id)
    if not agent:
        return render_template(
            "error.html",
            error="Agent not found",
            message=f"No agent found with ID: {agent_id}",
        ), 404

    # Get job history for this agent
    job_history = _get_agent_job_history(agent_id, org_id, db_path, limit=50)

    # Get crash reports for this agent
    crash_reports = _get_agent_crash_reports(agent_id, org_id, db_path, limit=10)

    return render_template(
        "agent_detail.html",
        agent=agent,
        job_history=job_history,
        crash_reports=crash_reports,
    )


# ============================================================================
# API Routes
# ============================================================================


@agents_api_bp.route("/list")
@login_required
def api_list_agents() -> Any:
    """JSON list of agents for the organization."""
    from mysql_to_sheets.core.tenant import get_tenant_db_path
    from mysql_to_sheets.models.agents import get_agent_repository

    org_id = session.get("organization_id")
    if not org_id:
        return jsonify({"success": False, "error": "No organization"}), 400

    db_path = get_tenant_db_path()
    repo = get_agent_repository(db_path)

    status_filter = request.args.get("status")
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"

    agents = repo.get_all(
        organization_id=org_id,
        include_inactive=include_inactive,
        status=status_filter,
    )

    return jsonify({
        "success": True,
        "agents": [a.to_dict() for a in agents],
        "count": len(agents),
    })


@agents_api_bp.route("/stats")
@login_required
def api_fleet_stats() -> Any:
    """Fleet health statistics."""
    from mysql_to_sheets.core.tenant import get_tenant_db_path
    from mysql_to_sheets.models.agents import get_agent_repository

    org_id = session.get("organization_id")
    if not org_id:
        return jsonify({"success": False, "error": "No organization"}), 400

    db_path = get_tenant_db_path()
    repo = get_agent_repository(db_path)

    stats = repo.get_fleet_stats(org_id)

    return jsonify({
        "success": True,
        "stats": stats,
    })


@agents_api_bp.route("/<agent_id>/jobs")
@login_required
def api_agent_jobs(agent_id: str) -> Any:
    """Job history for a specific agent."""
    from mysql_to_sheets.core.tenant import get_tenant_db_path

    org_id = session.get("organization_id")
    if not org_id:
        return jsonify({"success": False, "error": "No organization"}), 400

    db_path = get_tenant_db_path()
    # EC-57: Use bounded pagination to prevent OOM
    _, limit, offset = get_bounded_pagination(request, default_per_page=50, max_per_page=100)

    jobs = _get_agent_job_history(agent_id, org_id, db_path, limit=limit, offset=offset)

    return jsonify({
        "success": True,
        "jobs": jobs,
        "count": len(jobs),
    })


@agents_api_bp.route("/<agent_id>/crash-reports")
@login_required
def api_agent_crash_reports(agent_id: str) -> Any:
    """Crash reports for a specific agent."""
    from mysql_to_sheets.core.tenant import get_tenant_db_path

    org_id = session.get("organization_id")
    if not org_id:
        return jsonify({"success": False, "error": "No organization"}), 400

    db_path = get_tenant_db_path()
    # EC-57: Use bounded pagination to prevent OOM
    _, limit, _ = get_bounded_pagination(request, default_per_page=20, max_per_page=100)

    reports = _get_agent_crash_reports(agent_id, org_id, db_path, limit=limit)

    return jsonify({
        "success": True,
        "crash_reports": reports,
        "count": len(reports),
    })


# ============================================================================
# Helper Functions
# ============================================================================


def _get_agent_job_history(
    agent_id: str,
    organization_id: int,
    db_path: str,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Get job history for an agent.

    Args:
        agent_id: Agent identifier.
        organization_id: Organization ID.
        db_path: Path to tenant database.
        limit: Maximum number of jobs to return.
        offset: Number of jobs to skip.

    Returns:
        List of job dictionaries.
    """
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from mysql_to_sheets.models.jobs import JobModel

        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            jobs = (
                session.query(JobModel)
                .filter(
                    JobModel.organization_id == organization_id,
                    JobModel.worker_id == agent_id,
                )
                .order_by(JobModel.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": job.id,
                    "job_type": job.job_type,
                    "status": job.status,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error": job.error,
                }
                for job in jobs
            ]
        finally:
            session.close()

    except Exception as e:
        logger.warning(f"Failed to get job history for agent {agent_id}: {e}")
        return []


def _get_agent_crash_reports(
    agent_id: str,
    organization_id: int,
    db_path: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Get crash reports for an agent.

    Args:
        agent_id: Agent identifier.
        organization_id: Organization ID.
        db_path: Path to tenant database.
        limit: Maximum number of reports to return.

    Returns:
        List of crash report dictionaries.
    """
    try:
        from mysql_to_sheets.models.crash_reports import get_crash_report_repository

        repo = get_crash_report_repository(db_path)
        reports = repo.get_by_agent(agent_id, organization_id, limit=limit)

        return [r.to_dict() for r in reports]

    except (ImportError, ValueError) as e:
        logger.debug(f"Crash reports not available: {e}")
        return []
