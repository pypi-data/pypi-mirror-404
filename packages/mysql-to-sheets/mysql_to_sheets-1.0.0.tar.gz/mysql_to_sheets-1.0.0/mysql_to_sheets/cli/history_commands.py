"""CLI commands for sync history.

Contains: history command.
"""

from __future__ import annotations

import argparse
import json

from mysql_to_sheets.core.config import get_config


def add_history_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add history command parser.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    history_parser = subparsers.add_parser(
        "history",
        help="View sync history",
    )
    history_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of entries to show (default: 20)",
    )
    history_parser.add_argument(
        "--sheet-id",
        help="Filter by Google Sheet ID",
    )
    history_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def cmd_history(args: argparse.Namespace) -> int:
    """Execute history command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    from mysql_to_sheets.core.history import get_history_repository

    config = get_config()

    repo = get_history_repository(
        backend=config.history_backend,
        db_path=config.history_db_path if config.history_backend == "sqlite" else None,
    )

    if args.sheet_id:
        entries = repo.get_by_sheet_id(args.sheet_id, limit=args.limit)
    else:
        entries = repo.get_all(limit=args.limit)

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "entries": [
                        {
                            "id": e.id,
                            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                            "success": e.success,
                            "rows_synced": e.rows_synced,
                            "columns": e.columns,
                            "message": e.message,
                            "error": e.error,
                            "sheet_id": e.sheet_id,
                            "worksheet": e.worksheet,
                            "duration_ms": e.duration_ms,
                            "request_id": e.request_id,
                            "source": e.source,
                        }
                        for e in entries
                    ],
                    "total": len(entries),
                },
                indent=2,
            )
        )
    else:
        if not entries:
            print("No sync history found.")
        else:
            print(f"Sync History ({len(entries)} entries):")
            print("-" * 100)
            print(
                f"  {'Timestamp':<20}  {'Status':<8}  {'Rows':<8}  {'Duration':<10}  {'Sheet ID'}"
            )
            print("-" * 100)
            for entry in entries:
                timestamp = (
                    entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") if entry.timestamp else "N/A"
                )
                status = "Success" if entry.success else "Failed"
                duration = f"{entry.duration_ms:.0f}ms" if entry.duration_ms else "N/A"
                sheet_id = (
                    (entry.sheet_id[:20] + "...")
                    if entry.sheet_id and len(entry.sheet_id) > 23
                    else (entry.sheet_id or "N/A")
                )

                print(
                    f"  {timestamp:<20}  {status:<8}  {entry.rows_synced:<8}  {duration:<10}  {sheet_id}"
                )

                if entry.error:
                    print(f"      Error: {entry.error[:60]}...")

    return 0
