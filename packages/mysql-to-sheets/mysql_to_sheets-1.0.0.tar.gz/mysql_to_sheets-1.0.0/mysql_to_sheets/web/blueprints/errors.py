"""Error log blueprint for web dashboard.

Provides error log viewing and filtering.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import Blueprint, Response, jsonify, render_template, request

from mysql_to_sheets import __version__
from mysql_to_sheets.core.exceptions import (
    REMEDIATION_HINTS,
    ErrorCategory,
    get_error_category,
)
from mysql_to_sheets.web.history import sync_history

logger = logging.getLogger("mysql_to_sheets.web.errors")

errors_bp = Blueprint("errors", __name__)


@errors_bp.route("/errors")
def errors_page() -> str:
    """Render the error log page.

    Returns:
        Rendered error log template.
    """
    return render_template(
        "errors.html",
        version=__version__,
        error_categories=[c.value for c in ErrorCategory],
    )


@errors_bp.route("/api/errors", methods=["GET"])
def api_errors() -> tuple[Response, int]:
    """Get error log entries.

    Query params:
        code: Filter by error code
        category: Filter by error category
        hours: Hours to look back (default 24)
        limit: Max entries to return (default 50)

    Returns:
        JSON response with error entries.
    """
    code_filter = request.args.get("code")
    category_filter = request.args.get("category")
    hours = int(request.args.get("hours", "24"))
    limit = int(request.args.get("limit", "50"))

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    errors = []

    for entry in sync_history.get_all():
        # Only include failed entries
        if entry.get("success", True):
            continue

        # Parse timestamp
        try:
            ts_str = entry.get("timestamp", "")
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts.replace(tzinfo=None) < cutoff:
                continue
        except (ValueError, TypeError):
            continue

        # Apply filters
        if code_filter and entry.get("error_code") != code_filter:
            continue
        if category_filter and entry.get("error_category") != category_filter:
            continue

        # Add remediation hint
        error_code = entry.get("error_code")
        remediation = REMEDIATION_HINTS.get(error_code) if error_code else None

        errors.append(
            {
                "timestamp": entry.get("timestamp"),
                "message": entry.get("message"),
                "error_code": error_code,
                "error_category": entry.get("error_category"),
                "sheet_id": entry.get("sheet_id"),
                "worksheet": entry.get("worksheet"),
                "remediation": remediation,
            }
        )

        if len(errors) >= limit:
            break

    return jsonify(
        {
            "errors": errors,
            "total": len(errors),
            "filters": {
                "code": code_filter,
                "category": category_filter,
                "hours": hours,
            },
        }
    ), 200


@errors_bp.route("/api/errors/stats", methods=["GET"])
def api_error_stats() -> tuple[Response, int]:
    """Get error statistics.

    Query params:
        hours: Hours to look back (default 24)

    Returns:
        JSON response with error statistics.
    """
    hours = int(request.args.get("hours", "24"))
    stats = sync_history.get_error_stats(hours)

    # Add top error codes
    top_codes = sorted(
        stats["errors_by_code"].items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    return jsonify(
        {
            "total_errors_24h": stats["total_errors"],
            "errors_by_category": stats["errors_by_category"],
            "top_error_codes": [{"code": code, "count": count} for code, count in top_codes],
            "hours": hours,
        }
    ), 200


@errors_bp.route("/api/errors/codes", methods=["GET"])
def api_error_codes() -> tuple[Response, int]:
    """Get all error codes with descriptions and remediation hints.

    Returns:
        JSON response with error code reference.
    """
    from mysql_to_sheets.core.exceptions import ErrorCode

    codes = []
    for attr in dir(ErrorCode):
        if attr.startswith("_"):
            continue
        code = getattr(ErrorCode, attr)
        if not isinstance(code, str):
            continue

        category = get_error_category(code)
        remediation = REMEDIATION_HINTS.get(code)

        codes.append(
            {
                "code": code,
                "name": attr,
                "category": category.value if category else None,
                "remediation": remediation,
            }
        )

    return jsonify(
        {
            "codes": sorted(codes, key=lambda x: x["code"]),
        }
    ), 200
