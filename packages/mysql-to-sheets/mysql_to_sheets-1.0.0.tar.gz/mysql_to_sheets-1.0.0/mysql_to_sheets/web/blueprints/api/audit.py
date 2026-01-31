"""Audit API blueprint for web dashboard.

Handles audit log viewing and export via AJAX (multi-tenant).
"""

import io
import logging
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, Response, jsonify, request, session

from mysql_to_sheets.core.audit import VALID_AUDIT_ACTIONS, AuditAction, log_action
from mysql_to_sheets.core.audit_export import (
    ExportOptions,
    export_audit_logs,
    get_supported_formats,
)
from mysql_to_sheets.core.audit_retention import get_retention_stats
from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.audit_logs import get_audit_log_repository
from mysql_to_sheets.web.blueprints.api.auth_helpers import (
    _get_user_or_401,
    _require_admin,
)
from mysql_to_sheets.web.context import get_current_user

logger = logging.getLogger("mysql_to_sheets.web.api.audit")

audit_api_bp = Blueprint("audit_api", __name__, url_prefix="/api/audit")


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse date string to datetime."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None


@audit_api_bp.route("", methods=["GET"])
def list_audit_logs() -> tuple[Response, int]:
    """List audit logs with filters.

    Query params:
    - from_date: Start date (ISO format)
    - to_date: End date (ISO format)
    - action: Filter by action type
    - user_id: Filter by user ID
    - resource_type: Filter by resource type
    - limit: Maximum results (default 100)
    - offset: Results to skip (default 0)

    Returns:
        JSON response with audit logs list.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    organization_id = current["organization_id"]
    db_path = get_tenant_db_path()

    # Parse filters
    from_date = _parse_date(request.args.get("from_date"))
    to_date = _parse_date(request.args.get("to_date"))
    action = request.args.get("action")
    user_id = request.args.get("user_id", type=int)
    resource_type = request.args.get("resource_type")
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    # Enforce limits
    limit = min(limit, 1000)
    offset = max(offset, 0)

    # Log this access
    log_action(
        action=AuditAction.AUDIT_VIEWED,
        resource_type="audit",
        organization_id=organization_id,
        db_path=db_path,
        user_id=current["id"],
        metadata={
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "action_filter": action,
        },
    )

    repo = get_audit_log_repository(db_path)
    logs = repo.get_all(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )

    total = repo.count(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
        action=action,
        user_id=user_id,
    )

    return jsonify(
        {
            "success": True,
            "logs": [log.to_dict() for log in logs],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    ), 200


@audit_api_bp.route("/export", methods=["GET"])
def export_audit_logs_endpoint() -> Response | tuple[Response, int]:
    """Export audit logs to file.

    Query params:
    - format: Export format (csv, json, jsonl, cef)
    - from_date: Start date (ISO format)
    - to_date: End date (ISO format)
    - action: Filter by action type
    - user_id: Filter by user ID

    Returns:
        File download with appropriate content type.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    organization_id = current["organization_id"]
    db_path = get_tenant_db_path()

    # Parse options
    format_type = request.args.get("format", "csv").lower()
    from_date = _parse_date(request.args.get("from_date"))
    to_date = _parse_date(request.args.get("to_date"))
    action = request.args.get("action")
    user_id = request.args.get("user_id", type=int)

    if format_type not in get_supported_formats():
        return jsonify(
            {
                "success": False,
                "error": f"Unsupported format: {format_type}",
                "message": f"Unsupported format: {format_type}",
            }
        ), 400

    # Log this export
    log_action(
        action=AuditAction.AUDIT_EXPORTED,
        resource_type="audit",
        organization_id=organization_id,
        db_path=db_path,
        user_id=current["id"],
        metadata={
            "format": format_type,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "action_filter": action,
        },
    )

    options = ExportOptions(
        from_date=from_date,
        to_date=to_date,
        action=action,
        user_id=user_id,
    )

    # Export to string buffer
    output = io.StringIO()
    result = export_audit_logs(
        organization_id=organization_id,
        output=output,
        db_path=db_path,
        format=format_type,
        options=options,
    )

    content = output.getvalue()

    # Set content type and filename based on format
    content_types = {
        "csv": "text/csv",
        "json": "application/json",
        "jsonl": "application/x-ndjson",
        "cef": "text/plain",
    }
    extensions = {
        "csv": "csv",
        "json": "json",
        "jsonl": "jsonl",
        "cef": "cef",
    }

    content_type = content_types.get(format_type, "text/plain")
    extension = extensions.get(format_type, "txt")
    filename = f"audit_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.{extension}"

    response = Response(
        content,
        mimetype=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Record-Count": str(result.record_count),
        },
    )
    return response


@audit_api_bp.route("/stats", methods=["GET"])
def get_audit_stats() -> tuple[Response, int]:
    """Get audit log statistics.

    Returns:
        JSON response with audit statistics.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    organization_id = current["organization_id"]
    db_path = get_tenant_db_path()

    config = get_config()
    retention_days = config.audit_retention_days

    repo = get_audit_log_repository(db_path)
    stats = repo.get_stats(organization_id)
    retention = get_retention_stats(organization_id, db_path, retention_days)

    return jsonify(
        {
            "success": True,
            "stats": {
                "total_logs": stats.get("total_logs", 0),
                "oldest_log": stats.get("oldest_log"),
                "newest_log": stats.get("newest_log"),
                "logs_to_delete": retention.logs_to_delete,
                "retention_days": retention_days,
                "by_action": stats.get("by_action", {}),
                "by_resource_type": stats.get("by_resource_type", {}),
            },
        }
    ), 200


@audit_api_bp.route("/actions", methods=["GET"])
def list_audit_actions() -> tuple[Response, int]:
    """List all valid audit action types.

    Returns:
        JSON response with action types.
    """
    # This endpoint doesn't require auth - it's informational
    return jsonify(
        {
            "success": True,
            "actions": VALID_AUDIT_ACTIONS,
        }
    ), 200
