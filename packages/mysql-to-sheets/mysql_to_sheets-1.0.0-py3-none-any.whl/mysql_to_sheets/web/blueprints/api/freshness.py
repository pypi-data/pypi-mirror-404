"""Freshness API blueprint for web dashboard.

Handles freshness/SLA monitoring operations via AJAX.
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request, session

from mysql_to_sheets.core.freshness import (
    check_all_freshness,
    get_freshness_report,
    get_freshness_status,
    set_sla,
)
from mysql_to_sheets.core.freshness_alerts import check_and_alert
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.web.decorators import login_required

logger = logging.getLogger("mysql_to_sheets.web.api.freshness")

freshness_api_bp = Blueprint("freshness_api", __name__, url_prefix="/api/freshness")


def _get_org_id() -> int | None:
    """Get current organization ID from session."""
    return session.get("organization_id")


@freshness_api_bp.route("", methods=["GET"])
@login_required
def list_freshness() -> tuple[Response, int]:
    """List freshness status for all sync configs.

    Query params:
    - enabled_only: Only check enabled configs (default true)

    Returns:
        JSON response with freshness statuses.
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

    enabled_only = request.args.get("enabled_only", "true").lower() == "true"

    db_path = get_tenant_db_path()
    statuses = check_all_freshness(
        organization_id=org_id,
        enabled_only=enabled_only,
        db_path=db_path,
    )

    return jsonify(
        {
            "success": True,
            "statuses": [s.to_dict() for s in statuses],
            "count": len(statuses),
        }
    ), 200


@freshness_api_bp.route("/report", methods=["GET"])
@login_required
def get_report() -> tuple[Response, int]:
    """Get freshness report for the organization.

    Returns:
        JSON response with freshness report.
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
    report = get_freshness_report(organization_id=org_id, db_path=db_path)

    return jsonify(
        {
            "success": True,
            **report,
        }
    ), 200


@freshness_api_bp.route("/<int:config_id>", methods=["GET"])
@login_required
def get_config_freshness(config_id: int) -> tuple[Response, int]:
    """Get freshness status for a specific config.

    Returns:
        JSON response with freshness status.
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
    status = get_freshness_status(
        config_id=config_id,
        organization_id=org_id,
        db_path=db_path,
    )

    if not status:
        return jsonify(
            {"success": False, "error": "Config not found", "message": "Config not found"}
        ), 404

    return jsonify(
        {
            "success": True,
            "status": status.to_dict(),
        }
    ), 200


@freshness_api_bp.route("/<int:config_id>/sla", methods=["PUT"])
@login_required
def update_sla(config_id: int) -> tuple[Response, int]:
    """Update SLA threshold for a config.

    Expects JSON body with:
    - sla_minutes: New SLA threshold in minutes

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

    data = request.get_json() or {}

    sla_minutes = data.get("sla_minutes")
    if not sla_minutes or not isinstance(sla_minutes, int) or sla_minutes < 1:
        return jsonify(
            {
                "success": False,
                "error": "sla_minutes must be a positive integer",
                "message": "sla_minutes must be a positive integer",
            }
        ), 400

    db_path = get_tenant_db_path()

    try:
        success = set_sla(
            config_id=config_id,
            organization_id=org_id,
            sla_minutes=sla_minutes,
            db_path=db_path,
        )
    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400

    if success:
        return jsonify(
            {
                "success": True,
                "message": f"SLA set to {sla_minutes} minutes",
                "sla_minutes": sla_minutes,
            }
        ), 200
    else:
        return jsonify(
            {"success": False, "error": "Config not found", "message": "Config not found"}
        ), 404


@freshness_api_bp.route("/check", methods=["POST"])
@login_required
def check_alerts() -> tuple[Response, int]:
    """Check freshness and trigger alerts.

    Query params:
    - send_notifications: Whether to send notifications (default false)

    Returns:
        JSON response with alerts.
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
    send_notifications = data.get("send_notifications", False)

    db_path = get_tenant_db_path()
    alerts = check_and_alert(
        organization_id=org_id,
        db_path=db_path,
        send_notifications=send_notifications,
    )

    return jsonify(
        {
            "success": True,
            "alerts": alerts,
            "alert_count": len(alerts),
            "notifications_sent": send_notifications,
        }
    ), 200
