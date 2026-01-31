"""Jobs API blueprint for web dashboard.

Handles job queue operations via AJAX.
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request, session

from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.job_queue import (
    cancel_job,
    enqueue_job,
    get_job_status,
    get_queue_stats,
    list_jobs,
    retry_job,
)
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.jobs import VALID_JOB_STATUSES, VALID_JOB_TYPES, Job
from mysql_to_sheets.web.decorators import login_required

logger = logging.getLogger("mysql_to_sheets.web.api.jobs")

jobs_api_bp = Blueprint("jobs_api", __name__, url_prefix="/api/jobs")


def _job_to_dict(job: Job) -> dict[str, Any]:
    """Convert Job to JSON-serializable dict."""
    return job.to_dict()


def _get_org_id() -> int | None:
    """Get current organization ID from session."""
    return session.get("organization_id")


def _get_user_id() -> int | None:
    """Get current user ID from session."""
    return session.get("user_id")


@jobs_api_bp.route("", methods=["GET"])
@login_required
def list_jobs_endpoint() -> tuple[Response, int]:
    """List jobs for the current organization.

    Query params:
    - status: Filter by status
    - job_type: Filter by job type
    - limit: Maximum results (default 50)

    Returns:
        JSON response with job list.
    """
    org_id = _get_org_id()
    if not org_id:
        return jsonify(
            {
                "success": False,
                "error": "No organization selected",
                "message": "No organization selected",
            }
        ), 400

    status = request.args.get("status")
    job_type = request.args.get("job_type")
    limit = int(request.args.get("limit", 50))

    if status and status not in VALID_JOB_STATUSES:
        return jsonify(
            {
                "success": False,
                "error": f"Invalid status: {status}",
                "message": f"Invalid status: {status}",
            }
        ), 400

    if job_type and job_type not in VALID_JOB_TYPES:
        return jsonify(
            {
                "success": False,
                "error": f"Invalid job_type: {job_type}",
                "message": f"Invalid job_type: {job_type}",
            }
        ), 400

    db_path = get_tenant_db_path()
    jobs = list_jobs(
        organization_id=org_id,
        status=status,
        job_type=job_type,
        limit=limit,
        db_path=db_path,
    )

    return jsonify(
        {
            "success": True,
            "jobs": [_job_to_dict(j) for j in jobs],
            "count": len(jobs),
        }
    ), 200


@jobs_api_bp.route("", methods=["POST"])
@login_required
def create_job() -> tuple[Response, int]:
    """Create a new job.

    Expects JSON body with:
    - job_type: Job type (sync, export)
    - payload: Job payload data
    - priority: Optional priority (default 0)

    Returns:
        JSON response with created job ID.
    """
    org_id = _get_org_id()
    if not org_id:
        return jsonify(
            {
                "success": False,
                "error": "No organization selected",
                "message": "No organization selected",
            }
        ), 400

    data = request.get_json() or {}

    if not data.get("job_type"):
        return jsonify(
            {"success": False, "error": "job_type is required", "message": "job_type is required"}
        ), 400

    if data["job_type"] not in VALID_JOB_TYPES:
        return jsonify(
            {
                "success": False,
                "error": f"Invalid job_type: {data['job_type']}",
                "message": f"Invalid job_type: {data['job_type']}",
            }
        ), 400

    db_path = get_tenant_db_path()
    config = get_config()

    try:
        job = enqueue_job(
            job_type=data["job_type"],
            payload=data.get("payload", {}),
            organization_id=org_id,
            user_id=_get_user_id(),
            priority=data.get("priority", 0),
            max_attempts=config.job_max_attempts,
            db_path=db_path,
        )

        return jsonify(
            {
                "success": True,
                "job_id": job.id,
                "message": f"Job {job.id} created",
            }
        ), 201

    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 500


@jobs_api_bp.route("/stats", methods=["GET"])
@login_required
def get_stats() -> tuple[Response, int]:
    """Get queue statistics.

    Returns:
        JSON response with queue stats.
    """
    org_id = _get_org_id()
    if not org_id:
        return jsonify(
            {
                "success": False,
                "error": "No organization selected",
                "message": "No organization selected",
            }
        ), 400

    db_path = get_tenant_db_path()
    stats = get_queue_stats(organization_id=org_id, db_path=db_path)

    return jsonify(
        {
            "success": True,
            **stats,
            "total": sum(stats.values()),
        }
    ), 200


@jobs_api_bp.route("/<int:job_id>", methods=["GET"])
@login_required
def get_job(job_id: int) -> tuple[Response, int]:
    """Get a specific job.

    Returns:
        JSON response with job details.
    """
    org_id = _get_org_id()
    if not org_id:
        return jsonify(
            {
                "success": False,
                "error": "No organization selected",
                "message": "No organization selected",
            }
        ), 400

    db_path = get_tenant_db_path()
    job = get_job_status(job_id, organization_id=org_id, db_path=db_path)

    if not job:
        return jsonify(
            {"success": False, "error": "Job not found", "message": "Job not found"}
        ), 404

    return jsonify(
        {
            "success": True,
            "job": _job_to_dict(job),
        }
    ), 200


@jobs_api_bp.route("/<int:job_id>/cancel", methods=["POST"])
@login_required
def cancel_job_endpoint(job_id: int) -> tuple[Response, int]:
    """Cancel a pending job.

    Returns:
        JSON response with result.
    """
    org_id = _get_org_id()
    if not org_id:
        return jsonify(
            {
                "success": False,
                "error": "No organization selected",
                "message": "No organization selected",
            }
        ), 400

    db_path = get_tenant_db_path()
    success = cancel_job(job_id, org_id, db_path=db_path)

    if success:
        return jsonify(
            {
                "success": True,
                "message": f"Job {job_id} cancelled",
            }
        ), 200
    else:
        return jsonify(
            {
                "success": False,
                "error": "Job not found or not in pending status",
                "message": "Job not found or not in pending status",
            }
        ), 400


@jobs_api_bp.route("/<int:job_id>/retry", methods=["POST"])
@login_required
def retry_job_endpoint(job_id: int) -> tuple[Response, int]:
    """Retry a failed job.

    Returns:
        JSON response with result.
    """
    org_id = _get_org_id()
    if not org_id:
        return jsonify(
            {
                "success": False,
                "error": "No organization selected",
                "message": "No organization selected",
            }
        ), 400

    db_path = get_tenant_db_path()
    job = retry_job(job_id, org_id, db_path=db_path)

    if job:
        return jsonify(
            {
                "success": True,
                "message": f"Job {job_id} requeued for retry",
                "job": _job_to_dict(job),
            }
        ), 200
    else:
        return jsonify(
            {
                "success": False,
                "error": "Job not found or not in failed status",
                "message": "Job not found or not in failed status",
            }
        ), 400
