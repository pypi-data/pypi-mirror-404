"""Schedules API blueprint for web dashboard.

Handles schedule CRUD operations via AJAX.
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request, session

from mysql_to_sheets.core.exceptions import SchedulerError
from mysql_to_sheets.core.scheduler import ScheduledJob, get_scheduler_service
from mysql_to_sheets.core.tenant import get_tenant_db_path

logger = logging.getLogger("mysql_to_sheets.web.api.schedules")

schedules_api_bp = Blueprint("schedules_api", __name__, url_prefix="/api/schedules")


def _job_to_dict(job: ScheduledJob) -> dict[str, Any]:
    """Convert ScheduledJob to JSON-serializable dict."""
    return {
        "id": job.id,
        "name": job.name,
        "cron_expression": job.cron_expression,
        "interval_minutes": job.interval_minutes,
        "sheet_id": job.sheet_id,
        "worksheet_name": job.worksheet_name,
        "sql_query": job.sql_query,
        "notify_on_success": job.notify_on_success,
        "notify_on_failure": job.notify_on_failure,
        "enabled": job.enabled,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None,
        "last_run_success": job.last_run_success,
        "last_run_message": job.last_run_message,
        "last_run_rows": job.last_run_rows,
        "last_run_duration_ms": job.last_run_duration_ms,
        "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
        "status": job.status.value,
        "schedule_display": job.schedule_display,
    }


@schedules_api_bp.route("", methods=["GET"])
def list_schedules() -> tuple[Response, int]:
    """List all scheduled jobs.

    Query params:
    - include_disabled: If true, include disabled jobs

    Returns:
        JSON response with schedule list.
    """
    include_disabled = request.args.get("include_disabled", "false").lower() == "true"

    service = get_scheduler_service()
    jobs = service.get_all_jobs(include_disabled=include_disabled)

    return jsonify(
        {
            "schedules": [_job_to_dict(j) for j in jobs],
            "total": len(jobs),
        }
    ), 200


@schedules_api_bp.route("", methods=["POST"])
def create_schedule() -> tuple[Response, int]:
    """Create a new scheduled job.

    Expects JSON body with:
    - name: Job name (required)
    - cron_expression OR interval_minutes (one required)
    - sheet_id, worksheet_name, sql_query (optional overrides)
    - notify_on_success, notify_on_failure (optional)

    Returns:
        JSON response with created job.
    """
    data = request.get_json() or {}

    if not data.get("name"):
        return jsonify(
            {
                "success": False,
                "error": "Name is required",
                "message": "Name is required",
            }
        ), 400

    if not data.get("cron_expression") and not data.get("interval_minutes"):
        return jsonify(
            {
                "success": False,
                "error": "Either cron_expression or interval_minutes is required",
                "message": "Either cron_expression or interval_minutes is required",
            }
        ), 400

    # Enforce tier quota for schedules
    org_id = session.get("organization_id")
    if org_id:
        try:
            from mysql_to_sheets.core.tier import (  # type: ignore[attr-defined]
                TierError,
                enforce_quota,
            )
            from mysql_to_sheets.models.organizations import get_organization_repository

            db_path = get_tenant_db_path()
            org_repo = get_organization_repository(db_path)
            org = org_repo.get_by_id(org_id)
            if org:
                org_tier = org.subscription_tier or "free"
                service = get_scheduler_service()
                existing_schedules = service.get_all_jobs(include_disabled=True)
                try:
                    enforce_quota(
                        org_tier,
                        "schedules",
                        len(existing_schedules),
                        organization_id=org_id,
                    )
                except TierError as e:
                    return jsonify(
                        {
                            "success": False,
                            "error": e.message,
                            "message": e.message,
                            "upgrade_required": True,
                            "current_tier": org_tier,
                        }
                    ), 403
        except Exception as e:
            logger.debug(f"Quota check skipped: {e}")

    try:
        service = get_scheduler_service()

        # Parse sheet_id if it's a URL
        sheet_id = data.get("sheet_id")
        if sheet_id:
            from mysql_to_sheets.core.sheets_utils import parse_sheet_id

            try:
                sheet_id = parse_sheet_id(sheet_id)
            except ValueError as e:
                return jsonify(
                    {
                        "success": False,
                        "error": str(e),
                        "message": str(e),
                    }
                ), 400

        job = ScheduledJob(
            name=data["name"],
            cron_expression=data.get("cron_expression"),
            interval_minutes=data.get("interval_minutes"),
            sheet_id=sheet_id,
            worksheet_name=data.get("worksheet_name"),
            sql_query=data.get("sql_query"),
            notify_on_success=data.get("notify_on_success"),
            notify_on_failure=data.get("notify_on_failure"),
        )

        created = service.add_job(job)

        return jsonify(
            {
                "success": True,
                "schedule": _job_to_dict(created),
            }
        ), 201

    except SchedulerError as e:
        return jsonify(
            {
                "success": False,
                "error": e.message,
                "message": e.message,
            }
        ), 400
    except Exception as e:
        logger.exception(f"Error creating schedule: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 500


@schedules_api_bp.route("/<int:schedule_id>", methods=["GET"])
def get_schedule(schedule_id: int) -> tuple[Response, int]:
    """Get a scheduled job by ID.

    Returns:
        JSON response with job details.
    """
    service = get_scheduler_service()
    job = service.get_job(schedule_id)

    if not job:
        return jsonify(
            {
                "success": False,
                "error": f"Schedule {schedule_id} not found",
                "message": f"Schedule {schedule_id} not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "schedule": _job_to_dict(job),
        }
    ), 200


@schedules_api_bp.route("/<int:schedule_id>", methods=["PUT"])
def update_schedule(schedule_id: int) -> tuple[Response, int]:
    """Update a scheduled job.

    Returns:
        JSON response with updated job.
    """
    data = request.get_json() or {}

    service = get_scheduler_service()
    job = service.get_job(schedule_id)

    if not job:
        return jsonify(
            {
                "success": False,
                "error": f"Schedule {schedule_id} not found",
                "message": f"Schedule {schedule_id} not found",
            }
        ), 404

    # Apply updates
    if "name" in data:
        job.name = data["name"]
    if "cron_expression" in data:
        job.cron_expression = data["cron_expression"]
        job.interval_minutes = None
    if "interval_minutes" in data:
        job.interval_minutes = data["interval_minutes"]
        job.cron_expression = None
    if "sheet_id" in data:
        from mysql_to_sheets.core.sheets_utils import parse_sheet_id

        try:
            job.sheet_id = parse_sheet_id(data["sheet_id"]) if data["sheet_id"] else None
        except ValueError as e:
            return jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "message": str(e),
                }
            ), 400
    if "worksheet_name" in data:
        job.worksheet_name = data["worksheet_name"]
    if "sql_query" in data:
        job.sql_query = data["sql_query"]
    if "notify_on_success" in data:
        job.notify_on_success = data["notify_on_success"]
    if "notify_on_failure" in data:
        job.notify_on_failure = data["notify_on_failure"]
    if "enabled" in data:
        job.enabled = data["enabled"]

    try:
        updated = service.update_job(job)
        return jsonify(
            {
                "success": True,
                "schedule": _job_to_dict(updated),
            }
        ), 200

    except SchedulerError as e:
        return jsonify(
            {
                "success": False,
                "error": e.message,
                "message": e.message,
            }
        ), 400


@schedules_api_bp.route("/<int:schedule_id>", methods=["DELETE"])
def delete_schedule(schedule_id: int) -> tuple[Response, int]:
    """Delete a scheduled job.

    Returns:
        JSON response confirming deletion.
    """
    service = get_scheduler_service()
    deleted = service.delete_job(schedule_id)

    if not deleted:
        return jsonify(
            {
                "success": False,
                "error": f"Schedule {schedule_id} not found",
                "message": f"Schedule {schedule_id} not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "message": f"Schedule {schedule_id} deleted",
        }
    ), 200


@schedules_api_bp.route("/<int:schedule_id>/trigger", methods=["POST"])
def trigger_schedule(schedule_id: int) -> tuple[Response, int]:
    """Trigger a scheduled job to run immediately.

    Returns:
        JSON response with updated job.
    """
    service = get_scheduler_service()
    job = service.get_job(schedule_id)

    if not job:
        return jsonify(
            {
                "success": False,
                "error": f"Schedule {schedule_id} not found",
                "message": f"Schedule {schedule_id} not found",
            }
        ), 404

    try:
        service.trigger_job(schedule_id)
        # Refresh job to get updated status
        job = service.get_job(schedule_id)
        if not job:
            return jsonify({"success": False, "error": "Schedule not found"}), 404
        return jsonify(
            {
                "success": True,
                "schedule": _job_to_dict(job),
            }
        ), 200

    except SchedulerError as e:
        return jsonify(
            {
                "success": False,
                "error": e.message,
                "message": e.message,
            }
        ), 400


@schedules_api_bp.route("/<int:schedule_id>/enable", methods=["POST"])
def enable_schedule(schedule_id: int) -> tuple[Response, int]:
    """Enable a scheduled job.

    Returns:
        JSON response with updated job.
    """
    service = get_scheduler_service()
    job = service.get_job(schedule_id)

    if not job:
        return jsonify(
            {
                "success": False,
                "error": f"Schedule {schedule_id} not found",
                "message": f"Schedule {schedule_id} not found",
            }
        ), 404

    try:
        service.enable_job(schedule_id)
        job = service.get_job(schedule_id)
        if not job:
            return jsonify({"success": False, "error": "Schedule not found"}), 404
        return jsonify(
            {
                "success": True,
                "schedule": _job_to_dict(job),
            }
        ), 200

    except SchedulerError as e:
        return jsonify(
            {
                "success": False,
                "error": e.message,
                "message": e.message,
            }
        ), 400


@schedules_api_bp.route("/<int:schedule_id>/disable", methods=["POST"])
def disable_schedule(schedule_id: int) -> tuple[Response, int]:
    """Disable a scheduled job.

    Returns:
        JSON response with updated job.
    """
    service = get_scheduler_service()
    job = service.get_job(schedule_id)

    if not job:
        return jsonify(
            {
                "success": False,
                "error": f"Schedule {schedule_id} not found",
                "message": f"Schedule {schedule_id} not found",
            }
        ), 404

    try:
        service.disable_job(schedule_id)
        job = service.get_job(schedule_id)
        if not job:
            return jsonify({"success": False, "error": "Schedule not found"}), 404
        return jsonify(
            {
                "success": True,
                "schedule": _job_to_dict(job),
            }
        ), 200

    except SchedulerError as e:
        return jsonify(
            {
                "success": False,
                "error": e.message,
                "message": e.message,
            }
        ), 400
