"""CLI commands for freshness/SLA monitoring.

Contains: freshness status/check/set-sla commands.

NOTE: Freshness/SLA monitoring requires BUSINESS tier or higher.
"""

from __future__ import annotations

import argparse
import json
import sys

from mysql_to_sheets.cli.tier_check import require_cli_tier
from mysql_to_sheets.cli.utils import (
    ensure_data_dir,
    format_table,
    get_organization_id,
    output_result,
)


def add_freshness_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add freshness management command parsers.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    freshness_parser = subparsers.add_parser(
        "freshness",
        help="Monitor data freshness and SLA compliance",
    )
    freshness_subparsers = freshness_parser.add_subparsers(
        dest="freshness_command",
        help="Freshness commands",
    )

    # freshness status
    freshness_status = freshness_subparsers.add_parser(
        "status",
        help="Show freshness status for all sync configs",
    )
    freshness_status.add_argument(
        "--org-slug",
        help="Organization slug",
    )
    freshness_status.add_argument(
        "--config-id",
        type=int,
        help="Specific config ID to check",
    )
    freshness_status.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # freshness check
    freshness_check = freshness_subparsers.add_parser(
        "check",
        help="Check freshness and send alerts for stale configs",
    )
    freshness_check.add_argument(
        "--org-slug",
        help="Organization slug (checks all orgs if not provided)",
    )
    freshness_check.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually send notifications",
    )
    freshness_check.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # freshness set-sla
    freshness_sla = freshness_subparsers.add_parser(
        "set-sla",
        help="Set SLA threshold for a sync config",
    )
    freshness_sla.add_argument(
        "config_id",
        type=int,
        help="Sync config ID",
    )
    freshness_sla.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    freshness_sla.add_argument(
        "--minutes",
        type=int,
        required=True,
        help="SLA threshold in minutes",
    )
    freshness_sla.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # freshness report
    freshness_report = freshness_subparsers.add_parser(
        "report",
        help="Generate a freshness report for an organization",
    )
    freshness_report.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    freshness_report.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


@require_cli_tier("freshness_sla")
def handle_freshness_command(args: argparse.Namespace) -> int:
    """Handle freshness commands.

    Requires BUSINESS tier or higher license.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    db_path = ensure_data_dir()

    if args.freshness_command == "status":
        return _cmd_freshness_status(args, db_path)
    elif args.freshness_command == "check":
        return _cmd_freshness_check(args, db_path)
    elif args.freshness_command == "set-sla":
        return _cmd_freshness_set_sla(args, db_path)
    elif args.freshness_command == "report":
        return _cmd_freshness_report(args, db_path)
    else:
        print("Error: Unknown freshness command. Use --help for usage.", file=sys.stderr)
        return 1


def _cmd_freshness_status(args: argparse.Namespace, db_path: str) -> int:
    """Show freshness status."""
    from mysql_to_sheets.core.freshness import (
        FRESHNESS_FRESH,
        FRESHNESS_STALE,
        FRESHNESS_WARNING,
        check_all_freshness,
        get_freshness_status,
    )

    # Get organization ID
    org_id = None
    if args.org_slug:
        org_id = get_organization_id(args.org_slug, db_path)
        if not org_id:
            output_result(
                {"success": False, "message": f"Organization not found: {args.org_slug}"},
                args.output,
            )
            return 1
    else:
        # Use first org
        from mysql_to_sheets.models.organizations import OrganizationRepository

        org_repo = OrganizationRepository(db_path)
        orgs = org_repo.get_all()
        if orgs:
            org_id = orgs[0].id
        else:
            output_result(
                {"success": False, "message": "No organizations found. Create one first."},
                args.output,
            )
            return 1

    # Get specific config or all
    if args.config_id:
        assert org_id is not None
        status = get_freshness_status(args.config_id, org_id, db_path=db_path)
        if not status:
            output_result(
                {"success": False, "message": f"Config not found: {args.config_id}"},
                args.output,
            )
            return 1
        statuses = [status]
    else:
        assert org_id is not None
        statuses = check_all_freshness(org_id, enabled_only=True, db_path=db_path)

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "statuses": [s.to_dict() for s in statuses],
                    "count": len(statuses),
                },
                indent=2,
                default=str,
            )
        )
    else:
        if not statuses:
            print("No sync configs found.")
        else:
            # Status icons for text display
            status_icons = {
                FRESHNESS_FRESH: "✓",
                FRESHNESS_WARNING: "⚠",
                FRESHNESS_STALE: "✗",
                "unknown": "?",
            }

            headers = ["ID", "Name", "Status", "Last Sync", "SLA", "% Used"]
            rows = []
            for s in statuses:
                icon = status_icons.get(s.status, "?")
                last_sync = (
                    f"{s.minutes_since_sync}m ago" if s.minutes_since_sync is not None else "Never"
                )
                pct = f"{s.percent_of_sla:.0f}%" if s.percent_of_sla is not None else "-"
                rows.append(
                    [
                        s.config_id,
                        s.config_name[:20],
                        f"{icon} {s.status}",
                        last_sync,
                        f"{s.sla_minutes}m",
                        pct,
                    ]
                )

            print(format_table(headers, rows))

            # Summary
            fresh = sum(1 for s in statuses if s.status == FRESHNESS_FRESH)
            warning = sum(1 for s in statuses if s.status == FRESHNESS_WARNING)
            stale = sum(1 for s in statuses if s.status == FRESHNESS_STALE)
            print(f"\nSummary: {fresh} fresh, {warning} warning, {stale} stale")

    return 0


def _cmd_freshness_check(args: argparse.Namespace, db_path: str) -> int:
    """Check freshness and send alerts."""
    from mysql_to_sheets.core.freshness_alerts import check_and_alert, check_and_alert_all

    send_notifications = not args.dry_run

    if args.org_slug:
        org_id = get_organization_id(args.org_slug, db_path)
        if not org_id:
            output_result(
                {"success": False, "message": f"Organization not found: {args.org_slug}"},
                args.output,
            )
            return 1

        alerts = check_and_alert(
            organization_id=org_id,
            db_path=db_path,
            send_notifications=send_notifications,
        )
        all_alerts = {org_id: alerts} if alerts else {}
    else:
        all_alerts = check_and_alert_all(
            db_path=db_path,
            send_notifications=send_notifications,
        )

    # Count total alerts
    total_alerts = sum(len(a) for a in all_alerts.values())

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "alerts": all_alerts,
                    "total_alerts": total_alerts,
                    "notifications_sent": send_notifications,
                },
                indent=2,
                default=str,
            )
        )
    else:
        if total_alerts == 0:
            print("No freshness alerts triggered.")
        else:
            print(f"Triggered {total_alerts} freshness alerts:")
            for org_id, alerts in all_alerts.items():
                for alert in alerts:
                    icon = "⚠" if alert["severity"] == "warning" else "✗"
                    print(
                        f"  {icon} [{alert['severity']}] {alert['config_name']}: {alert['message']}"
                    )

            if args.dry_run:
                print("\n(Dry run - no notifications sent)")
            else:
                print(f"\nNotifications sent: {total_alerts}")

    return 0


def _cmd_freshness_set_sla(args: argparse.Namespace, db_path: str) -> int:
    """Set SLA threshold for a config."""
    from mysql_to_sheets.core.freshness import set_sla

    org_id = get_organization_id(args.org_slug, db_path)
    if not org_id:
        output_result(
            {"success": False, "message": f"Organization not found: {args.org_slug}"},
            args.output,
        )
        return 1

    if args.minutes < 1:
        output_result(
            {"success": False, "message": "SLA must be at least 1 minute"},
            args.output,
        )
        return 1

    success = set_sla(
        config_id=args.config_id,
        organization_id=org_id,
        sla_minutes=args.minutes,
        db_path=db_path,
    )

    if success:
        output_result(
            {
                "success": True,
                "message": f"SLA for config {args.config_id} set to {args.minutes} minutes",
            },
            args.output,
        )
        return 0
    else:
        output_result(
            {"success": False, "message": f"Config not found: {args.config_id}"},
            args.output,
        )
        return 1


def _cmd_freshness_report(args: argparse.Namespace, db_path: str) -> int:
    """Generate freshness report."""
    from mysql_to_sheets.core.freshness import get_freshness_report

    org_id = get_organization_id(args.org_slug, db_path)
    if not org_id:
        output_result(
            {"success": False, "message": f"Organization not found: {args.org_slug}"},
            args.output,
        )
        return 1

    report = get_freshness_report(organization_id=org_id, db_path=db_path)

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "report": report,
                },
                indent=2,
                default=str,
            )
        )
    else:
        print(f"Freshness Report for Organization {args.org_slug}")
        print("=" * 50)
        print(f"Total Configs: {report['total_configs']}")
        print(f"Health Score: {report['health_percent']:.1f}%")
        print()
        print("Status Breakdown:")
        for status, count in report["counts"].items():
            print(f"  {status}: {count}")
        print()
        print(f"Checked at: {report['checked_at']}")

    return 0
