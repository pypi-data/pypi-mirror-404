"""Interactive quickstart command for first-time setup.

This module provides a guided, interactive setup experience for new users
to configure their first sync without needing to manually edit .env files.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path
from typing import Any

from mysql_to_sheets import __version__


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal styling."""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def supports_color() -> bool:
    """Check if the terminal supports color output."""
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


def colorize(text: str, color: str) -> str:
    """Apply color to text if terminal supports it."""
    if supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text


def print_header(text: str) -> None:
    """Print a styled header."""
    print()
    print(colorize(f"{'=' * 50}", Colors.CYAN))
    print(colorize(f"  {text}", Colors.BOLD))
    print(colorize(f"{'=' * 50}", Colors.CYAN))
    print()


def print_step(step: int, total: int, title: str) -> None:
    """Print a step indicator."""
    print()
    print(colorize(f"Step {step}/{total}: {title}", Colors.BOLD + Colors.BLUE))
    print(colorize("-" * 40, Colors.DIM))


def print_success(text: str) -> None:
    """Print a success message."""
    print(colorize(f"  ✓ {text}", Colors.GREEN))


def print_error(text: str) -> None:
    """Print an error message."""
    print(colorize(f"  ✗ {text}", Colors.RED))


def print_info(text: str) -> None:
    """Print an info message."""
    print(colorize(f"  → {text}", Colors.CYAN))


def print_hint(text: str) -> None:
    """Print a hint message."""
    print(colorize(f"    {text}", Colors.DIM))


def prompt(label: str, default: str | None = None, password: bool = False) -> str:
    """Prompt user for input with optional default value."""
    if default:
        display_default = "****" if password and default else default
        prompt_text = f"  {label} [{display_default}]: "
    else:
        prompt_text = f"  {label}: "

    if password:
        value = getpass.getpass(prompt_text)
    else:
        value = input(prompt_text)

    return value.strip() if value.strip() else (default or "")


def prompt_choice(label: str, options: list[tuple[str, str]], default: int = 0) -> str:
    """Prompt user to choose from a list of options."""
    print(f"  {label}")
    for i, (value, description) in enumerate(options):
        marker = ">" if i == default else " "
        print(
            colorize(
                f"    {marker} [{i + 1}] {description}",
                Colors.DIM if i != default else Colors.RESET,
            )
        )

    while True:
        choice = input(f"  Choice [1-{len(options)}] (default: {default + 1}): ").strip()
        if not choice:
            return options[default][0]
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
        except ValueError:
            pass
        print_error(f"Please enter a number between 1 and {len(options)}")


def validate_database_connection(config: dict[str, Any]) -> tuple[bool, str]:
    """Validate database connection with provided config."""
    try:
        from mysql_to_sheets.core.database import get_connection
        from mysql_to_sheets.core.database.base import DatabaseConfig

        db_type = config.get("db_type", "mysql")

        if db_type == "sqlite":
            db_config = DatabaseConfig(
                db_type=db_type,
                database=config["db_name"],
            )
        else:
            db_config = DatabaseConfig(
                db_type=db_type,
                host=config["db_host"],
                port=int(config["db_port"]),
                user=config["db_user"],
                password=config["db_password"],
                database=config["db_name"],
            )

        conn = get_connection(db_config)

        # Test with simple query
        with conn:
            conn.execute("SELECT 1")

        return True, "Connection successful!"

    except Exception as e:
        return False, str(e)


def _get_service_account_email(path: str | None) -> str | None:
    """Extract client_email from service account JSON file.

    Args:
        path: Path to the service account JSON file.

    Returns:
        The client_email value, or None if file doesn't exist or can't be parsed.
    """
    if not path or not os.path.exists(path):
        return None
    try:
        import json

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("client_email")
    except Exception:
        return None


def validate_sheets_connection(config: dict[str, Any]) -> tuple[bool, str]:
    """Validate Google Sheets connection with provided config."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        service_account_path = config.get("service_account_file", "./service_account.json")

        if not os.path.exists(service_account_path):
            return False, f"Service account file not found: {service_account_path}"

        # Validate service account file structure before using it
        from mysql_to_sheets.core.config import (
            _validate_service_account_json,
            _validate_service_account_structure,
        )

        json_valid, json_error = _validate_service_account_json(service_account_path)
        if not json_valid:
            return False, json_error or "Invalid JSON in service account file"

        struct_valid, struct_error = _validate_service_account_structure(service_account_path)
        if not struct_valid:
            return False, struct_error or "Invalid service account file structure"

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ]

        creds = Credentials.from_service_account_file(service_account_path, scopes=scopes)  # type: ignore[no-untyped-call]
        client = gspread.authorize(creds)  # type: ignore[attr-defined]

        sheet_id = config.get("google_sheet_id", "")
        if not sheet_id:
            return False, "No sheet ID provided"

        # Validate sheet ID is not a wrong Google service URL
        from mysql_to_sheets.core.sheets_utils import parse_sheet_id, validate_google_url

        url_valid, url_error = validate_google_url(sheet_id)
        if not url_valid:
            return False, url_error or "Invalid Google Sheets URL"

        # Extract ID from URL if full URL provided
        try:
            sheet_id = parse_sheet_id(sheet_id)
        except ValueError as e:
            return False, str(e)

        spreadsheet = client.open_by_key(sheet_id)
        return True, f"Connected to: {spreadsheet.title}"

    except gspread.exceptions.SpreadsheetNotFound:
        # Enhanced error message with service account email (EC-35)
        sa_email = _get_service_account_email(config.get("service_account_file"))
        if sa_email:
            return (
                False,
                f"Spreadsheet not found or not shared with the service account. "
                f"Share the sheet with: {sa_email}",
            )
        return (
            False,
            "Spreadsheet not found. Make sure the ID is correct and shared with the service account. "
            "Find the service account email in your service_account.json file (client_email field).",
        )
    except gspread.exceptions.APIError as e:
        error_str = str(e).lower()
        # Enhanced permission denied error (EC-35)
        if "403" in error_str or "permission" in error_str:
            sa_email = _get_service_account_email(config.get("service_account_file"))
            if sa_email:
                return (
                    False,
                    f"Permission denied. Share the Google Sheet with your service account email: {sa_email}",
                )
            return (
                False,
                "Permission denied. Share the Google Sheet with your service account email "
                "(found in service_account.json under 'client_email').",
            )
        return False, f"Google Sheets API error: {e}"
    except Exception as e:
        return False, str(e)


def validate_query(config: dict[str, Any], query: str) -> tuple[bool, int, str]:
    """Validate SQL query and return row count."""
    try:
        from mysql_to_sheets.core.database import get_connection
        from mysql_to_sheets.core.database.base import DatabaseConfig

        db_type = config.get("db_type", "mysql")

        if db_type == "sqlite":
            db_config = DatabaseConfig(
                db_type=db_type,
                database=config["db_name"],
            )
        else:
            db_config = DatabaseConfig(
                db_type=db_type,
                host=config["db_host"],
                port=int(config["db_port"]),
                user=config["db_user"],
                password=config["db_password"],
                database=config["db_name"],
            )

        conn = get_connection(db_config)

        with conn:
            rows = conn.execute(query)
            count = len(rows.rows) if rows else 0

        return True, count, "Query executed successfully"

    except Exception as e:
        return False, 0, str(e)


def save_env_file(config: dict[str, Any], env_path: str = ".env") -> tuple[bool, str]:
    """Save configuration to .env file."""
    try:
        lines = []
        lines.append("# Generated by mysql-to-sheets quickstart")
        lines.append("")

        # Essential settings
        lines.append("# Database")
        lines.append(f"DB_TYPE={config.get('db_type', 'mysql')}")

        if config.get("db_type") == "sqlite":
            lines.append(f"DB_NAME={config.get('db_name', '')}")
        else:
            lines.append(f"DB_HOST={config.get('db_host', 'localhost')}")
            lines.append(f"DB_PORT={config.get('db_port', '3306')}")
            lines.append(f"DB_USER={config.get('db_user', '')}")
            lines.append(f"DB_PASSWORD={config.get('db_password', '')}")
            lines.append(f"DB_NAME={config.get('db_name', '')}")

        lines.append("")
        lines.append("# Google Sheets")
        lines.append(f"GOOGLE_SHEET_ID={config.get('google_sheet_id', '')}")
        lines.append(f"GOOGLE_WORKSHEET_NAME={config.get('worksheet', 'Sheet1')}")
        lines.append(
            f"SERVICE_ACCOUNT_FILE={config.get('service_account_file', './service_account.json')}"
        )

        lines.append("")
        lines.append("# Query")
        lines.append(f"SQL_QUERY={config.get('sql_query', '')}")

        lines.append("")
        lines.append("# Logging")
        lines.append("LOG_LEVEL=INFO")

        # Write file
        with open(env_path, "w") as f:
            f.write("\n".join(lines))
            f.write("\n")

        return True, f"Configuration saved to {env_path}"

    except Exception as e:
        return False, str(e)


def run_sync(config: dict[str, Any]) -> tuple[bool, int, str]:
    """Run the actual sync operation."""
    try:
        from mysql_to_sheets.core.config import Config
        from mysql_to_sheets.core.sync import run_sync as core_run_sync

        # Build config object
        sync_config = Config(
            db_type=config.get("db_type", "mysql"),
            db_host=config.get("db_host", "localhost"),
            db_port=int(config.get("db_port", 3306)),
            db_user=config.get("db_user", ""),
            db_password=config.get("db_password", ""),
            db_name=config.get("db_name", ""),
            google_sheet_id=config.get("google_sheet_id", ""),
            google_worksheet_name=config.get("worksheet", "Sheet1"),
            service_account_file=config.get("service_account_file", "./service_account.json"),
            sql_query=config.get("sql_query", ""),
        )

        result = core_run_sync(sync_config)

        if result.success:
            return True, result.rows_synced, "Sync completed successfully!"
        else:
            return False, 0, result.error or "Sync failed"

    except Exception as e:
        return False, 0, str(e)


def add_quickstart_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add quickstart command parser.

    Args:
        subparsers: Subparsers action from main argument parser.
    """
    parser = subparsers.add_parser(
        "quickstart",
        help="Interactive setup wizard for first-time configuration",
        description="Walk through an interactive setup to configure your first sync.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start interactive setup
  mysql-to-sheets quickstart

  # Save to custom .env path
  mysql-to-sheets quickstart --env-path=/path/to/.env

  # Start with demo data (no database required)
  mysql-to-sheets quickstart --demo
""",
    )

    parser.add_argument(
        "--env-path",
        default=".env",
        help="Path to save .env file (default: .env)",
    )

    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="Skip connection tests (not recommended)",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo data for quick evaluation (no real database needed)",
    )


def _prompt_database_uri() -> dict[str, Any] | None:
    """Prompt user for connection string and parse it.

    Returns:
        Parsed database config dict, or None if user skips.
    """
    from mysql_to_sheets.core.config import parse_database_uri

    print()
    print_hint("Or paste a connection string (leave empty to enter fields manually):")
    print_hint("  mysql://user:pass@host:3306/dbname")
    print_hint("  postgres://user:pass@host:5432/dbname")
    print_hint("  sqlite:///path/to/file.db")
    print()

    uri = prompt("Connection string", default="")
    if not uri.strip():
        return None

    try:
        parsed = parse_database_uri(uri)
        print_success(f"Parsed: {parsed['db_type'].upper()} database '{parsed['db_name']}'")
        if parsed["db_host"]:
            print_info(f"Host: {parsed['db_host']}:{parsed['db_port']}")
        return parsed
    except ValueError as e:
        print_error(f"Invalid connection string: {e}")
        print_hint("Please enter database details manually.")
        return None


def cmd_quickstart(args: argparse.Namespace) -> int:
    """Run interactive quickstart setup.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success).
    """
    config: dict[str, Any] = {}

    print_header(f"MySQL to Sheets Quickstart (v{__version__})")
    print("Welcome! Let's set up your first sync.")
    print("Press Ctrl+C at any time to exit.")
    print()

    try:
        # Handle demo mode
        if getattr(args, "demo", False):
            from mysql_to_sheets.core.demo import create_demo_database, get_demo_db_path

            print_step(1, 4, "Demo Database")
            print_info("Setting up demo database with sample data...")

            create_demo_database()
            demo_path = get_demo_db_path()

            config["db_type"] = "sqlite"
            config["db_name"] = str(demo_path)
            config["sql_query"] = "SELECT * FROM sample_customers LIMIT 100"

            print_success(f"Demo database created: {demo_path}")
            print()
            print_hint("Demo tables available:")
            print_hint("  - sample_customers (id, name, email, created_at, status)")
            print_hint("  - sample_orders (id, customer_id, amount, order_date)")
            print_hint("  - sample_products (id, name, category, price)")
            print()

            # Skip to step 2 for demo mode
            args.skip_test = True
        else:
            # Step 1: Database
            print_step(1, 4, "Database Connection")

            # Try connection string first
            parsed_uri = _prompt_database_uri()
            if parsed_uri:
                config.update(parsed_uri)
            else:
                db_type = prompt_choice(
                    "Select your database type:",
                    [
                        ("mysql", "MySQL"),
                        ("postgres", "PostgreSQL"),
                        ("sqlite", "SQLite (file-based)"),
                        ("mssql", "SQL Server"),
                    ],
                    default=0,
                )
                config["db_type"] = db_type

                if db_type == "sqlite":
                    config["db_name"] = prompt("Database file path", "/path/to/database.db")
                else:
                    port_defaults = {"mysql": "3306", "postgres": "5432", "mssql": "1433"}

                    config["db_host"] = prompt("Host", "localhost")
                    config["db_port"] = prompt("Port", port_defaults.get(db_type, "3306"))
                    config["db_user"] = prompt("Username")
                    config["db_password"] = prompt("Password", password=True)
                    config["db_name"] = prompt("Database name")

        if not args.skip_test:
            print()
            print_info("Testing connection...")
            success, message = validate_database_connection(config)
            if success:
                print_success(message)
            else:
                print_error(message)
                print_hint("Check your credentials and try again.")
                print()
                choice = input("  [R]etry, [D]emo mode, or [Q]uit? [R/d/q]: ").strip().lower()
                if choice == "d":
                    args.demo = True
                    return cmd_quickstart(args)
                elif choice == "q":
                    return 1
                else:
                    return cmd_quickstart(args)

        # Step 2: Google Sheets
        print_step(2, 4, "Google Sheets Access")

        default_sa = "./service_account.json"
        config["service_account_file"] = prompt("Service account JSON path", default_sa)

        if not os.path.exists(config["service_account_file"]):
            print_error(f"File not found: {config['service_account_file']}")
            print()
            print_hint("To get a service account file:")
            print_hint("1. Go to https://console.cloud.google.com/")
            print_hint("2. Create a project and enable Google Sheets API")
            print_hint("3. Create a Service Account and download the JSON key")
            print_hint("4. Share your Google Sheet with the service account email")
            print()
            print_hint("Full setup guide: docs/google-cloud-setup.md")
            print()
            return 1

        print()
        print("Enter your Google Sheet ID or paste the full URL:")
        print_hint("URL example: https://docs.google.com/spreadsheets/d/SHEET_ID/edit")
        config["google_sheet_id"] = prompt("Sheet ID or URL")

        config["worksheet"] = prompt("Worksheet name", "Sheet1")

        if not args.skip_test:
            print()
            print_info("Verifying sheet access...")
            success, message = validate_sheets_connection(config)
            if success:
                print_success(message)
            else:
                print_error(message)
                if "not found" in message.lower() or "404" in message:
                    print_hint("The sheet ID may be incorrect. Copy it from the URL:")
                    print_hint("  https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
                    print_hint("See: docs/google-cloud-setup.md#sheet-id")
                elif "permission" in message.lower() or "403" in message:
                    print_hint("Share the sheet with your service account email as Editor.")
                    print_hint("Find the email in service_account.json under 'client_email'.")
                    print_hint("See: docs/google-cloud-setup.md#sharing")
                else:
                    print_hint("Make sure you've shared the sheet with your service account email.")
                    print_hint("See: docs/google-cloud-setup.md#troubleshooting")
                return 1

        # Step 3: SQL Query
        print_step(3, 4, "SQL Query")

        # Check if query is already set (demo mode)
        if config.get("sql_query"):
            print(f"Using pre-configured query: {config['sql_query'][:60]}...")
            print()
            use_default = input("  Use this query? [Y/n]: ").strip().lower()
            if use_default == "n":
                config["sql_query"] = ""  # Reset to prompt for new query

        if not config.get("sql_query"):
            print("Enter your SQL query (press Enter twice when done):")
            print_hint("Example: SELECT * FROM users LIMIT 100")
            print()

            lines: list[str] = []
            while True:
                line = input("  > " if not lines else "  ... ")
                if not line and lines:
                    break
                lines.append(line)

            config["sql_query"] = " ".join(lines).strip()

            if not config["sql_query"]:
                print_error("No query provided")
                return 1

        if not args.skip_test:
            print()
            print_info("Testing query...")
            success, count, message = validate_query(config, config["sql_query"])
            if success:
                print_success(f"{message} ({count} rows)")
            else:
                print_error(message)
                return 1

        # Step 4: Run Sync
        print_step(4, 4, "Run First Sync")

        print("Configuration summary:")
        if config["db_type"] == "sqlite":
            print_info(f"Database: SQLite - {config['db_name']}")
        else:
            print_info(
                f"Database: {config['db_type'].upper()} - {config['db_name']}@{config['db_host']}"
            )
        print_info(f"Sheet: {config['google_sheet_id'][:30]}...")
        print_info(f"Worksheet: {config['worksheet']}")
        print_info(f"Query: {config['sql_query'][:50]}...")
        print()

        # Ask to save configuration FIRST (to temp file)
        print()
        save = input(f"  Save configuration to {args.env_path}? [Y/n]: ").strip().lower()
        want_save = save != "n"
        env_tmp_path = Path(str(args.env_path) + ".tmp")

        if want_save:
            success, message = save_env_file(config, env_tmp_path)
            if success:
                print_success(f"Configuration saved to {env_tmp_path}")
            else:
                print_error(message)
                want_save = False  # Can't save, continue without

        # Ask to run test sync
        run_now = input("  Run sync now to verify? [Y/n]: ").strip().lower()
        if run_now != "n":
            print()
            print_info("Running sync...")
            success, rows, message = run_sync(config)
            if success:
                print_success(f"{message} - {rows} rows synced!")
                # Sync succeeded - finalize config
                if want_save:
                    env_tmp_path.rename(args.env_path)
                    print_success(f"Configuration finalized to {args.env_path}")
                    # Validate the saved configuration
                    from mysql_to_sheets.core.config import get_config as _get_config
                    from mysql_to_sheets.core.config import reset_config as _reset_config

                    _reset_config()
                    try:
                        saved_config = _get_config()
                        errors = saved_config.validate()
                        if errors:
                            print_error(f"Saved config has {len(errors)} issue(s):")
                            for err in errors:
                                print_hint(f"  - {err}")
                        else:
                            print_success("Configuration validated successfully")
                    except Exception as val_err:
                        print_error(f"Could not validate saved config: {val_err}")
            else:
                print_error(message)
                # Sync failed - ask to keep config anyway
                if want_save:
                    keep = input("  Keep configuration anyway? [y/N]: ").strip().lower()
                    if keep == "y":
                        env_tmp_path.rename(args.env_path)
                        print_success(f"Configuration saved to {args.env_path}")
                    else:
                        env_tmp_path.unlink(missing_ok=True)
                        print_info("Configuration discarded.")
                        return 1
        elif want_save:
            # No test requested - finalize config
            env_tmp_path.rename(args.env_path)
            print_success(f"Configuration saved to {args.env_path}")

        # Success!
        print()
        print_header("Setup Complete!")
        print(colorize("  You can now run syncs with:", Colors.BOLD))
        print(colorize("    mysql-to-sheets sync", Colors.CYAN))
        print()

        # Enhanced next steps with numbered list
        print(colorize("  Next Steps:", Colors.BOLD))
        print()
        print(colorize("  1. Schedule automatic syncs", Colors.CYAN))
        print_hint("     mysql-to-sheets schedule add --name='daily' --cron='0 6 * * *'")
        print()
        print(colorize("  2. View sync history", Colors.CYAN))
        print_hint("     mysql-to-sheets history")
        print()
        print(colorize("  3. Launch web dashboard", Colors.CYAN))
        print_hint("     flask --app mysql_to_sheets.web.app run")
        print_hint("     Then open http://localhost:5000 in your browser")
        print()
        print(colorize("  4. Configure additional data sources", Colors.CYAN))
        print_hint("     Edit .env or use: mysql-to-sheets config add --name='reports'")
        print()
        print(colorize("  Security note:", Colors.DIM))
        print_hint("     API rate limiting is enabled by default (60 req/min).")
        print_hint("     Configure via RATE_LIMIT_ENABLED and RATE_LIMIT_RPM in .env")
        print()
        print(colorize("  Documentation:", Colors.DIM))
        print_hint("     https://github.com/BrandonFricke/mysql-to-sheets#readme")
        print()

        # Show demo upsell if in demo mode
        if getattr(args, "demo", False):
            print()
            print(colorize("  Ready for real data?", Colors.BOLD + Colors.YELLOW))
            print_hint(
                "     Run 'mysql-to-sheets quickstart' without --demo to connect your database"
            )
            print()

        return 0

    except KeyboardInterrupt:
        print()
        print()
        print_info("Setup cancelled.")
        return 1

    except Exception as e:
        print()
        print_error(f"Unexpected error: {e}")
        return 1
