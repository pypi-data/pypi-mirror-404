"""CLI commands for audit log management.

NOTE: Audit logs require BUSINESS tier or higher.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from mysql_to_sheets.cli.tier_check import require_cli_tier
from mysql_to_sheets.cli.utils import (
    ensure_data_dir,
    get_organization_id,
    output_result,
)


def add_audit_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add audit management subcommands.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    audit_parser = subparsers.add_parser(
        "audit",
        help="Manage audit logs (multi-tenant)",
    )
    audit_subparsers = audit_parser.add_subparsers(
        dest="audit_command",
        help="Audit commands",
    )

    # audit list
    audit_list = audit_subparsers.add_parser(
        "list",
        help="List audit logs with filters",
    )
    audit_list.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    audit_list.add_argument(
        "--from",
        dest="from_date",
        help="Start date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    )
    audit_list.add_argument(
        "--to",
        dest="to_date",
        help="End date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
    )
    audit_list.add_argument(
        "--action",
        help="Filter by action type (e.g., sync.completed, auth.login)",
    )
    audit_list.add_argument(
        "--user-id",
        type=int,
        help="Filter by user ID",
    )
    audit_list.add_argument(
        "--resource-type",
        help="Filter by resource type (e.g., sync, user, config)",
    )
    audit_list.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of logs to show (default: 50)",
    )
    audit_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # audit export
    audit_export = audit_subparsers.add_parser(
        "export",
        help="Export audit logs to file",
    )
    audit_export.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    audit_export.add_argument(
        "--format",
        choices=["csv", "json", "jsonl", "cef"],
        default="csv",
        help="Export format (default: csv)",
    )
    audit_export.add_argument(
        "-o",
        "--output-file",
        help="Output file path (defaults to stdout)",
    )
    audit_export.add_argument(
        "--from",
        dest="from_date",
        help="Start date (ISO format)",
    )
    audit_export.add_argument(
        "--to",
        dest="to_date",
        help="End date (ISO format)",
    )
    audit_export.add_argument(
        "--action",
        help="Filter by action type",
    )
    audit_export.add_argument(
        "--user-id",
        type=int,
        help="Filter by user ID",
    )

    # audit stats
    audit_stats = audit_subparsers.add_parser(
        "stats",
        help="Show audit log statistics",
    )
    audit_stats.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    audit_stats.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # audit cleanup
    audit_cleanup = audit_subparsers.add_parser(
        "cleanup",
        help="Delete old audit logs (retention management)",
    )
    audit_cleanup.add_argument(
        "--older-than",
        type=int,
        default=90,
        help="Delete logs older than N days (default: 90)",
    )
    audit_cleanup.add_argument(
        "--org-slug",
        help="Optionally scope to specific organization",
    )
    audit_cleanup.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting",
    )
    audit_cleanup.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # audit actions
    audit_actions = audit_subparsers.add_parser(
        "actions",
        help="List valid audit action types",
    )
    audit_actions.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


@require_cli_tier("audit_logs")
def handle_audit_command(args: argparse.Namespace) -> int:
    """Handle audit management commands.

    Requires BUSINESS tier or higher license.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    db_path = ensure_data_dir()

    if args.audit_command == "list":
        return _handle_audit_list(args, db_path)
    elif args.audit_command == "export":
        return _handle_audit_export(args, db_path)
    elif args.audit_command == "stats":
        return _handle_audit_stats(args, db_path)
    elif args.audit_command == "cleanup":
        return _handle_audit_cleanup(args, db_path)
    elif args.audit_command == "actions":
        return _handle_audit_actions(args)
    else:
        print("Error: No audit command specified. Use --help for usage.")
        return 1


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse date string to datetime.

    Args:
        date_str: ISO format date string.

    Returns:
        datetime or None.
    """
    if not date_str:
        return None
    try:
        # Try full ISO format first
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        # Try date only
        return datetime.strptime(date_str, "%Y-%m-%d")


def _handle_audit_list(args: argparse.Namespace, db_path: str) -> int:
    """Handle audit list command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    from mysql_to_sheets.models.audit_logs import get_audit_log_repository

    from_date = _parse_date(args.from_date)
    to_date = _parse_date(args.to_date)

    repo = get_audit_log_repository(db_path)
    logs = repo.get_all(
        organization_id=org_id,
        from_date=from_date,
        to_date=to_date,
        action=args.action,
        user_id=args.user_id,
        resource_type=args.resource_type,
        limit=args.limit,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "logs": [log.to_dict() for log in logs],
                    "total": len(logs),
                },
                indent=2,
                default=str,
            )
        )
    else:
        if not logs:
            print("No audit logs found.")
        else:
            print(f"Audit Logs ({len(logs)} found):")
            print("-" * 100)
            for log in logs:
                timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "N/A"
                user = f"user={log.user_id}" if log.user_id else "system"
                resource = f"{log.resource_type}"
                if log.resource_id:
                    resource += f"/{log.resource_id}"
                print(f"  {timestamp}  {log.action:30s}  {resource:30s}  {user}")
                if log.rows_affected is not None:
                    print(f"                          rows_affected={log.rows_affected}")
                if log.source_ip:
                    print(f"                          ip={log.source_ip}")

    return 0


def _handle_audit_export(args: argparse.Namespace, db_path: str) -> int:
    """Handle audit export command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        print(f"Error: Organization '{args.org_slug}' not found", file=sys.stderr)
        return 1

    from mysql_to_sheets.core.audit_export import ExportOptions, export_audit_logs

    from_date = _parse_date(args.from_date)
    to_date = _parse_date(args.to_date)

    options = ExportOptions(
        from_date=from_date,
        to_date=to_date,
        action=args.action,
        user_id=args.user_id,
    )

    # Open output file or use stdout
    from typing import TextIO
    output: TextIO
    if args.output_file:
        output = open(args.output_file, "w", encoding="utf-8")
    else:
        output = sys.stdout

    try:
        result = export_audit_logs(
            organization_id=org_id,
            output=output,
            db_path=db_path,
            format=args.format,
            options=options,
        )

        if args.output_file:
            print(f"Exported {result.record_count} records to {args.output_file}", file=sys.stderr)
        else:
            # Add newline for stdout export
            if not output.closed:
                output.write("\n")

        return 0

    finally:
        if args.output_file and not output.closed:
            output.close()


def _handle_audit_stats(args: argparse.Namespace, db_path: str) -> int:
    """Handle audit stats command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    from mysql_to_sheets.core.audit_retention import get_retention_stats
    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.models.audit_logs import get_audit_log_repository

    config = get_config()
    retention_days = config.audit_retention_days

    repo = get_audit_log_repository(db_path)
    stats = repo.get_stats(org_id)
    retention = get_retention_stats(org_id, db_path, retention_days)

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "stats": {
                        **stats,
                        "retention_days": retention_days,
                        "logs_to_delete": retention.logs_to_delete,
                    },
                },
                indent=2,
                default=str,
            )
        )
    else:
        print(f"Audit Log Statistics for '{args.org_slug}':")
        print("-" * 50)
        print(f"  Total logs: {stats['total_logs']}")
        print(f"  Oldest log: {stats['oldest_log'] or 'N/A'}")
        print(f"  Newest log: {stats['newest_log'] or 'N/A'}")
        print(f"  Retention period: {retention_days} days")
        print(f"  Logs eligible for cleanup: {retention.logs_to_delete}")
        print()
        print("  By Action:")
        for action, count in sorted(stats.get("by_action", {}).items()):
            print(f"    {action}: {count}")
        print()
        print("  By Resource Type:")
        for rtype, count in sorted(stats.get("by_resource_type", {}).items()):
            print(f"    {rtype}: {count}")

    return 0


def _handle_audit_cleanup(args: argparse.Namespace, db_path: str) -> int:
    """Handle audit cleanup command."""
    from mysql_to_sheets.core.audit_retention import cleanup_old_logs

    org_id = None
    if args.org_slug:
        org_id = get_organization_id(args.org_slug, db_path)
        if org_id is None:
            output_result(
                {
                    "success": False,
                    "message": f"Organization '{args.org_slug}' not found",
                },
                args.output,
            )
            return 1

    result = cleanup_old_logs(
        retention_days=args.older_than,
        db_path=db_path,
        organization_id=org_id,
        dry_run=args.dry_run,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "result": result.to_dict(),
                },
                indent=2,
                default=str,
            )
        )
    else:
        action = "Would delete" if args.dry_run else "Deleted"
        scope = f"organization '{args.org_slug}'" if args.org_slug else "all organizations"
        print(f"{action} {result.deleted_count} audit logs from {scope}")
        print(f"  Cutoff date: {result.cutoff_date.isoformat()}")
        if args.dry_run:
            print("  (dry run - no changes made)")

    return 0


def _handle_audit_actions(args: argparse.Namespace) -> int:
    """Handle audit actions command."""
    from mysql_to_sheets.core.audit import VALID_AUDIT_ACTIONS

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "actions": VALID_AUDIT_ACTIONS,
                },
                indent=2,
            )
        )
    else:
        print("Valid Audit Actions:")
        print("-" * 40)

        # Group by prefix
        groups: dict[str, list[str]] = {}
        for action in sorted(VALID_AUDIT_ACTIONS):
            prefix = action.split(".")[0]
            if prefix not in groups:
                groups[prefix] = []
            groups[prefix].append(action)

        for prefix in sorted(groups.keys()):
            print(f"\n  {prefix}:")
            for action in groups[prefix]:
                print(f"    - {action}")

    return 0
