"""Freshness/SLA monitoring blueprint for Flask web dashboard.

Displays data freshness status, SLA thresholds, and health metrics.
"""

import logging
from typing import Any, cast

from flask import Blueprint, Response, jsonify, redirect, render_template, request, session, url_for

from mysql_to_sheets import __version__
from mysql_to_sheets.core.freshness import (
    FRESHNESS_FRESH,
    FRESHNESS_STALE,
    FRESHNESS_UNKNOWN,
    FRESHNESS_WARNING,
    check_all_freshness,
    get_freshness_report,
    get_freshness_status,
    set_sla,
)
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.web.context import get_current_user
from mysql_to_sheets.web.decorators import login_required

logger = logging.getLogger("mysql_to_sheets.web.freshness")

freshness_bp = Blueprint("freshness", __name__)


@freshness_bp.route("/freshness")
@login_required
def freshness_page() -> str | Response:
    """Render the freshness/SLA monitoring page.

    Shows data freshness status for all sync configurations.

    Returns:
        Rendered HTML template.
    """
    current = get_current_user()
    if not current:
        return cast(Response, redirect(url_for("auth.login")))

    db_path = get_tenant_db_path()
    organization_id = current["organization_id"]

    # Get freshness report
    report = get_freshness_report(organization_id, db_path)

    return render_template(
        "freshness.html",
        version=__version__,
        report=report,
        statuses=report.get("statuses", []),
        counts=report.get("counts", {}),
        health_percent=report.get("health_percent", 0),
        total_configs=report.get("total_configs", 0),
    )


# Page-level API endpoints
freshness_page_api_bp = Blueprint("freshness_page_api", __name__, url_prefix="/api/freshness-page")


@freshness_page_api_bp.route("/report", methods=["GET"])
def api_freshness_report() -> Response | tuple[Response, int]:
    """Get freshness report via API.

    Returns:
        JSON response with freshness report.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    db_path = get_tenant_db_path()
    organization_id = current["organization_id"]

    report = get_freshness_report(organization_id, db_path)

    return jsonify(
        {
            "success": True,
            "report": report,
        }
    ), 200


@freshness_page_api_bp.route("/status/<int:config_id>", methods=["GET"])
def api_freshness_status(config_id: int) -> Response | tuple[Response, int]:
    """Get freshness status for a specific config.

    Args:
        config_id: Sync configuration ID.

    Returns:
        JSON response with freshness status.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    db_path = get_tenant_db_path()
    organization_id = current["organization_id"]

    status = get_freshness_status(config_id, organization_id, db_path)
    if not status:
        return jsonify({"success": False, "error": "Config not found"}), 404

    return jsonify(
        {
            "success": True,
            "status": status.to_dict(),
        }
    ), 200


@freshness_page_api_bp.route("/sla/<int:config_id>", methods=["PUT"])
def api_set_sla(config_id: int) -> Response | tuple[Response, int]:
    """Set SLA threshold for a config.

    Args:
        config_id: Sync configuration ID.

    Returns:
        JSON response with update result.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Check permission (admin+ or operator)
    if current["role"] not in ("owner", "admin", "operator"):
        return jsonify({"success": False, "error": "Permission denied"}), 403

    data = request.get_json() or {}
    sla_minutes = data.get("sla_minutes")

    if sla_minutes is None:
        return jsonify({"success": False, "error": "sla_minutes is required"}), 400

    try:
        sla_minutes = int(sla_minutes)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "sla_minutes must be an integer"}), 400

    if sla_minutes < 1:
        return jsonify({"success": False, "error": "sla_minutes must be at least 1"}), 400

    db_path = get_tenant_db_path()
    organization_id = current["organization_id"]

    try:
        updated = set_sla(config_id, organization_id, sla_minutes, db_path)
        if not updated:
            return jsonify({"success": False, "error": "Config not found"}), 404

        return jsonify(
            {
                "success": True,
                "message": f"SLA set to {sla_minutes} minutes",
            }
        ), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to set SLA: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@freshness_page_api_bp.route("/check", methods=["POST"])
def api_check_freshness() -> Response | tuple[Response, int]:
    """Trigger a manual freshness check.

    Returns:
        JSON response with check results.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    db_path = get_tenant_db_path()
    organization_id = current["organization_id"]

    # Get all freshness statuses
    statuses = check_all_freshness(organization_id, enabled_only=True, db_path=db_path)

    return jsonify(
        {
            "success": True,
            "statuses": [s.to_dict() for s in statuses],
            "total": len(statuses),
            "stale": sum(1 for s in statuses if s.status == FRESHNESS_STALE),
            "warning": sum(1 for s in statuses if s.status == FRESHNESS_WARNING),
            "fresh": sum(1 for s in statuses if s.status == FRESHNESS_FRESH),
            "unknown": sum(1 for s in statuses if s.status == FRESHNESS_UNKNOWN),
        }
    ), 200
