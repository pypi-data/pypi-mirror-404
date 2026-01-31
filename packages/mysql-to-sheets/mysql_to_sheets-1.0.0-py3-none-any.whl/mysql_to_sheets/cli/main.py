"""Command-line interface for MySQL to Google Sheets sync.

This module provides the main entry point for the CLI. Commands are organized
into separate modules:

- quickstart_commands: quickstart (interactive setup wizard)
- sync_commands: sync, validate, test-db, test-sheets
- api_key_commands: api-key create/list/revoke
- history_commands: history
- schedule_commands: schedule add/list/remove/enable/disable/trigger/run
- org_commands: org create/list/get/update/delete
- user_commands: user create/list/get/update/delete/reset-password
- config_commands: config add/list/get/update/delete/sync
- webhook_commands: webhook create/list/get/update/delete/test
- job_commands: jobs list/status/cancel/retry/worker/stats/cleanup
- freshness_commands: freshness status/check/set-sla/report
- favorite_commands: favorite query/sheet add/list/get/edit/remove
- sheet_commands: sheet create/list/delete (worksheet management)
- pii_commands: pii detect/policy/acknowledge/preview (PII protection)
"""

import argparse
import sys
from typing import NoReturn

from mysql_to_sheets import __version__
from mysql_to_sheets.core.exceptions import SyncError

# Category-specific exit codes for scripting and automation.
# config=1, db=2, sheets=3, auth=4, license=5, tier=6, other=1
EXIT_OK = 0
EXIT_CONFIG = 1
EXIT_DATABASE = 2
EXIT_SHEETS = 3
EXIT_AUTH = 4
EXIT_LICENSE = 5  # License validation failed
EXIT_TIER = 6  # Tier insufficient for feature
from mysql_to_sheets.cli.admin_commands import add_admin_parsers, handle_admin_command
from mysql_to_sheets.cli.api_key_commands import add_api_key_parsers, cmd_api_key
from mysql_to_sheets.cli.audit_commands import add_audit_parsers, handle_audit_command
from mysql_to_sheets.cli.config_commands import add_config_parsers, handle_config_command
from mysql_to_sheets.cli.db_commands import add_db_parsers, handle_db_command
from mysql_to_sheets.cli.diagnose_commands import add_diagnose_parsers, cmd_debug_sync, cmd_diagnose
from mysql_to_sheets.cli.favorite_commands import add_favorite_parsers, handle_favorite_command
from mysql_to_sheets.cli.freshness_commands import add_freshness_parsers, handle_freshness_command
from mysql_to_sheets.cli.history_commands import add_history_parsers, cmd_history
from mysql_to_sheets.cli.job_commands import add_job_parsers, handle_jobs_command
from mysql_to_sheets.cli.license_commands import add_license_parsers, handle_license_command
from mysql_to_sheets.cli.multi_sheet_commands import add_multi_sheet_parsers, cmd_multi_sync
from mysql_to_sheets.cli.org_commands import add_org_parsers, handle_org_command
from mysql_to_sheets.cli.pii_commands import add_pii_parsers, handle_pii_command

# Import command modules
from mysql_to_sheets.cli.quickstart_commands import add_quickstart_parsers, cmd_quickstart
from mysql_to_sheets.cli.reverse_sync_commands import add_reverse_sync_parsers, cmd_reverse_sync
from mysql_to_sheets.cli.rollback_commands import (
    add_rollback_parsers,
    add_snapshot_parsers,
    cmd_rollback,
    cmd_snapshot,
)
from mysql_to_sheets.cli.schedule_commands import add_schedule_parsers, cmd_schedule
from mysql_to_sheets.cli.sheet_commands import add_sheet_parsers, handle_sheet_command
from mysql_to_sheets.cli.sync_commands import (
    add_sync_parsers,
    cmd_sync,
    cmd_test_db,
    cmd_test_sheets,
    cmd_validate,
)
from mysql_to_sheets.cli.tier_commands import add_tier_parsers, handle_tier_command
from mysql_to_sheets.cli.usage_commands import register_commands as add_usage_parsers
from mysql_to_sheets.cli.user_commands import add_user_parsers, handle_user_command
from mysql_to_sheets.cli.webhook_commands import add_webhook_parsers, handle_webhook_command

# Command groups for organized help display
COMMAND_GROUPS = {
    "Essential": {
        "commands": ["quickstart", "sync", "validate"],
        "description": "Get started and run syncs",
    },
    "Testing": {
        "commands": ["test-db", "test-sheets", "diagnose", "debug-sync"],
        "description": "Test connections and troubleshoot",
    },
    "Data Management": {
        "commands": ["history", "favorite", "sheet", "snapshot", "rollback"],
        "description": "Manage sync data and favorites",
    },
    "Scheduling": {
        "commands": ["schedule", "jobs", "freshness"],
        "description": "Automate syncs and monitor freshness",
    },
    "Administration": {
        "commands": ["org", "user", "config", "api-key", "tier", "usage", "db", "license", "admin"],
        "description": "Multi-tenant and organization management",
    },
    "Advanced": {
        "commands": ["reverse-sync", "multi-sync", "webhook", "audit", "pii"],
        "description": "Advanced sync modes and integrations",
    },
}


def print_grouped_help() -> None:
    """Print help with commands organized into groups."""
    print(f"mysql-to-sheets v{__version__}")
    print("Sync data from MySQL/PostgreSQL/SQLite to Google Sheets")
    print()

    for group_name, group_info in COMMAND_GROUPS.items():
        print(f"\033[1m{group_name}\033[0m - {group_info['description']}")
        commands = group_info["commands"]
        # Format commands in columns
        for i in range(0, len(commands), 4):
            row = commands[i : i + 4]
            print("  " + "  ".join(f"{cmd:<15}" for cmd in row))
        print()

    print("\033[2mUse --all to see all commands, or COMMAND --help for details\033[0m")
    print()
    print("Quick start:")
    print("  mysql-to-sheets quickstart    # Interactive first-time setup")
    print("  mysql-to-sheets sync          # Run sync with .env configuration")
    print()


def create_parser(show_all: bool = False) -> argparse.ArgumentParser:
    """Create the argument parser with all subcommands.

    Args:
        show_all: If True, show all commands. If False, show grouped help.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="mysql-to-sheets",
        description="Sync data from MySQL/PostgreSQL/SQLite to Google Sheets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quick Start:
  mysql-to-sheets quickstart     # Interactive first-time setup
  mysql-to-sheets sync           # Run sync with .env configuration
  mysql-to-sheets validate       # Validate configuration

Examples:
  # Run sync with overrides
  mysql-to-sheets sync --sheet-id=ABC123 --query="SELECT * FROM users"

  # Test connections
  mysql-to-sheets test-db --diagnose
  mysql-to-sheets test-sheets --diagnose

  # Manage schedules
  mysql-to-sheets schedule add --name="daily" --cron="0 6 * * *"
  mysql-to-sheets schedule list

Use --all to see all 50+ commands, or COMMAND --help for details.
""",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        dest="show_all_commands",
        help="Show all available commands",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command parsers from each module
    add_quickstart_parsers(subparsers)
    add_sync_parsers(subparsers)
    add_api_key_parsers(subparsers)
    add_history_parsers(subparsers)
    add_schedule_parsers(subparsers)
    add_org_parsers(subparsers)
    add_user_parsers(subparsers)
    add_config_parsers(subparsers)
    add_webhook_parsers(subparsers)
    add_audit_parsers(subparsers)
    add_job_parsers(subparsers)
    add_freshness_parsers(subparsers)
    add_snapshot_parsers(subparsers)
    add_rollback_parsers(subparsers)
    add_tier_parsers(subparsers)
    add_reverse_sync_parsers(subparsers)
    add_multi_sheet_parsers(subparsers)
    add_diagnose_parsers(subparsers)
    add_favorite_parsers(subparsers)
    add_sheet_parsers(subparsers)
    add_db_parsers(subparsers)
    add_usage_parsers(subparsers)
    add_license_parsers(subparsers)
    add_admin_parsers(subparsers)
    add_pii_parsers(subparsers)

    return parser


def _handle_usage_command(args: argparse.Namespace) -> int:
    """Handle usage subcommands."""
    if hasattr(args, "func"):
        result = args.func(args)
        return int(result) if result is not None else 0
    return 0


def cli(args: list[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        args: Command line arguments (uses sys.argv if None).

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Show grouped help if no command and not --all
    if not parsed_args.command:
        if hasattr(parsed_args, "show_all_commands") and parsed_args.show_all_commands:
            parser.print_help()
        else:
            print_grouped_help()
        return 0

    # Dispatch to appropriate command handler
    command_handlers = {
        "quickstart": cmd_quickstart,
        "sync": cmd_sync,
        "validate": cmd_validate,
        "test-db": cmd_test_db,
        "test-sheets": cmd_test_sheets,
        "api-key": cmd_api_key,
        "history": cmd_history,
        "schedule": cmd_schedule,
        "org": handle_org_command,
        "user": handle_user_command,
        "config": handle_config_command,
        "webhook": handle_webhook_command,
        "audit": handle_audit_command,
        "jobs": handle_jobs_command,
        "freshness": handle_freshness_command,
        "snapshot": cmd_snapshot,
        "rollback": cmd_rollback,
        "tier": handle_tier_command,
        "reverse-sync": cmd_reverse_sync,
        "multi-sync": cmd_multi_sync,
        "diagnose": cmd_diagnose,
        "debug-sync": cmd_debug_sync,
        "favorite": handle_favorite_command,
        "sheet": handle_sheet_command,
        "db": handle_db_command,
        "usage": _handle_usage_command,
        "license": handle_license_command,
        "admin": handle_admin_command,
        "pii": handle_pii_command,
    }

    handler = command_handlers.get(parsed_args.command)
    if handler:
        try:
            return handler(parsed_args)
        except SyncError as e:
            # User-friendly error formatting
            print(f"\nError: {e.message}", file=sys.stderr)
            if e.code:
                print(f"Code: {e.code}", file=sys.stderr)
            if e.remediation:
                print(f"\nHow to fix: {e.remediation}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("\nOperation cancelled.", file=sys.stderr)
            return 130
        except Exception as e:
            # Unexpected errors - show brief message, suggest debug mode
            print(f"\nUnexpected error: {e}", file=sys.stderr)
            print("Run with LOG_LEVEL=DEBUG for details.", file=sys.stderr)
            return 1

    # Unknown command
    print(f"Unknown command: {parsed_args.command}")
    print_grouped_help()
    return 1


def main() -> NoReturn:
    """Main entry point for the CLI.

    This function is called when running the CLI as a script.
    It calls cli() and exits with the returned code.
    """
    sys.exit(cli())


if __name__ == "__main__":
    main()
