"""Multi-Sheet Sync blueprint for Flask web dashboard.

Provides a web interface for syncing data from a database to multiple
Google Sheets simultaneously. Supports per-target filtering and parallel execution.
"""

import logging
from typing import Any, cast

from flask import (
    Blueprint,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from mysql_to_sheets import __version__
from mysql_to_sheets.core.config import SheetTarget, get_config
from mysql_to_sheets.core.multi_sheet_sync import run_multi_sheet_sync
from mysql_to_sheets.core.tier import FEATURE_TIERS, Tier
from mysql_to_sheets.web.context import (
    get_current_user,
    get_effective_tier_from_license,
    has_tier_access,
)
from mysql_to_sheets.web.decorators import login_required, tier_required

logger = logging.getLogger("mysql_to_sheets.web.multi_sheet")

# Page blueprint
multi_sheet_bp = Blueprint("multi_sheet", __name__)


@multi_sheet_bp.route("/multi-sync")
@login_required
def index() -> str | Response:
    """Render the multi-sheet sync page.

    Returns:
        Rendered HTML template.
    """
    current = get_current_user()
    if not current:
        return cast(Response, redirect(url_for("auth.login")))

    # Check tier access - use license-based tier check
    feature_available = has_tier_access("multi_sheet")
    required_tier = FEATURE_TIERS.get("multi_sheet", Tier.BUSINESS)
    current_tier_str = get_effective_tier_from_license()
    try:
        org_tier = Tier(current_tier_str)
    except ValueError:
        org_tier = Tier.FREE

    # Get default config for pre-filling form
    try:
        config = get_config()
        db_type = config.db_type or "mysql"
        default_query = config.sql_query or "SELECT * FROM your_table LIMIT 100"
    except Exception:
        db_type = "mysql"
        default_query = "SELECT * FROM your_table LIMIT 100"

    return render_template(
        "multi_sheet.html",
        version=__version__,
        feature_available=feature_available,
        required_tier=required_tier.value.title(),
        current_tier=org_tier.value.title(),
        db_type=db_type,
        default_query=default_query,
        sync_modes=[
            {
                "value": "replace",
                "label": "Replace",
                "description": "Clear sheet and write all data",
            },
            {"value": "append", "label": "Append", "description": "Add rows without clearing"},
        ],
    )


# API blueprint
multi_sheet_api_bp = Blueprint("multi_sheet_api", __name__, url_prefix="/api/multi-sync")


def _parse_targets(targets_data: list[dict[str, Any]]) -> list[SheetTarget]:
    """Parse target configurations from request data.

    Args:
        targets_data: List of target dictionaries from request.

    Returns:
        List of SheetTarget objects.
    """
    targets = []
    for t in targets_data:
        sheet_id = t.get("sheet_id", "").strip()
        if not sheet_id:
            continue

        # Parse column filter
        column_filter = t.get("column_filter")
        if isinstance(column_filter, str):
            column_filter = [c.strip() for c in column_filter.split(",") if c.strip()]
        elif not column_filter:
            column_filter = None

        target = SheetTarget(
            sheet_id=sheet_id,
            worksheet_name=t.get("worksheet_name", "Sheet1").strip() or "Sheet1",
            mode=t.get("mode", "replace"),
            column_filter=column_filter,
            row_filter=t.get("row_filter", "").strip() or None,
        )
        targets.append(target)

    return targets


@multi_sheet_api_bp.route("/preview", methods=["POST"])
@tier_required("multi_sheet")
def api_preview() -> Response | tuple[Response, int]:
    """Preview multi-sheet sync operation without executing.

    Requires BUSINESS tier or higher.

    Returns:
        JSON response with preview data for each target.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    data = request.get_json() or {}

    # Parse targets
    targets_data = data.get("targets", [])
    if not targets_data:
        return jsonify({"success": False, "error": "At least one target sheet is required"}), 400

    targets = _parse_targets(targets_data)
    if not targets:
        return jsonify({"success": False, "error": "No valid targets provided"}), 400

    try:
        # Build config with optional query override
        config = get_config()
        if data.get("query"):
            config = config.with_overrides(sql_query=data["query"])

        # Run preview (dry_run mode)
        result = run_multi_sheet_sync(
            config=config,
            targets=targets,
            dry_run=True,
            parallel=data.get("parallel", False),
        )

        return jsonify(
            {
                "success": True,
                "preview": {
                    "total_rows_fetched": result.total_rows_fetched,
                    "targets_count": len(targets),
                    "target_results": [r.to_dict() for r in result.target_results],
                    "message": result.message,
                },
            }
        ), 200

    except Exception as e:
        logger.exception("Multi-sheet sync preview failed")
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500


@multi_sheet_api_bp.route("/execute", methods=["POST"])
@tier_required("multi_sheet")
def api_execute() -> Response | tuple[Response, int]:
    """Execute multi-sheet sync operation.

    Syncs data from database to multiple Google Sheets.
    Requires BUSINESS tier or higher.

    Returns:
        JSON response with execution results.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    data = request.get_json() or {}

    # Parse targets
    targets_data = data.get("targets", [])
    if not targets_data:
        return jsonify({"success": False, "error": "At least one target sheet is required"}), 400

    targets = _parse_targets(targets_data)
    if not targets:
        return jsonify({"success": False, "error": "No valid targets provided"}), 400

    try:
        # Build config with optional query override
        config = get_config()
        if data.get("query"):
            config = config.with_overrides(sql_query=data["query"])

        # Execute multi-sheet sync
        parallel = data.get("parallel", False)
        max_workers = data.get("max_workers", 4)

        result = run_multi_sheet_sync(
            config=config,
            targets=targets,
            dry_run=False,
            parallel=parallel,
            max_workers=max_workers,
        )

        if result.success:
            succeeded = sum(1 for r in result.target_results if r.success)
            logger.info(
                f"Multi-sheet sync completed: {succeeded}/{len(targets)} targets, "
                f"{result.total_rows_fetched} rows fetched"
            )

        return jsonify(
            {
                "success": result.success,
                "result": result.to_dict(),
            }
        ), 200 if result.success else 500

    except Exception as e:
        logger.exception("Multi-sheet sync execution failed")
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500


@multi_sheet_api_bp.route("/validate-sheet", methods=["POST"])
def api_validate_sheet() -> Response | tuple[Response, int]:
    """Validate a Google Sheet is accessible.

    Returns:
        JSON response with validation result.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    data = request.get_json() or {}
    sheet_id = data.get("sheet_id", "").strip()
    worksheet_name = data.get("worksheet_name", "Sheet1").strip()

    if not sheet_id:
        return jsonify({"success": False, "error": "sheet_id is required"}), 400

    try:
        import gspread

        config = get_config()
        gc = gspread.service_account(filename=config.service_account_file)  # type: ignore[attr-defined]
        spreadsheet = gc.open_by_key(sheet_id)

        # Get worksheet list
        worksheets = [ws.title for ws in spreadsheet.worksheets()]

        # Check if specified worksheet exists
        worksheet_exists = worksheet_name in worksheets

        return jsonify(
            {
                "success": True,
                "sheet_id": sheet_id,
                "title": spreadsheet.title,
                "worksheets": worksheets,
                "worksheet_exists": worksheet_exists,
                "specified_worksheet": worksheet_name,
            }
        ), 200

    except gspread.exceptions.SpreadsheetNotFound:
        return jsonify(
            {
                "success": False,
                "error": "Spreadsheet not found. Check the ID and ensure the service account has access.",
            }
        ), 404
    except Exception as e:
        logger.exception(f"Failed to validate sheet {sheet_id}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500


@multi_sheet_api_bp.route("/test-query", methods=["POST"])
def api_test_query() -> Response | tuple[Response, int]:
    """Test the SQL query and return column headers.

    Returns:
        JSON response with query results preview.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    data = request.get_json() or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"success": False, "error": "query is required"}), 400

    try:
        config = get_config()
        config = config.with_overrides(sql_query=query)

        from mysql_to_sheets.core.sync import fetch_data

        # Fetch a limited amount for testing
        headers, rows = fetch_data(config)

        # Limit preview to first 5 rows
        preview_rows = rows[:5] if rows else []

        return jsonify(
            {
                "success": True,
                "headers": headers,
                "row_count": len(rows),
                "preview_rows": preview_rows,
            }
        ), 200

    except Exception as e:
        logger.exception("Query test failed")
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500
