"""Diagnostics blueprint for Flask web dashboard.

Provides system health checks, connectivity tests, and troubleshooting tools.
"""

import logging
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Blueprint, Response, jsonify, render_template

from mysql_to_sheets import __version__
from mysql_to_sheets.core.config import get_config, reset_config
from mysql_to_sheets.core.paths import (
    get_config_dir,
    get_data_dir,
    get_default_env_path,
    get_default_service_account_path,
    get_logs_dir,
)

logger = logging.getLogger("mysql_to_sheets.web.diagnostics")

diagnostics_bp = Blueprint("diagnostics", __name__)


@diagnostics_bp.route("/diagnostics")
def diagnostics_page() -> str:
    """Render the diagnostics page.

    Shows system health, connectivity tests, and environment validation.

    Returns:
        Rendered HTML template.
    """
    # Get system info
    system_info = _get_system_info()

    # Get environment info
    env_info = _get_environment_info()

    # Get paths info
    paths_info = _get_paths_info()

    return render_template(
        "diagnostics.html",
        version=__version__,
        system_info=system_info,
        env_info=env_info,
        paths_info=paths_info,
    )


def _get_system_info() -> dict[str, Any]:
    """Get system information.

    Returns:
        Dictionary with system details.
    """
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "Unknown",
        "app_version": __version__,
    }


def _get_environment_info() -> dict[str, Any]:
    """Get environment configuration status.

    Returns:
        Dictionary with environment details.
    """
    env_path = get_default_env_path()
    service_account_path = get_default_service_account_path()

    env_exists = env_path.exists()
    service_account_exists = service_account_path.exists()

    # Check key environment variables (without exposing values)
    env_vars = {
        "DB_HOST": bool(os.getenv("DB_HOST")),
        "DB_USER": bool(os.getenv("DB_USER")),
        "DB_PASSWORD": bool(os.getenv("DB_PASSWORD")),
        "DB_NAME": bool(os.getenv("DB_NAME")),
        "GOOGLE_SHEET_ID": bool(os.getenv("GOOGLE_SHEET_ID")),
        "SQL_QUERY": bool(os.getenv("SQL_QUERY")),
        "SERVICE_ACCOUNT_FILE": bool(os.getenv("SERVICE_ACCOUNT_FILE")),
    }

    return {
        "env_file_exists": env_exists,
        "env_file_path": str(env_path),
        "service_account_exists": service_account_exists,
        "service_account_path": str(service_account_path),
        "env_vars_set": env_vars,
        "all_required_set": all(
            [
                env_vars["DB_HOST"] or env_vars["DB_NAME"],
                env_vars["GOOGLE_SHEET_ID"],
                env_vars["SQL_QUERY"],
            ]
        ),
    }


def _get_paths_info() -> dict[str, Any]:
    """Get application paths information.

    Returns:
        Dictionary with path details.
    """
    config_dir = get_config_dir()
    data_dir = get_data_dir()
    logs_dir = get_logs_dir()

    return {
        "config_dir": str(config_dir),
        "config_dir_exists": config_dir.exists(),
        "data_dir": str(data_dir),
        "data_dir_exists": data_dir.exists(),
        "logs_dir": str(logs_dir),
        "logs_dir_exists": logs_dir.exists(),
        "working_dir": os.getcwd(),
    }


# API endpoints for diagnostics
diagnostics_api_bp = Blueprint("diagnostics_api", __name__, url_prefix="/api/diagnostics")


@diagnostics_api_bp.route("", methods=["GET"])
def api_run_diagnostics() -> tuple[Response, int]:
    """Run full diagnostics and return results.

    Returns:
        JSON response with diagnostic results.
    """
    results: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "system": _get_system_info(),
        "environment": _get_environment_info(),
        "paths": _get_paths_info(),
        "checks": {},
    }

    # Run individual checks
    results["checks"]["config"] = _check_config()
    results["checks"]["dependencies"] = _check_dependencies()

    # Calculate overall status
    all_checks = results["checks"].values()
    results["overall_status"] = (
        "healthy" if all(c.get("status") == "ok" for c in all_checks) else "issues_found"
    )

    return jsonify(results), 200


@diagnostics_api_bp.route("/db", methods=["POST"])
def api_test_database() -> tuple[Response, int]:
    """Test database connectivity.

    Returns:
        JSON response with database test results.
    """
    reset_config()
    config = get_config()

    result: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db_type": config.db_type,
        "db_host": config.db_host,
        "db_name": config.db_name,
        "status": "unknown",
        "message": "",
        "details": {},
    }

    try:
        from mysql_to_sheets.core.database import get_connection

        conn = get_connection(config)  # type: ignore[arg-type]
        # Test with a simple query
        if config.db_type == "sqlite":
            test_query = "SELECT sqlite_version()"
        elif config.db_type == "postgres":
            test_query = "SELECT version()"
        elif config.db_type == "mssql":
            test_query = "SELECT @@VERSION"
        else:
            test_query = "SELECT VERSION()"

        with conn.get_cursor() as cursor:  # type: ignore[attr-defined]
            cursor.execute(test_query)
            version_row = cursor.fetchone()
            db_version = version_row[0] if version_row else "Unknown"

        result["status"] = "ok"
        result["message"] = "Database connection successful"
        result["details"]["server_version"] = (
            db_version[:100] if len(db_version) > 100 else db_version
        )

    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
        result["details"]["error_type"] = type(e).__name__

        # Add remediation hints
        error_str = str(e).lower()
        if "connection refused" in error_str:
            result["remediation"] = (
                "Check that the database server is running and accepting connections"
            )
        elif "authentication" in error_str or "access denied" in error_str:
            result["remediation"] = "Verify DB_USER and DB_PASSWORD in your .env file"
        elif "unknown database" in error_str or "does not exist" in error_str:
            result["remediation"] = "Check that DB_NAME exists on the server"
        else:
            result["remediation"] = "Check database configuration in .env file"

    return jsonify(result), 200


@diagnostics_api_bp.route("/sheets", methods=["POST"])
def api_test_sheets() -> tuple[Response, int]:
    """Test Google Sheets connectivity.

    Returns:
        JSON response with Sheets test results.
    """
    reset_config()
    config = get_config()

    result: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sheet_id": config.google_sheet_id[:20] + "..."
        if len(config.google_sheet_id) > 20
        else config.google_sheet_id,
        "worksheet": config.google_worksheet_name,
        "status": "unknown",
        "message": "",
        "details": {},
    }

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        # Check service account file
        sa_path = Path(config.service_account_file)
        if not sa_path.exists():
            raise FileNotFoundError(f"Service account file not found: {sa_path}")

        # Load credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        creds = Credentials.from_service_account_file(str(sa_path), scopes=scopes)  # type: ignore[no-untyped-call]

        # Connect to Google Sheets
        client = gspread.authorize(creds)  # type: ignore[attr-defined]

        # Try to open the spreadsheet
        spreadsheet = client.open_by_key(config.google_sheet_id)

        result["status"] = "ok"
        result["message"] = "Google Sheets connection successful"
        result["details"]["spreadsheet_title"] = spreadsheet.title
        result["details"]["worksheet_count"] = len(spreadsheet.worksheets())
        result["details"]["service_account_email"] = creds.service_account_email

    except FileNotFoundError as e:
        result["status"] = "error"
        result["message"] = str(e)
        result["remediation"] = "Download your service account JSON from Google Cloud Console"

    except gspread.exceptions.SpreadsheetNotFound:
        result["status"] = "error"
        result["message"] = "Spreadsheet not found"
        result["remediation"] = (
            "Check GOOGLE_SHEET_ID and ensure the sheet is shared with your service account email"
        )

    except gspread.exceptions.APIError as e:
        result["status"] = "error"
        result["message"] = f"Google Sheets API error: {e}"
        if "403" in str(e):
            result["remediation"] = "Share the spreadsheet with your service account email"
        else:
            result["remediation"] = "Check Google Sheets API quota and try again"

    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
        result["details"]["error_type"] = type(e).__name__
        result["remediation"] = "Check service account configuration"

    return jsonify(result), 200


@diagnostics_api_bp.route("/config", methods=["GET"])
def api_check_config() -> tuple[Response, int]:
    """Check configuration validity.

    Returns:
        JSON response with config check results.
    """
    result = _check_config()
    return jsonify(result), 200


@diagnostics_api_bp.route("/export", methods=["GET"])
def api_export_diagnostics() -> tuple[Response, int]:
    """Export full diagnostics report.

    Returns:
        JSON response with complete diagnostic report.
    """
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "system": _get_system_info(),
        "environment": _get_environment_info(),
        "paths": _get_paths_info(),
        "checks": {
            "config": _check_config(),
            "dependencies": _check_dependencies(),
        },
    }

    return jsonify(report), 200


def _check_config() -> dict[str, Any]:
    """Check configuration validity.

    Returns:
        Dictionary with config check results.
    """
    result: dict[str, Any] = {
        "status": "unknown",
        "errors": [],
        "warnings": [],
    }

    try:
        reset_config()
        config = get_config()

        # Check required fields
        if not config.db_name:
            result["errors"].append("DB_NAME is not set")

        if not config.google_sheet_id:
            result["errors"].append("GOOGLE_SHEET_ID is not set")

        if not config.sql_query:
            result["errors"].append("SQL_QUERY is not set")

        # Check service account file
        sa_path = Path(config.service_account_file)
        if not sa_path.exists():
            result["errors"].append(f"Service account file not found: {sa_path}")

        # Warnings
        if config.db_type not in ("mysql", "postgres", "sqlite", "mssql"):
            result["warnings"].append(f"Unusual database type: {config.db_type}")

        if not os.getenv("SESSION_SECRET_KEY"):
            result["warnings"].append("SESSION_SECRET_KEY not set (using default for dev)")

        result["status"] = "ok" if not result["errors"] else "error"

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Config loading failed: {e}")

    return result


def _check_dependencies() -> dict[str, Any]:
    """Check Python dependencies.

    Returns:
        Dictionary with dependency check results.
    """
    result: dict[str, Any] = {
        "status": "ok",
        "packages": {},
        "missing": [],
    }

    packages_to_check = [
        "gspread",
        "google.auth",
        "mysql.connector",
        "psycopg2",
        "flask",
        "flask_wtf",
        "sqlalchemy",
        "dotenv",
    ]

    for package in packages_to_check:
        try:
            if package == "dotenv":
                import dotenv

                version = getattr(dotenv, "__version__", "installed")
            elif package == "google.auth":
                import google.auth

                version = getattr(google.auth, "__version__", "installed")
            elif package == "mysql.connector":
                import mysql.connector

                version = mysql.connector.__version__
            else:
                module = __import__(package)
                version = getattr(module, "__version__", "installed")
            result["packages"][package] = {"installed": True, "version": version}
        except ImportError:
            result["packages"][package] = {"installed": False}
            # Only mark as missing if it's a core dependency
            if package in ("gspread", "google.auth", "flask", "sqlalchemy"):
                result["missing"].append(package)

    if result["missing"]:
        result["status"] = "error"

    return result
