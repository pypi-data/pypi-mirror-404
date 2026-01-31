"""Sync API blueprint for web dashboard.

Handles sync and validate endpoints via AJAX.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, Response, jsonify, request

from mysql_to_sheets.core.config import get_config, reset_config
from mysql_to_sheets.core.exceptions import ConfigError, DatabaseError, SheetsError
from mysql_to_sheets.core.sync import run_sync
from mysql_to_sheets.web.history import SyncHistoryEntry, sync_history

logger = logging.getLogger("mysql_to_sheets.web.api.sync")

sync_api_bp = Blueprint("sync_api", __name__, url_prefix="/api")


@sync_api_bp.route("/health", methods=["GET"])
def api_health() -> tuple[Response, int]:
    """Health check endpoint.

    Returns:
        JSON response with health status.
    """
    from mysql_to_sheets import __version__

    return jsonify(
        {
            "status": "healthy",
            "version": __version__,
        }
    ), 200


@sync_api_bp.route("/setup/status", methods=["GET"])
def api_setup_status() -> tuple[Response, int]:
    """Get setup status.

    Returns:
        JSON response with setup status.
    """
    from mysql_to_sheets.core.paths import (
        get_default_env_path,
        get_default_service_account_path,
    )

    env_path = get_default_env_path()
    service_account_path = get_default_service_account_path()

    env_exists = env_path.exists()
    service_account_exists = service_account_path.exists()

    # Check if .env has been configured
    env_configured = False
    if env_exists:
        content = env_path.read_text()
        env_configured = (
            "your_password" not in content and "your_spreadsheet_id_here" not in content
        )

    return jsonify(
        {
            "env_exists": env_exists,
            "env_configured": env_configured,
            "service_account_exists": service_account_exists,
            "setup_complete": env_configured and service_account_exists,
        }
    ), 200


@sync_api_bp.route("/sync", methods=["POST"])
def api_sync() -> tuple[Response, int]:
    """Execute sync from MySQL to Google Sheets.

    Accepts JSON body with optional overrides:
    - sheet_id: Google Sheet ID
    - worksheet: Worksheet name
    - sql_query: SQL query to execute
    - dry_run: If true, validate only
    - preview: If true, show diff without pushing

    Returns:
        JSON response with sync result.
    """
    data = request.get_json() or {}

    try:
        # Load fresh config
        reset_config()
        config = get_config()

        # Apply overrides from request
        overrides = {}
        if data.get("sheet_id"):
            from mysql_to_sheets.core.sheets_utils import parse_sheet_id

            try:
                overrides["google_sheet_id"] = parse_sheet_id(data["sheet_id"])
            except ValueError as e:
                return jsonify(
                    {
                        "success": False,
                        "error": str(e),
                        "message": str(e),
                        "error_type": "ValidationError",
                    }
                ), 400
        if data.get("worksheet"):
            overrides["google_worksheet_name"] = data["worksheet"]
        if data.get("sql_query"):
            overrides["sql_query"] = data["sql_query"]

        # Handle mode and chunk_size overrides
        if data.get("mode"):
            overrides["sync_mode"] = data["mode"]
        if data.get("chunk_size"):
            overrides["sync_chunk_size"] = data["chunk_size"]

        if overrides:
            config = config.with_overrides(**overrides)

        # Track timing
        start_time = time.time()

        # Execute sync with atomic streaming options
        dry_run = data.get("dry_run", False)
        preview = data.get("preview", False)
        atomic = data.get("atomic", True)  # Default to atomic mode
        preserve_gid = data.get("preserve_gid", False)

        result = run_sync(
            config,
            dry_run=dry_run,
            preview=preview,
            atomic=atomic,
            preserve_gid=preserve_gid,
        )

        duration_ms = (time.time() - start_time) * 1000

        # Add to history
        sync_history.add(
            SyncHistoryEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=result.success,
                rows_synced=result.rows_synced,
                message=result.message or ("Dry run" if dry_run else ""),
                sheet_id=config.google_sheet_id,
                worksheet=config.google_worksheet_name,
                duration_ms=duration_ms,
            )
        )

        # Build response - ensure message is never None for failures
        message = result.message
        if not result.success and not message:
            message = result.error or "Sync failed"

        response = {
            "success": result.success,
            "rows_synced": result.rows_synced,
            "columns": result.columns,
            "headers": result.headers,
            "message": message,
            "error": result.error,
            "preview": result.preview,
            "dry_run": dry_run,
        }

        # Include diff info if preview mode
        if result.diff:
            response["diff"] = {
                "has_changes": result.diff.has_changes,
                "sheet_row_count": result.diff.sheet_row_count,
                "query_row_count": result.diff.query_row_count,
                "rows_to_add": result.diff.rows_to_add,
                "rows_to_remove": result.diff.rows_to_remove,
                "rows_unchanged": result.diff.rows_unchanged,
                "summary": result.diff.summary(),
            }

        return jsonify(response), 200

    except ConfigError as e:
        logger.error(f"Config error: {e.message}")
        return jsonify(
            {
                "success": False,
                "error": e.message,
                "message": e.message,
                "errors": e.details.get("missing_fields", []),
                "error_type": "ConfigError",
                "code": e.code,
                "category": e.category.value if e.category else None,
                "remediation": e.remediation,
            }
        ), 400
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        # Add to history for failed sync
        sync_history.add(
            SyncHistoryEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=False,
                rows_synced=0,
                message=f"Database error: {e.message}",
                sheet_id=config.google_sheet_id,
                worksheet=config.google_worksheet_name,
                duration_ms=0,
                error_code=e.code,
                error_category=e.category.value if e.category else None,
            )
        )
        return jsonify(
            {
                "success": False,
                "error": e.message,
                "message": e.message,
                "error_type": "DatabaseError",
                "code": e.code,
                "category": e.category.value if e.category else None,
                "remediation": e.remediation,
            }
        ), 500
    except SheetsError as e:
        logger.error(f"Sheets error: {e.message}")
        # Add to history for failed sync
        sync_history.add(
            SyncHistoryEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=False,
                rows_synced=0,
                message=f"Sheets error: {e.message}",
                sheet_id=config.google_sheet_id,
                worksheet=config.google_worksheet_name,
                duration_ms=0,
                error_code=e.code,
                error_category=e.category.value if e.category else None,
            )
        )
        return jsonify(
            {
                "success": False,
                "error": e.message,
                "message": e.message,
                "error_type": "SheetsError",
                "code": e.code,
                "category": e.category.value if e.category else None,
                "remediation": e.remediation,
            }
        ), 500
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
                "error_type": "UnexpectedError",
            }
        ), 500


@sync_api_bp.route("/validate", methods=["POST"])
def api_validate() -> tuple[Response, int]:
    """Validate sync configuration.

    Accepts JSON body with optional overrides:
    - sheet_id: Google Sheet ID
    - worksheet: Worksheet name
    - sql_query: SQL query to execute
    - test_connections: If true, test DB and Sheets connections

    Returns:
        JSON response with validation result.
    """
    data = request.get_json() or {}

    try:
        # Load fresh config
        reset_config()
        config = get_config()

        # Apply overrides from request
        overrides = {}
        if data.get("sheet_id"):
            from mysql_to_sheets.core.sheets_utils import parse_sheet_id

            try:
                overrides["google_sheet_id"] = parse_sheet_id(data["sheet_id"])
            except ValueError as e:
                return jsonify(
                    {
                        "valid": False,
                        "error": str(e),
                        "message": str(e),
                        "errors": [str(e)],
                    }
                ), 400
        if data.get("worksheet"):
            overrides["google_worksheet_name"] = data["worksheet"]
        if data.get("sql_query"):
            overrides["sql_query"] = data["sql_query"]

        if overrides:
            config = config.with_overrides(**overrides)

        # Validate config
        errors = config.validate()
        valid = len(errors) == 0

        response: dict[str, Any] = {
            "valid": valid,
            "errors": errors,
            "database_ok": None,
            "sheets_ok": None,
        }

        # Optionally test connections
        if data.get("test_connections") and valid:
            from mysql_to_sheets.core.sync import SyncService

            service = SyncService(config)

            try:
                service.test_database_connection()
                response["database_ok"] = True
            except DatabaseError as e:
                response["database_ok"] = False
                response["valid"] = False
                response["errors"].append(f"Database: {e.message}")

            try:
                service.test_sheets_connection()
                response["sheets_ok"] = True
            except SheetsError as e:
                response["sheets_ok"] = False
                response["valid"] = False
                response["errors"].append(f"Sheets: {e.message}")

        status_code = 200 if response["valid"] else 400
        return jsonify(response), status_code

    except Exception as e:
        logger.exception(f"Validation error: {e}")
        return jsonify(
            {
                "valid": False,
                "error": str(e),
                "message": str(e),
                "errors": [str(e)],
            }
        ), 500


@sync_api_bp.route("/history", methods=["GET"])
def api_history() -> tuple[Response, int]:
    """Get sync history.

    Returns:
        JSON response with history entries.
    """
    return jsonify(
        {
            "history": sync_history.get_all(),
            "total": sync_history.count(),
        }
    ), 200
