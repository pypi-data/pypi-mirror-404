"""Reverse Sync blueprint for Flask web dashboard.

Provides a web interface for syncing data from Google Sheets back to a database.
Supports multiple conflict resolution modes and column mapping.
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
from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.reverse_sync import (
    ConflictMode,
    ReverseSyncConfig,
    run_reverse_sync,
)
from mysql_to_sheets.core.tier import FEATURE_TIERS, Tier
from mysql_to_sheets.web.context import (
    get_current_user,
    get_effective_tier_from_license,
    has_tier_access,
)
from mysql_to_sheets.web.decorators import login_required, tier_required

logger = logging.getLogger("mysql_to_sheets.web.reverse_sync")

# Page blueprint
reverse_sync_bp = Blueprint("reverse_sync", __name__)


@reverse_sync_bp.route("/reverse-sync")
@login_required
def index() -> str | Response:
    """Render the reverse sync page.

    Returns:
        Rendered HTML template.
    """
    current = get_current_user()
    if not current:
        return cast(Response, redirect(url_for("auth.login")))

    # Check tier access - use license-based tier check
    feature_available = has_tier_access("reverse_sync")
    required_tier = FEATURE_TIERS.get("reverse_sync", Tier.PRO)
    current_tier_str = get_effective_tier_from_license()
    try:
        org_tier = Tier(current_tier_str)
    except ValueError:
        org_tier = Tier.FREE

    # Get default config for pre-filling form
    try:
        config = get_config()
        default_sheet_id = config.google_sheet_id or ""
        default_worksheet = config.google_worksheet_name or "Sheet1"
        db_type = config.db_type or "mysql"
    except Exception:
        default_sheet_id = ""
        default_worksheet = "Sheet1"
        db_type = "mysql"

    return render_template(
        "reverse_sync.html",
        version=__version__,
        feature_available=feature_available,
        required_tier=required_tier.value.title(),
        current_tier=org_tier.value.title(),
        default_sheet_id=default_sheet_id,
        default_worksheet=default_worksheet,
        db_type=db_type,
        conflict_modes=[
            {
                "value": "overwrite",
                "label": "Overwrite (Upsert)",
                "description": "Update existing rows, insert new ones",
            },
            {
                "value": "skip",
                "label": "Skip Existing",
                "description": "Only insert rows that don't exist",
            },
            {
                "value": "error",
                "label": "Error on Conflict",
                "description": "Fail if any row already exists",
            },
        ],
    )


# API blueprint
reverse_sync_api_bp = Blueprint("reverse_sync_api", __name__, url_prefix="/api/reverse-sync")


@reverse_sync_api_bp.route("/preview", methods=["POST"])
@tier_required("reverse_sync")
def api_preview() -> Response | tuple[Response, int]:
    """Preview reverse sync operation without executing.

    Fetches data from the sheet and shows what would be synced.
    Requires PRO tier or higher.

    Returns:
        JSON response with preview data.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    data = request.get_json() or {}

    # Validate required fields
    table_name = data.get("table_name")
    if not table_name:
        return jsonify({"success": False, "error": "table_name is required"}), 400

    try:
        # Build config with overrides from request
        config = get_config()
        if data.get("sheet_id"):
            config = config.with_overrides(google_sheet_id=data["sheet_id"])
        if data.get("worksheet"):
            config = config.with_overrides(google_worksheet_name=data["worksheet"])

        # Build reverse sync config
        key_columns = data.get("key_columns", [])
        if isinstance(key_columns, str):
            key_columns = [c.strip() for c in key_columns.split(",") if c.strip()]

        conflict_mode_str = data.get("conflict_mode", "overwrite")
        try:
            conflict_mode = ConflictMode(conflict_mode_str)
        except ValueError:
            conflict_mode = ConflictMode.OVERWRITE

        column_mapping = data.get("column_mapping")
        if isinstance(column_mapping, str):
            # Parse JSON string if provided
            import json

            try:
                column_mapping = json.loads(column_mapping) if column_mapping else None
            except json.JSONDecodeError:
                column_mapping = None

        reverse_config = ReverseSyncConfig(
            table_name=table_name,
            key_columns=key_columns,
            conflict_mode=conflict_mode,
            column_mapping=column_mapping,
            sheet_range=data.get("sheet_range"),
            skip_header=data.get("skip_header", True),
        )

        # Run preview (dry_run mode)
        result = run_reverse_sync(
            config=config,
            reverse_config=reverse_config,
            dry_run=True,
        )

        return jsonify(
            {
                "success": True,
                "preview": {
                    "rows_to_sync": result.rows_processed,
                    "table_name": table_name,
                    "key_columns": key_columns,
                    "conflict_mode": conflict_mode.value,
                    "message": result.message,
                },
            }
        ), 200

    except Exception as e:
        logger.exception("Reverse sync preview failed")
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500


@reverse_sync_api_bp.route("/execute", methods=["POST"])
def api_execute() -> Response | tuple[Response, int]:
    """Execute reverse sync operation.

    Syncs data from Google Sheets to the database.

    Returns:
        JSON response with execution results.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Check tier access
    org_tier_str = current.get("organization_tier", "free")
    try:
        org_tier = Tier(org_tier_str.lower())
    except ValueError:
        org_tier = Tier.FREE

    required_tier = FEATURE_TIERS.get("reverse_sync", Tier.PRO)
    if org_tier < required_tier:
        return jsonify(
            {
                "success": False,
                "error": f"Reverse Sync requires {required_tier.value.title()} tier or higher",
            }
        ), 403

    data = request.get_json() or {}

    # Validate required fields
    table_name = data.get("table_name")
    if not table_name:
        return jsonify({"success": False, "error": "table_name is required"}), 400

    try:
        # Build config with overrides from request
        config = get_config()
        if data.get("sheet_id"):
            config = config.with_overrides(google_sheet_id=data["sheet_id"])
        if data.get("worksheet"):
            config = config.with_overrides(google_worksheet_name=data["worksheet"])

        # Build reverse sync config
        key_columns = data.get("key_columns", [])
        if isinstance(key_columns, str):
            key_columns = [c.strip() for c in key_columns.split(",") if c.strip()]

        conflict_mode_str = data.get("conflict_mode", "overwrite")
        try:
            conflict_mode = ConflictMode(conflict_mode_str)
        except ValueError:
            conflict_mode = ConflictMode.OVERWRITE

        column_mapping = data.get("column_mapping")
        if isinstance(column_mapping, str):
            import json

            try:
                column_mapping = json.loads(column_mapping) if column_mapping else None
            except json.JSONDecodeError:
                column_mapping = None

        reverse_config = ReverseSyncConfig(
            table_name=table_name,
            key_columns=key_columns,
            conflict_mode=conflict_mode,
            column_mapping=column_mapping,
            sheet_range=data.get("sheet_range"),
            skip_header=data.get("skip_header", True),
            batch_size=data.get("batch_size", 1000),
        )

        # Execute reverse sync
        result = run_reverse_sync(
            config=config,
            reverse_config=reverse_config,
            dry_run=False,
        )

        if result.success:
            logger.info(
                f"Reverse sync completed: {result.rows_inserted} inserted, "
                f"{result.rows_updated} updated, {result.rows_skipped} skipped"
            )

        return jsonify(
            {
                "success": result.success,
                "result": result.to_dict(),
            }
        ), 200 if result.success else 500

    except Exception as e:
        logger.exception("Reverse sync execution failed")
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500


@reverse_sync_api_bp.route("/tables", methods=["GET"])
def api_list_tables() -> Response | tuple[Response, int]:
    """List available database tables for reverse sync.

    Returns:
        JSON response with list of table names.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    try:
        config = get_config()
        from mysql_to_sheets.core.database import DatabaseConfig, get_connection

        db_config = DatabaseConfig(
            db_type=config.db_type,
            host=config.db_host,
            port=config.db_port,
            user=config.db_user,
            password=config.db_password,
            database=config.db_name,
            connect_timeout=config.db_connect_timeout,
        )

        with get_connection(db_config) as conn:
            tables = conn.list_tables()  # type: ignore[attr-defined]

        return jsonify(
            {
                "success": True,
                "tables": tables,
                "db_type": config.db_type,
                "database": config.db_name,
            }
        ), 200

    except Exception as e:
        logger.exception("Failed to list tables")
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500


@reverse_sync_api_bp.route("/table/<table_name>/columns", methods=["GET"])
def api_table_columns(table_name: str) -> Response | tuple[Response, int]:
    """Get column information for a specific table.

    Args:
        table_name: Name of the table to inspect.

    Returns:
        JSON response with column details.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    try:
        config = get_config()
        from mysql_to_sheets.core.database import DatabaseConfig, get_connection

        db_config = DatabaseConfig(
            db_type=config.db_type,
            host=config.db_host,
            port=config.db_port,
            user=config.db_user,
            password=config.db_password,
            database=config.db_name,
            connect_timeout=config.db_connect_timeout,
        )

        with get_connection(db_config) as conn:
            columns = conn.get_table_columns(table_name)  # type: ignore[attr-defined]

        return jsonify(
            {
                "success": True,
                "table": table_name,
                "columns": columns,
            }
        ), 200

    except Exception as e:
        logger.exception(f"Failed to get columns for table {table_name}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
            }
        ), 500
