"""Dashboard blueprint for Flask web dashboard.

Handles main dashboard pages: index, setup, schedules, users, configs, webhooks, favorites.
Also includes setup wizard API endpoints for interactive first-time configuration.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from flask import Blueprint, Response, jsonify, redirect, render_template, request, session, url_for

from mysql_to_sheets import __version__
from mysql_to_sheets.core.config import get_config, reset_config
from mysql_to_sheets.core.paths import (
    get_config_dir,
    get_default_env_path,
    get_default_service_account_path,
)
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.web.context import get_current_user
from mysql_to_sheets.web.decorators import login_required
from mysql_to_sheets.web.history import sync_history

logger = logging.getLogger("mysql_to_sheets.web.dashboard")

dashboard_bp = Blueprint("dashboard", __name__)


def _validate_port(value: Any, default: int = 3306) -> tuple[int | None, str | None]:
    """Validate and parse a port number.

    EC-55: Dashboard port validation to prevent crashes from invalid values.

    Args:
        value: Port value from form (str, int, or None).
        default: Default port if value is None or empty.

    Returns:
        Tuple of (port_number, error_message).
        On success: (port_number, None)
        On failure: (None, error_message)
    """
    if value is None or value == "":
        return default, None
    try:
        port = int(value)
    except (ValueError, TypeError):
        return None, f"Invalid port '{value}': must be a number"
    if port < 1 or port > 65535:
        return None, f"Port {port} out of range (must be 1-65535)"
    return port, None


@dashboard_bp.route("/")
@login_required
def index() -> str:
    """Render the main dashboard page.

    Returns:
        Rendered HTML template.
    """
    # Load current config for defaults
    reset_config()
    config = get_config()

    return render_template(
        "index.html",
        version=__version__,
        config={
            "sheet_id": config.google_sheet_id,
            "worksheet": config.google_worksheet_name,
            "sql_query": config.sql_query,
            "db_type": config.db_type,
            "db_host": config.db_host,
            "db_name": config.db_name,
            "service_account_file": config.service_account_file,
        },
        history=sync_history.get_all(),
    )


@dashboard_bp.route("/history")
@login_required
def history_page() -> str:
    """Render the sync history page with pagination.

    Returns:
        Rendered HTML template.
    """
    page_size = 20
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    all_history = sync_history.get_all()
    total = len(all_history)
    total_pages = max(1, (total + page_size - 1) // page_size)

    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size

    return render_template(
        "history.html",
        version=__version__,
        history=all_history[start:end],
        page=page,
        total=total,
        total_pages=total_pages,
    )


@dashboard_bp.route("/dismiss-banner", methods=["POST"])
def dismiss_banner() -> Any:
    """Dismiss the first-run credentials banner.

    Returns:
        Redirect to dashboard.
    """
    session.pop("_first_run", None)
    return redirect(url_for("dashboard.index"))


@dashboard_bp.route("/setup")
def setup() -> Any:
    """Render the first-run setup wizard.

    Returns:
        Rendered setup HTML template or redirect to dashboard.
    """
    # Check configuration status
    env_path = get_default_env_path()
    service_account_path = get_default_service_account_path()
    config_dir = get_config_dir()

    env_exists = env_path.exists()
    service_account_exists = service_account_path.exists()

    # Check if .env has been configured (not just copied)
    env_configured = False
    if env_exists:
        content = env_path.read_text()
        # Check if required fields have been filled in
        env_configured = (
            "your_password" not in content and "your_spreadsheet_id_here" not in content
        )

    return render_template(
        "setup.html",
        version=__version__,
        config_dir=str(config_dir),
        env_path=str(env_path),
        service_account_path=str(service_account_path),
        env_exists=env_exists,
        env_configured=env_configured,
        service_account_exists=service_account_exists,
        setup_complete=env_configured and service_account_exists,
    )


@dashboard_bp.route("/schedules")
def schedules() -> str:
    """Render the schedule management page.

    Returns:
        Rendered HTML template.
    """
    from mysql_to_sheets.core.scheduler import get_scheduler_service

    service = get_scheduler_service()
    jobs = service.get_all_jobs(include_disabled=True)
    status = service.get_status()

    return render_template(
        "schedules.html",
        version=__version__,
        jobs=[j.to_dict() for j in jobs],
        scheduler_status=status,
    )


@dashboard_bp.route("/users")
@login_required
def users() -> Any:
    """Render the user management page.

    Returns:
        Rendered HTML template.
    """
    from mysql_to_sheets.models.users import get_user_repository

    current = get_current_user()
    if not current:
        return redirect(url_for("auth.login"))

    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    # Get all users for the current organization
    users_list = user_repo.get_all(current["organization_id"])

    return render_template(
        "users.html",
        version=__version__,
        users=[u.to_dict() for u in users_list],
    )


@dashboard_bp.route("/configs")
@login_required
def configs_page() -> Any:
    """Render the sync configs management page.

    Returns:
        Rendered HTML template.
    """
    from mysql_to_sheets.models.sync_configs import get_sync_config_repository

    current = get_current_user()
    if not current:
        return redirect(url_for("auth.login"))

    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    configs_list = config_repo.get_all(current["organization_id"])
    return render_template(
        "configs.html",
        version=__version__,
        configs=[c.to_dict() for c in configs_list],
    )


@dashboard_bp.route("/webhooks")
@login_required
def webhooks_page() -> Any:
    """Render the webhooks management page.

    Returns:
        Rendered HTML template.
    """
    from mysql_to_sheets.models.webhooks import get_webhook_repository

    current = get_current_user()
    if not current:
        return redirect(url_for("auth.login"))

    # Check permission (admin+ only)
    if current["role"] not in ("owner", "admin"):
        return render_template(
            "error.html",
            version=__version__,
            error="Access Denied",
            message="You do not have permission to access this page.",
        ), 403

    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhooks_list = webhook_repo.get_all_subscriptions(current["organization_id"])
    return render_template(
        "webhooks.html",
        version=__version__,
        webhooks=[w.to_dict() for w in webhooks_list],
    )


@dashboard_bp.route("/audit")
@login_required
def audit_page() -> Any:
    """Render the audit logs page.

    Returns:
        Rendered HTML template.
    """
    current = get_current_user()
    if not current:
        return redirect(url_for("auth.login"))

    # Check permission (admin+ only)
    if current["role"] not in ("owner", "admin"):
        return render_template(
            "error.html",
            version=__version__,
            error="Access Denied",
            message="You do not have permission to access this page.",
        ), 403

    return render_template(
        "audit.html",
        version=__version__,
    )


@dashboard_bp.route("/jobs")
@login_required
def jobs_page() -> str:
    """Render the job queue page.

    Returns:
        Rendered HTML template.
    """
    return render_template(
        "jobs.html",
        version=__version__,
    )


@dashboard_bp.route("/snapshots")
@login_required
def snapshots_page() -> str:
    """Render the snapshots and rollback page.

    Returns:
        Rendered HTML template.
    """
    return render_template(
        "snapshots.html",
        version=__version__,
    )


@dashboard_bp.route("/favorites")
@login_required
def favorites_page() -> Any:
    """Render the favorites management page.

    Shows saved queries and sheets with CRUD operations.

    Returns:
        Rendered HTML template.
    """
    from mysql_to_sheets.models.favorites import (
        get_favorite_query_repository,
        get_favorite_sheet_repository,
    )

    current = get_current_user()
    if not current:
        return redirect(url_for("auth.login"))

    db_path = get_tenant_db_path()
    query_repo = get_favorite_query_repository(db_path)
    sheet_repo = get_favorite_sheet_repository(db_path)

    queries = query_repo.get_all(        organization_id=current["organization_id"],
        user_id=current["id"],
    )
    sheets = sheet_repo.get_all(        organization_id=current["organization_id"],
        user_id=current["id"],
    )

    return render_template(
        "favorites.html",
        version=__version__,
        queries=[q.to_dict() for q in queries],
        sheets=[s.to_dict() for s in sheets],
    )


@dashboard_bp.route("/worksheets")
def worksheets_page() -> str:
    """Render the worksheets management page.

    Allows users to list, create, and delete worksheets within a Google Spreadsheet.
    No authentication required - accessible like the main dashboard.

    Returns:
        Rendered HTML template.
    """
    reset_config()
    config = get_config()

    return render_template(
        "worksheets.html",
        version=__version__,
        sheet_id=config.google_sheet_id,
        default_rows=config.worksheet_default_rows,
        default_cols=config.worksheet_default_cols,
    )


# =============================================================================
# Setup Wizard API Endpoints
# =============================================================================


@dashboard_bp.route("/api/setup/status")
def api_setup_status() -> Response:
    """Get setup status for wizard.

    Returns:
        JSON response with setup status.
    """
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
    )


@dashboard_bp.route("/api/setup/test-db", methods=["POST"])
def api_setup_test_db() -> Response:
    """Test database connection with provided credentials.

    Returns:
        JSON response with connection status.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})

        db_type = data.get("db_type", "mysql")

        # Import database module
        from mysql_to_sheets.core.database import get_connection

        if db_type == "sqlite":
            db_name = data.get("db_name", "")
            if not db_name:
                return jsonify({"success": False, "message": "Database path required"})
            if not Path(db_name).exists():
                return jsonify(
                    {
                        "success": False,
                        "message": f"Database file not found: {db_name}",
                        "remediation": "Check the file path exists and is readable",
                    }
                )

            conn = get_connection(db_type=db_type, db_name=db_name)  # type: ignore[call-arg]
        else:
            # EC-55: Validate port before conversion
            port, port_error = _validate_port(data.get("db_port"), default=3306)
            if port_error:
                return jsonify({"success": False, "message": port_error})

            conn = get_connection(  # type: ignore[call-arg]
                db_type=db_type,
                host=data.get("db_host", "localhost"),
                port=port,
                user=data.get("db_user", ""),
                password=data.get("db_password", ""),
                database=data.get("db_name", ""),
            )

        # Test connection
        with conn:
            conn.execute("SELECT 1")

        return jsonify({"success": True, "message": "Connection successful!"})

    except Exception as e:
        error_msg = str(e)
        remediation = _get_db_error_remediation(error_msg)
        return jsonify(
            {
                "success": False,
                "message": error_msg,
                "remediation": remediation,
            }
        )


@dashboard_bp.route("/api/setup/test-sheets", methods=["POST"])
def api_setup_test_sheets() -> Response:
    """Test Google Sheets access with provided credentials.

    Returns:
        JSON response with connection status.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})

        service_account = data.get("service_account")
        sheet_id = data.get("sheet_id", "")
        worksheet = data.get("worksheet", "Sheet1")

        if not service_account:
            return jsonify(
                {
                    "success": False,
                    "message": "Service account credentials required",
                }
            )

        if not sheet_id:
            return jsonify(
                {
                    "success": False,
                    "message": "Sheet ID required",
                }
            )

        # Extract sheet ID from URL if necessary
        if "docs.google.com" in sheet_id:
            match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_id)
            if match:
                sheet_id = match.group(1)

        # Import Google libraries
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ]

        creds = Credentials.from_service_account_info(service_account, scopes=scopes)  # type: ignore[no-untyped-call]
        client = gspread.authorize(creds)  # type: ignore[attr-defined]

        spreadsheet = client.open_by_key(sheet_id)

        return jsonify(
            {
                "success": True,
                "message": "Sheet access verified!",
                "sheet_title": spreadsheet.title,
            }
        )

    except Exception as e:
        error_msg = str(e)
        remediation = _get_sheets_error_remediation(error_msg)
        return jsonify(
            {
                "success": False,
                "message": error_msg,
                "remediation": remediation,
            }
        )


@dashboard_bp.route("/api/setup/preview-query", methods=["POST"])
def api_setup_preview_query() -> Response:
    """Preview SQL query results.

    Returns:
        JSON response with query preview.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})

        sql_query = data.get("sql_query", "")
        if not sql_query:
            return jsonify({"success": False, "message": "SQL query required"})

        db_type = data.get("db_type", "mysql")

        from mysql_to_sheets.core.database import get_connection
        from mysql_to_sheets.core.database.base import DatabaseConfig

        if db_type == "sqlite":
            db_config = DatabaseConfig(
                db_type=db_type,
                database=data.get("db_name", ""),
            )
        else:
            # EC-55: Validate port before conversion
            port, port_error = _validate_port(data.get("db_port"), default=3306)
            if port_error:
                return jsonify({"success": False, "message": port_error})

            db_config = DatabaseConfig(
                db_type=db_type,
                host=data.get("db_host", "localhost"),
                port=port,
                user=data.get("db_user", ""),
                password=data.get("db_password", ""),
                database=data.get("db_name", ""),
            )

        conn = get_connection(db_config)

        with conn:
            result = conn.execute(sql_query)

        # FetchResult is a dataclass with headers and rows attributes
        headers = result.headers
        rows = result.rows

        # Limit preview to first 10 rows
        preview_rows = rows[:10]

        return jsonify(
            {
                "success": True,
                "row_count": len(rows),
                "headers": headers,
                "preview_rows": preview_rows,
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": str(e),
            }
        )


@dashboard_bp.route("/api/setup/run-sync", methods=["POST"])
def api_setup_run_sync() -> Response:
    """Run sync with provided configuration.

    Returns:
        JSON response with sync result.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})

        # Build config
        from mysql_to_sheets.core.config import Config
        from mysql_to_sheets.core.sync import run_sync as core_run_sync

        # Write service account to temp file
        service_account = data.get("service_account")
        temp_sa_path = None

        if service_account:
            import tempfile

            temp_sa_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            json.dump(service_account, temp_sa_file)
            temp_sa_file.close()
            temp_sa_path = temp_sa_file.name

        try:
            # Extract sheet ID from URL
            sheet_id = data.get("sheet_id", "")
            if "docs.google.com" in sheet_id:
                match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_id)
                if match:
                    sheet_id = match.group(1)

            # EC-55: Validate port before conversion
            port, port_error = _validate_port(data.get("db_port"), default=3306)
            if port_error:
                return jsonify({"success": False, "message": port_error})

            sync_config = Config(
                db_type=data.get("db_type", "mysql"),
                db_host=data.get("db_host", "localhost"),
                db_port=port,
                db_user=data.get("db_user", ""),
                db_password=data.get("db_password", ""),
                db_name=data.get("db_name", ""),
                google_sheet_id=sheet_id,
                google_worksheet_name=data.get("worksheet", "Sheet1"),
                service_account_file=str(temp_sa_path or get_default_service_account_path()),
                sql_query=data.get("sql_query", ""),
            )

            result = core_run_sync(sync_config)

            if result.success:
                return jsonify(
                    {
                        "success": True,
                        "rows_synced": result.rows_synced,
                        "message": "Sync completed successfully!",
                    }
                )
            else:
                return jsonify(
                    {
                        "success": False,
                        "message": result.error or "Sync failed",
                        "remediation": result.remediation
                        if hasattr(result, "remediation")
                        else None,
                    }
                )

        finally:
            # Clean up temp file
            if temp_sa_path and Path(temp_sa_path).exists():
                os.unlink(temp_sa_path)

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": str(e),
            }
        )


@dashboard_bp.route("/api/setup/save-config", methods=["POST"])
def api_setup_save_config() -> Response:
    """Save configuration to .env file.

    Returns:
        JSON response with save status.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})

        env_path = get_default_env_path()

        lines = []
        lines.append("# Generated by MySQL to Sheets setup wizard")
        lines.append("")
        lines.append("# Database")

        for key, value in data.items():
            if value is not None:
                lines.append(f"{key}={value}")

        # Add defaults
        if "LOG_LEVEL" not in data:
            lines.append("")
            lines.append("# Logging")
            lines.append("LOG_LEVEL=INFO")

        with open(env_path, "w") as f:
            f.write("\n".join(lines))
            f.write("\n")

        return jsonify(
            {
                "success": True,
                "message": f"Configuration saved to {env_path}",
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": str(e),
            }
        )


@dashboard_bp.route("/api/setup/parse-uri", methods=["POST"])
def api_setup_parse_uri() -> Response:
    """Parse a database connection URI into components.

    Returns:
        JSON response with parsed connection details.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})

        uri = data.get("uri", "")
        if not uri:
            return jsonify({"success": False, "message": "Connection URI required"})

        from mysql_to_sheets.core.config import parse_database_uri

        parsed = parse_database_uri(uri)

        return jsonify(
            {
                "success": True,
                "db_type": parsed["db_type"],
                "db_host": parsed["db_host"],
                "db_port": parsed["db_port"],
                "db_user": parsed["db_user"],
                "db_password": parsed["db_password"],
                "db_name": parsed["db_name"],
            }
        )

    except ValueError as e:
        return jsonify(
            {
                "success": False,
                "message": str(e),
            }
        )
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": f"Failed to parse URI: {e}",
            }
        )


@dashboard_bp.route("/api/setup/demo", methods=["POST"])
def api_setup_demo() -> Response:
    """Set up demo database for evaluation.

    Returns:
        JSON response with demo database configuration.
    """
    try:
        from mysql_to_sheets.core.demo import (
            create_demo_database,
            get_demo_queries,
        )

        db_path = create_demo_database()

        return jsonify(
            {
                "success": True,
                "message": "Demo database created successfully",
                "db_type": "sqlite",
                "db_name": str(db_path),
                "suggested_queries": get_demo_queries(),
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": f"Failed to create demo database: {e}",
            }
        )


@dashboard_bp.route("/api/setup/schema/tables", methods=["GET"])
def api_schema_tables() -> Response:
    """List all tables in the connected database.

    Returns:
        JSON response with list of tables and row counts.
    """
    try:
        db_type = request.args.get("db_type") or os.getenv("DB_TYPE", "mysql")
        db_host = request.args.get("db_host") or os.getenv("DB_HOST", "localhost")
        db_port = request.args.get("db_port") or os.getenv("DB_PORT")
        db_user = request.args.get("db_user") or os.getenv("DB_USER")
        db_password = request.args.get("db_password") or os.getenv("DB_PASSWORD")
        db_name = request.args.get("db_name") or os.getenv("DB_NAME")

        if not db_name:
            return jsonify({"success": False, "message": "Database name is required"})

        # EC-55: Validate port before conversion
        port, port_error = _validate_port(db_port, default=3306)
        if port_error:
            return jsonify({"success": False, "message": port_error})

        from mysql_to_sheets.core.database import get_connection

        conn = get_connection(
            db_type=db_type,
            host=db_host,
            port=port,
            user=db_user,
            password=db_password,
            database=db_name,
        )

        tables = []
        with conn:
            if db_type == "mysql":
                cursor = conn.execute("SHOW TABLES")
                table_names = [row[0] for row in cursor.fetchall()]
            elif db_type == "postgres":
                cursor = conn.execute(
                    """SELECT table_name FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"""
                )
                table_names = [row[0] for row in cursor.fetchall()]
            elif db_type == "sqlite":
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                table_names = [row[0] for row in cursor.fetchall()]
            elif db_type == "mssql":
                cursor = conn.execute(
                    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
                )
                table_names = [row[0] for row in cursor.fetchall()]
            else:
                return jsonify({"success": False, "message": f"Unsupported database type: {db_type}"})

            # Get row counts for each table (optional, with fallback)
            for table_name in table_names:
                try:
                    # Quote table names to prevent SQL injection
                    if db_type == "mssql":
                        count_cursor = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                    else:
                        count_cursor = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                    row_count = count_cursor.fetchone()[0]
                except Exception:
                    row_count = None

                tables.append({"name": table_name, "row_count": row_count})

        return jsonify(
            {
                "success": True,
                "tables": tables,
                "message": f"Found {len(tables)} table(s)",
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": str(e),
                "remediation": _get_db_error_remediation(str(e)),
            }
        )


@dashboard_bp.route("/api/setup/schema/columns/<table_name>", methods=["GET"])
def api_schema_columns(table_name: str) -> Response:
    """List columns for a specific table with types.

    Args:
        table_name: Name of the table to get columns for.

    Returns:
        JSON response with list of columns and their types.
    """
    try:
        db_type = request.args.get("db_type") or os.getenv("DB_TYPE", "mysql")
        db_host = request.args.get("db_host") or os.getenv("DB_HOST", "localhost")
        db_port = request.args.get("db_port") or os.getenv("DB_PORT")
        db_user = request.args.get("db_user") or os.getenv("DB_USER")
        db_password = request.args.get("db_password") or os.getenv("DB_PASSWORD")
        db_name = request.args.get("db_name") or os.getenv("DB_NAME")

        if not db_name:
            return jsonify({"success": False, "message": "Database name is required"})

        # EC-55: Validate port before conversion
        port, port_error = _validate_port(db_port, default=3306)
        if port_error:
            return jsonify({"success": False, "message": port_error})

        from mysql_to_sheets.core.database import get_connection

        conn = get_connection(
            db_type=db_type,
            host=db_host,
            port=port,
            user=db_user,
            password=db_password,
            database=db_name,
        )

        # First validate table_name exists to prevent SQL injection
        with conn:
            if db_type == "mysql":
                cursor = conn.execute("SHOW TABLES")
                valid_tables = [row[0] for row in cursor.fetchall()]
            elif db_type == "postgres":
                cursor = conn.execute(
                    """SELECT table_name FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"""
                )
                valid_tables = [row[0] for row in cursor.fetchall()]
            elif db_type == "sqlite":
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                valid_tables = [row[0] for row in cursor.fetchall()]
            elif db_type == "mssql":
                cursor = conn.execute(
                    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
                )
                valid_tables = [row[0] for row in cursor.fetchall()]
            else:
                return jsonify({"success": False, "message": f"Unsupported database type: {db_type}"})

            if table_name not in valid_tables:
                return jsonify({"success": False, "message": f"Table '{table_name}' not found"})

            # Get column info
            columns = []
            if db_type == "mysql":
                cursor = conn.execute(f"DESCRIBE `{table_name}`")
                for row in cursor.fetchall():
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "key": row[3] if row[3] else None,
                        "default": row[4],
                    })
            elif db_type == "postgres":
                cursor = conn.execute(
                    f"""SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}' AND table_schema = 'public'
                        ORDER BY ordinal_position"""
                )
                for row in cursor.fetchall():
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "default": row[3],
                    })
            elif db_type == "sqlite":
                cursor = conn.execute(f'PRAGMA table_info("{table_name}")')
                for row in cursor.fetchall():
                    columns.append({
                        "name": row[1],
                        "type": row[2] or "TEXT",
                        "nullable": not row[3],  # notnull flag
                        "key": "PK" if row[5] else None,
                        "default": row[4],
                    })
            elif db_type == "mssql":
                cursor = conn.execute(
                    f"""SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = '{table_name}'
                        ORDER BY ORDINAL_POSITION"""
                )
                for row in cursor.fetchall():
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "default": row[3],
                    })

        return jsonify(
            {
                "success": True,
                "table": table_name,
                "columns": columns,
                "message": f"Found {len(columns)} column(s)",
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": str(e),
                "remediation": _get_db_error_remediation(str(e)),
            }
        )


@dashboard_bp.route("/api/setup/schema/preview", methods=["POST"])
def api_schema_preview() -> Response:
    """Preview query results with a limit of 10 rows.

    Returns:
        JSON response with preview data.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})

        query = data.get("query", "")
        if not query:
            return jsonify({"success": False, "message": "Query is required"})

        # Validate it's a SELECT query
        query_stripped = query.strip().upper()
        if not query_stripped.startswith("SELECT"):
            return jsonify({"success": False, "message": "Only SELECT queries are allowed"})

        db_type = data.get("db_type") or os.getenv("DB_TYPE", "mysql")
        db_host = data.get("db_host") or os.getenv("DB_HOST", "localhost")
        db_port = data.get("db_port") or os.getenv("DB_PORT")
        db_user = data.get("db_user") or os.getenv("DB_USER")
        db_password = data.get("db_password") or os.getenv("DB_PASSWORD")
        db_name = data.get("db_name") or os.getenv("DB_NAME")

        if not db_name:
            return jsonify({"success": False, "message": "Database name is required"})

        # EC-55: Validate port before conversion
        port, port_error = _validate_port(db_port, default=3306)
        if port_error:
            return jsonify({"success": False, "message": port_error})

        from mysql_to_sheets.core.database import get_connection

        conn = get_connection(
            db_type=db_type,
            host=db_host,
            port=port,
            user=db_user,
            password=db_password,
            database=db_name,
        )

        # Force a LIMIT 10 for preview
        preview_query = query.rstrip(";")
        if "LIMIT" not in preview_query.upper():
            preview_query += " LIMIT 10"
        else:
            # Replace existing LIMIT with 10
            import re
            preview_query = re.sub(r"\bLIMIT\s+\d+", "LIMIT 10", preview_query, flags=re.IGNORECASE)

        with conn:
            cursor = conn.execute(preview_query)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            # Convert rows to list of lists for JSON serialization
            from mysql_to_sheets.core.sync import clean_value
            rows_data = [[clean_value(cell) for cell in row] for row in rows]

        return jsonify(
            {
                "success": True,
                "columns": columns,
                "rows": rows_data,
                "row_count": len(rows_data),
                "message": f"Preview showing {len(rows_data)} row(s)",
            }
        )

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": str(e),
                "remediation": _get_db_error_remediation(str(e)),
            }
        )


def _get_db_error_remediation(error_msg: str) -> str:
    """Get remediation hint for database errors."""
    error_lower = error_msg.lower()

    if "connection refused" in error_lower:
        return "Check that your database server is running and the host/port are correct"
    elif "access denied" in error_lower or "authentication" in error_lower:
        return "Verify your database username and password are correct"
    elif "unknown database" in error_lower:
        return "Check that the database name exists on the server"
    elif "timeout" in error_lower:
        return "Check network connectivity and firewall rules"
    elif "ssl" in error_lower:
        return "Check SSL configuration - try disabling SSL or provide correct certificates"
    else:
        return "Check your database credentials and ensure the server is accessible"


def _get_sheets_error_remediation(error_msg: str) -> str:
    """Get remediation hint for Google Sheets errors."""
    error_lower = error_msg.lower()

    if "not found" in error_lower:
        return "Check the sheet ID is correct and the sheet exists"
    elif "permission" in error_lower or "forbidden" in error_lower:
        return "Share the Google Sheet with your service account email (found in the JSON as client_email)"
    elif "invalid" in error_lower and "credential" in error_lower:
        return "Your service account JSON may be corrupted - download a fresh copy from Google Cloud Console"
    elif "quota" in error_lower:
        return "API quota exceeded - wait a few minutes and try again"
    else:
        return "Check your service account credentials and ensure the sheet is shared with the service account"
