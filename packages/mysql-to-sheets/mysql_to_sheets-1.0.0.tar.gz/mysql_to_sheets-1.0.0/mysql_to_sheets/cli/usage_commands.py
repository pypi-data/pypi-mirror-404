"""Usage tracking CLI commands.

Provides commands to view usage metrics for billing and analytics.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.core.usage_tracking import (
    check_usage_threshold,
    get_current_usage,
    get_usage_history,
    get_usage_summary,
)

logger = logging.getLogger("mysql_to_sheets.cli.usage")


def register_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register usage CLI commands.

    Args:
        subparsers: Argument parser subparsers.
    """
    usage_parser = subparsers.add_parser(
        "usage",
        help="View usage metrics for billing",
        description="View usage metrics including rows synced, operations, and API calls.",
    )
    usage_subparsers = usage_parser.add_subparsers(dest="usage_command")

    # usage current
    current_parser = usage_subparsers.add_parser(
        "current",
        help="Show current period usage",
        description="Display usage for the current billing period.",
    )
    current_parser.add_argument(
        "--org-id",
        type=int,
        required=True,
        help="Organization ID",
    )
    current_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    current_parser.set_defaults(func=cmd_usage_current)

    # usage history
    history_parser = usage_subparsers.add_parser(
        "history",
        help="Show usage history",
        description="Display usage for past billing periods.",
    )
    history_parser.add_argument(
        "--org-id",
        type=int,
        required=True,
        help="Organization ID",
    )
    history_parser.add_argument(
        "--limit",
        type=int,
        default=6,
        help="Number of periods to show (default: 6)",
    )
    history_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    history_parser.set_defaults(func=cmd_usage_history)

    # usage summary
    summary_parser = usage_subparsers.add_parser(
        "summary",
        help="Show usage summary",
        description="Display usage summary with totals.",
    )
    summary_parser.add_argument(
        "--org-id",
        type=int,
        required=True,
        help="Organization ID",
    )
    summary_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    summary_parser.set_defaults(func=cmd_usage_summary)

    # Set default handler for bare 'usage' command
    usage_parser.set_defaults(func=lambda args: usage_parser.print_help())


def cmd_usage_current(args: argparse.Namespace) -> int:
    """Handle 'usage current' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code (0 for success).
    """
    db_path = get_tenant_db_path()

    try:
        record = get_current_usage(args.org_id, db_path)
        thresholds = check_usage_threshold(args.org_id, db_path=db_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.output == "json":
        output = {
            "usage": record.to_dict(),
            "thresholds": thresholds,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        _print_usage_text(record, thresholds)

    return 0


def cmd_usage_history(args: argparse.Namespace) -> int:
    """Handle 'usage history' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code (0 for success).
    """
    db_path = get_tenant_db_path()

    try:
        records = get_usage_history(args.org_id, limit=args.limit, db_path=db_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.output == "json":
        output = {
            "periods": [r.to_dict() for r in records],
            "count": len(records),
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        _print_history_text(records)

    return 0


def cmd_usage_summary(args: argparse.Namespace) -> int:
    """Handle 'usage summary' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code (0 for success).
    """
    db_path = get_tenant_db_path()

    try:
        summary = get_usage_summary(args.org_id, db_path=db_path)
        thresholds = check_usage_threshold(args.org_id, db_path=db_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.output == "json":
        output = {
            **summary,
            "thresholds": thresholds,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        _print_summary_text(summary, thresholds)

    return 0


def _print_usage_text(record: Any, thresholds: dict[str, Any]) -> None:
    """Print usage record in text format.

    Args:
        record: Usage record.
        thresholds: Threshold status.
    """
    print("\nCurrent Period Usage")
    print("=" * 50)
    print(f"Period: {record.period_start} to {record.period_end}")
    print()

    # Rows synced
    rows_status = thresholds.get("rows_synced", {})
    rows_indicator = _get_status_indicator(rows_status)
    print(f"Rows Synced:      {record.rows_synced:,} {rows_indicator}")

    # Sync operations
    ops_status = thresholds.get("sync_operations", {})
    ops_indicator = _get_status_indicator(ops_status)
    print(f"Sync Operations:  {record.sync_operations:,} {ops_indicator}")

    # API calls
    api_status = thresholds.get("api_calls", {})
    api_indicator = _get_status_indicator(api_status)
    print(f"API Calls:        {record.api_calls:,} {api_indicator}")


def _print_history_text(records: list[Any]) -> None:
    """Print usage history in text format.

    Args:
        records: List of usage records.
    """
    if not records:
        print("No usage history found.")
        return

    print("\nUsage History")
    print("=" * 70)
    print(f"{'Period':<25} {'Rows':>12} {'Operations':>12} {'API Calls':>12}")
    print("-" * 70)

    for r in records:
        period = f"{r.period_start} to {r.period_end}"
        print(f"{period:<25} {r.rows_synced:>12,} {r.sync_operations:>12,} {r.api_calls:>12,}")


def _print_summary_text(summary: dict[str, Any], thresholds: dict[str, Any]) -> None:
    """Print usage summary in text format.

    Args:
        summary: Usage summary.
        thresholds: Threshold status.
    """
    current = summary.get("current_period", {})
    totals = summary.get("totals", {})

    print("\nUsage Summary")
    print("=" * 50)

    print("\nCurrent Period:")
    period = f"{current.get('period_start', 'N/A')} to {current.get('period_end', 'N/A')}"
    print(f"  Period: {period}")

    rows_status = thresholds.get("rows_synced", {})
    print(f"  Rows Synced: {current.get('rows_synced', 0):,} {_get_status_indicator(rows_status)}")

    ops_status = thresholds.get("sync_operations", {})
    print(
        f"  Sync Operations: {current.get('sync_operations', 0):,} {_get_status_indicator(ops_status)}"
    )

    api_status = thresholds.get("api_calls", {})
    print(f"  API Calls: {current.get('api_calls', 0):,} {_get_status_indicator(api_status)}")

    print(f"\nHistorical Totals ({summary.get('periods_tracked', 0)} periods):")
    print(f"  Total Rows Synced: {totals.get('rows_synced', 0):,}")
    print(f"  Total Sync Operations: {totals.get('sync_operations', 0):,}")
    print(f"  Total API Calls: {totals.get('api_calls', 0):,}")


def _get_status_indicator(status: dict[str, Any]) -> str:
    """Get status indicator for threshold.

    Args:
        status: Threshold status dict.

    Returns:
        Status indicator string.
    """
    if not status or status.get("limit") is None:
        return "(unlimited)"

    limit = status.get("limit", 0)
    percent = status.get("percent", 0)

    if status.get("exceeded"):
        return f"[EXCEEDED - {percent:.0f}% of {limit:,}]"
    elif status.get("warning"):
        return f"[WARNING - {percent:.0f}% of {limit:,}]"
    else:
        return f"({percent:.0f}% of {limit:,})"
