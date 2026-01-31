"""CLI commands for diagnostics and troubleshooting.

Contains: diagnose, debug-sync commands.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

from mysql_to_sheets import __version__
from mysql_to_sheets.core.config import get_config, reset_config
from mysql_to_sheets.core.exceptions import (
    ConfigError,
    DatabaseError,
    ErrorCode,
    SheetsError,
    get_remediation_hint,
)

# Status indicators
PASS = "\033[92m[PASS]\033[0m"  # Green
FAIL = "\033[91m[FAIL]\033[0m"  # Red
WARN = "\033[93m[WARN]\033[0m"  # Yellow
INFO = "\033[94m[INFO]\033[0m"  # Blue


def _no_color() -> bool:
    """Check if color output should be disabled."""
    return os.getenv("NO_COLOR") is not None or not sys.stdout.isatty()


def _status(status: str) -> str:
    """Return status indicator, respecting NO_COLOR."""
    if _no_color():
        return (
            status.replace("\033[92m", "")
            .replace("\033[91m", "")
            .replace("\033[93m", "")
            .replace("\033[94m", "")
            .replace("\033[0m", "")
        )
    return status


def add_diagnose_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add diagnose-related command parsers.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    # Diagnose command
    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="Run comprehensive system diagnostics",
    )
    diagnose_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    diagnose_parser.add_argument(
        "--skip-connections",
        action="store_true",
        help="Skip database and Sheets connection tests",
    )

    # Debug sync command
    debug_sync_parser = subparsers.add_parser(
        "debug-sync",
        help="Run sync with detailed step-by-step timing",
    )
    debug_sync_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    debug_sync_parser.add_argument(
        "--sheet-id",
        dest="google_sheet_id",
        help="Google Sheets spreadsheet ID (overrides .env)",
    )
    debug_sync_parser.add_argument(
        "--worksheet",
        dest="google_worksheet_name",
        help="Target worksheet name (overrides .env)",
    )


def _check_python_version() -> dict[str, Any]:
    """Check Python version compatibility."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    passed = version >= (3, 9)
    return {
        "check": "Python version",
        "passed": passed,
        "value": version_str,
        "message": "Python 3.9+ required" if not passed else None,
    }


def _check_virtual_env() -> dict[str, Any]:
    """Check if running in a virtual environment."""
    in_venv = sys.prefix != sys.base_prefix
    return {
        "check": "Virtual environment",
        "passed": in_venv,
        "value": "active" if in_venv else "not active",
        "message": "Virtual environment recommended" if not in_venv else None,
    }


def _check_dependencies() -> dict[str, Any]:
    """Check required dependencies are installed."""
    required = ["gspread", "mysql.connector", "dotenv"]
    missing = []

    for pkg in required:
        try:
            if pkg == "mysql.connector":
                import mysql.connector  # noqa: F401
            elif pkg == "gspread":
                import gspread  # noqa: F401
            elif pkg == "dotenv":
                import dotenv  # noqa: F401
        except ImportError:
            missing.append(pkg)

    return {
        "check": "Dependencies",
        "passed": len(missing) == 0,
        "value": "all installed" if not missing else f"missing: {', '.join(missing)}",
        "message": "Run: pip install -r requirements.txt" if missing else None,
    }


def _check_env_file() -> dict[str, Any]:
    """Check if .env file exists and is configured."""
    from mysql_to_sheets.core.paths import get_default_env_path

    env_path = get_default_env_path()
    exists = env_path.exists()

    if not exists:
        return {
            "check": ".env file",
            "passed": False,
            "value": "not found",
            "message": f"Create .env at {env_path}",
            "code": ErrorCode.CONFIG_FILE_NOT_FOUND,
        }

    # Check if it has placeholder values
    content = env_path.read_text()
    has_placeholders = any(
        placeholder in content
        for placeholder in ["your_password", "your_spreadsheet_id_here", "your_"]
    )

    if has_placeholders:
        return {
            "check": ".env file",
            "passed": False,
            "value": "found but not configured",
            "message": "Edit .env to replace placeholder values",
            "code": ErrorCode.CONFIG_INVALID_VALUE,
        }

    return {
        "check": ".env file",
        "passed": True,
        "value": str(env_path),
        "message": None,
    }


def _check_service_account() -> dict[str, Any]:
    """Check if service account file exists."""
    reset_config()
    config = get_config()
    sa_path = Path(config.service_account_file)

    if not sa_path.exists():
        return {
            "check": "Service Account file",
            "passed": False,
            "value": f"not found at {sa_path}",
            "message": "Download from Google Cloud Console > IAM > Service Accounts",
            "code": ErrorCode.SHEETS_AUTH_FAILED,
        }

    # Verify it's valid JSON with expected fields
    try:
        with open(sa_path) as f:
            sa_data = json.load(f)
        if "client_email" not in sa_data:
            return {
                "check": "Service Account file",
                "passed": False,
                "value": "invalid format",
                "message": "Service account JSON must contain 'client_email' field",
                "code": ErrorCode.SHEETS_AUTH_FAILED,
            }
        email = sa_data.get("client_email", "")
        return {
            "check": "Service Account file",
            "passed": True,
            "value": f"found ({email})",
            "message": None,
        }
    except json.JSONDecodeError:
        return {
            "check": "Service Account file",
            "passed": False,
            "value": "invalid JSON",
            "message": "Service account file is not valid JSON",
            "code": ErrorCode.CONFIG_PARSE_ERROR,
        }


def _check_database_config() -> dict[str, Any]:
    """Check database configuration."""
    reset_config()
    config = get_config()

    if not config.db_host:
        return {
            "check": "Database config",
            "passed": False,
            "value": "DB_HOST not set",
            "message": "Set DB_HOST in .env",
            "code": ErrorCode.CONFIG_MISSING_FIELD,
        }

    return {
        "check": "Database config",
        "passed": True,
        "value": f"{config.db_type}://{config.db_host}:{config.db_port}/{config.db_name}",
        "message": None,
    }


def _check_database_connection() -> dict[str, Any]:
    """Test database connection."""
    from mysql_to_sheets.core.sync import SyncService

    reset_config()
    config = get_config()
    service = SyncService(config)

    start = time.time()
    try:
        service.test_database_connection()
        latency = int((time.time() - start) * 1000)
        return {
            "check": "Database connection",
            "passed": True,
            "value": f"OK (latency: {latency}ms)",
            "message": None,
        }
    except DatabaseError as e:
        return {
            "check": "Database connection",
            "passed": False,
            "value": e.message,
            "message": get_remediation_hint(e.code) if e.code else None,
            "code": e.code,
        }


def _check_query_syntax() -> dict[str, Any]:
    """Check SQL query syntax (basic validation)."""
    reset_config()
    config = get_config()

    query = config.sql_query.strip().upper() if config.sql_query else ""

    if not query:
        return {
            "check": "SQL query",
            "passed": False,
            "value": "not set",
            "message": "Set SQL_QUERY in .env",
            "code": ErrorCode.CONFIG_MISSING_FIELD,
        }

    if not query.startswith("SELECT"):
        return {
            "check": "SQL query",
            "passed": False,
            "value": "not a SELECT statement",
            "message": "SQL_QUERY must be a SELECT statement",
            "code": ErrorCode.DB_QUERY_ERROR,
        }

    # Check for dangerous statements
    dangerous = ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT"]
    for kw in dangerous:
        if f" {kw} " in f" {query} ":
            return {
                "check": "SQL query",
                "passed": False,
                "value": f"contains {kw}",
                "message": "SQL_QUERY should not contain modifying statements",
                "code": ErrorCode.DB_QUERY_ERROR,
            }

    return {
        "check": "SQL query",
        "passed": True,
        "value": "valid SELECT statement",
        "message": None,
    }


def _check_sheets_connection() -> dict[str, Any]:
    """Test Google Sheets connection."""
    from mysql_to_sheets.core.sync import SyncService

    reset_config()
    config = get_config()

    if not config.google_sheet_id:
        return {
            "check": "Google Sheets config",
            "passed": False,
            "value": "GOOGLE_SHEET_ID not set",
            "message": "Set GOOGLE_SHEET_ID in .env",
            "code": ErrorCode.CONFIG_MISSING_FIELD,
        }

    service = SyncService(config)

    start = time.time()
    try:
        service.test_sheets_connection()
        latency = int((time.time() - start) * 1000)
        return {
            "check": "Google Sheets connection",
            "passed": True,
            "value": f"OK (latency: {latency}ms)",
            "message": None,
            "extra": {
                "sheet_id": config.google_sheet_id,
                "worksheet": config.google_worksheet_name,
            },
        }
    except SheetsError as e:
        return {
            "check": "Google Sheets connection",
            "passed": False,
            "value": e.message,
            "message": get_remediation_hint(e.code) if e.code else None,
            "code": e.code,
        }


def cmd_diagnose(args: argparse.Namespace) -> int:
    """Execute diagnose command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 if all checks pass, 1 otherwise).
    """
    results: dict[str, list[dict[str, Any]]] = {
        "system": [],
        "configuration": [],
        "database": [],
        "sheets": [],
    }

    # System checks
    results["system"].append(_check_python_version())
    results["system"].append(_check_virtual_env())
    results["system"].append(_check_dependencies())

    # Configuration checks
    results["configuration"].append(_check_env_file())
    results["configuration"].append(_check_service_account())
    results["configuration"].append(_check_database_config())
    results["configuration"].append(_check_query_syntax())

    # Connection checks (if not skipped)
    if not args.skip_connections:
        results["database"].append(_check_database_connection())
        results["sheets"].append(_check_sheets_connection())

    # Output results
    if args.output == "json":
        # Calculate summary
        all_checks = [check for section in results.values() for check in section]
        passed = sum(1 for c in all_checks if c["passed"])
        failed = sum(1 for c in all_checks if not c["passed"])

        output = {
            "version": __version__,
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "summary": {
                "total": len(all_checks),
                "passed": passed,
                "failed": failed,
            },
            "results": results,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        # Text output
        print(f"\nMySQL to Sheets Diagnostics v{__version__}")
        print("=" * 50)

        sections = [
            ("System", results["system"]),
            ("Configuration", results["configuration"]),
            ("Database Connection", results["database"]),
            ("Google Sheets", results["sheets"]),
        ]

        for section_name, checks in sections:
            if not checks:
                continue
            print(f"\n{section_name}")
            print("-" * len(section_name))

            for check in checks:
                status = _status(PASS) if check["passed"] else _status(FAIL)
                print(f"{status} {check['check']}: {check['value']}")
                if check.get("message"):
                    print(f"       -> {check['message']}")

        # Summary
        all_checks = [check for section in results.values() for check in section]
        passed = sum(1 for c in all_checks if c["passed"])
        failed = sum(1 for c in all_checks if not c["passed"])

        print(f"\n{'=' * 50}")
        print(f"Summary: {passed} passed, {failed} failed")

        if failed > 0:
            print("\nFix the failed checks above before running sync.")
            return 1

        print("\nAll checks passed! Your configuration looks good.")
        return 0

    return 0 if all(c["passed"] for section in results.values() for c in section) else 1


def cmd_debug_sync(args: argparse.Namespace) -> int:
    """Execute debug-sync command with step-by-step timing.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    from mysql_to_sheets.core.sync import SyncService

    steps: list[dict[str, Any]] = []
    total_start = time.time()

    try:
        # Step 1: Load config
        step_start = time.time()
        reset_config()
        config = get_config()

        # Apply overrides
        overrides = {}
        if hasattr(args, "google_sheet_id") and args.google_sheet_id:
            overrides["google_sheet_id"] = args.google_sheet_id
        if hasattr(args, "google_worksheet_name") and args.google_worksheet_name:
            overrides["google_worksheet_name"] = args.google_worksheet_name
        if overrides:
            config = config.with_overrides(**overrides)

        step_time = int((time.time() - step_start) * 1000)
        steps.append(
            {
                "step": 1,
                "name": "Loading config",
                "status": "OK",
                "duration_ms": step_time,
            }
        )

        # Step 2: Connect to database
        step_start = time.time()
        service = SyncService(config)
        service.test_database_connection()
        step_time = int((time.time() - step_start) * 1000)
        steps.append(
            {
                "step": 2,
                "name": "Connecting to database",
                "status": "OK",
                "duration_ms": step_time,
            }
        )

        # Step 3: Execute query
        step_start = time.time()
        from mysql_to_sheets.core.database import get_connection
        from mysql_to_sheets.core.database.base import DatabaseConfig

        db_config = DatabaseConfig(
            host=config.db_host,
            port=config.db_port,
            user=config.db_user,
            password=config.db_password,
            database=config.db_name,
        )
        with get_connection(db_config) as conn:
            result = conn.execute(config.sql_query)
            columns = result.headers
            rows = result.rows
            row_count = len(rows)

        step_time = int((time.time() - step_start) * 1000)
        steps.append(
            {
                "step": 3,
                "name": "Executing query",
                "status": f"OK ({row_count} rows, {len(columns)} columns)",
                "duration_ms": step_time,
                "rows": row_count,
                "columns": len(columns),
            }
        )

        # Step 4: Push to Sheets (dry run - just test connection)
        step_start = time.time()
        service.test_sheets_connection()
        step_time = int((time.time() - step_start) * 1000)
        steps.append(
            {
                "step": 4,
                "name": "Testing Sheets connection",
                "status": "OK",
                "duration_ms": step_time,
            }
        )

        total_time = int((time.time() - total_start) * 1000)

        # Find bottleneck
        slowest = max(steps, key=lambda s: s["duration_ms"])
        bottleneck_pct = int((slowest["duration_ms"] / total_time) * 100) if total_time > 0 else 0

    except ConfigError as e:
        step_time = int((time.time() - step_start) * 1000)
        steps.append(
            {
                "step": len(steps) + 1,
                "name": "Loading config",
                "status": "FAILED",
                "duration_ms": step_time,
                "error": e.message,
                "code": e.code,
            }
        )
        total_time = int((time.time() - total_start) * 1000)
        slowest = None
        bottleneck_pct = 0

    except DatabaseError as e:
        step_time = int((time.time() - step_start) * 1000)
        steps.append(
            {
                "step": len(steps) + 1,
                "name": "Database operation",
                "status": "FAILED",
                "duration_ms": step_time,
                "error": e.message,
                "code": e.code,
                "remediation": e.remediation,
            }
        )
        total_time = int((time.time() - total_start) * 1000)
        slowest = None
        bottleneck_pct = 0

    except SheetsError as e:
        step_time = int((time.time() - step_start) * 1000)
        steps.append(
            {
                "step": len(steps) + 1,
                "name": "Sheets operation",
                "status": "FAILED",
                "duration_ms": step_time,
                "error": e.message,
                "code": e.code,
                "remediation": e.remediation,
            }
        )
        total_time = int((time.time() - total_start) * 1000)
        slowest = None
        bottleneck_pct = 0

    except Exception as e:
        step_time = int((time.time() - step_start) * 1000)
        steps.append(
            {
                "step": len(steps) + 1,
                "name": "Unknown step",
                "status": "FAILED",
                "duration_ms": step_time,
                "error": str(e),
            }
        )
        total_time = int((time.time() - total_start) * 1000)
        slowest = None
        bottleneck_pct = 0

    # Output results
    if args.output == "json":
        output = {
            "steps": steps,
            "total_ms": total_time,
            "bottleneck": {
                "step": slowest["step"] if slowest else None,
                "name": slowest["name"] if slowest else None,
                "percent": bottleneck_pct,
            }
            if slowest
            else None,
            "success": all(s["status"].startswith("OK") for s in steps),
        }
        print(json.dumps(output, indent=2))
    else:
        print("\nDebug Sync - Step by Step")
        print("=" * 50)

        for step in steps:
            status = _status(PASS) if step["status"].startswith("OK") else _status(FAIL)
            print(f"Step {step['step']}/4: {step['name']}... {status} ({step['duration_ms']}ms)")
            if step.get("error"):
                print(f"         Error: {step['error']}")
                if step.get("code"):
                    print(f"         Code: {step['code']}")
                if step.get("remediation"):
                    print(f"         Hint: {step['remediation']}")

        print(f"\nTotal: {total_time}ms")
        if slowest and bottleneck_pct > 0:
            print(f"Bottleneck: Step {slowest['step']} ({bottleneck_pct}% of time)")

    # Return appropriate exit code
    failed = any(s["status"] == "FAILED" for s in steps)
    return 1 if failed else 0
