"""CLI commands for snapshots and rollback.

Contains: snapshot list/show/cleanup and rollback commands.

NOTE: Snapshots and rollback require BUSINESS tier or higher.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from mysql_to_sheets.cli.tier_check import require_cli_tier
from mysql_to_sheets.cli.utils import (
    ensure_data_dir,
    format_table,
    get_organization_id,
    output_result,
)
from mysql_to_sheets.core.config import get_config


def add_snapshot_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add snapshot command parser.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    # Main snapshot command with subcommands
    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Manage sheet snapshots for rollback",
    )
    snapshot_subparsers = snapshot_parser.add_subparsers(
        dest="snapshot_action",
        help="Snapshot action",
    )

    # snapshot list
    list_parser = snapshot_subparsers.add_parser(
        "list",
        help="List available snapshots",
    )
    list_parser.add_argument(
        "--sheet-id",
        help="Filter by Google Sheet ID",
    )
    list_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of snapshots to show (default: 20)",
    )
    list_parser.add_argument(
        "--org-slug",
        help="Organization slug (required for multi-tenant)",
    )
    list_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # snapshot show
    show_parser = snapshot_subparsers.add_parser(
        "show",
        help="Show snapshot details",
    )
    show_parser.add_argument(
        "snapshot_id",
        type=int,
        help="Snapshot ID to show",
    )
    show_parser.add_argument(
        "--org-slug",
        help="Organization slug (required for multi-tenant)",
    )
    show_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # snapshot cleanup
    cleanup_parser = snapshot_subparsers.add_parser(
        "cleanup",
        help="Clean up old snapshots based on retention policy",
    )
    cleanup_parser.add_argument(
        "--org-slug",
        help="Organization slug (required for multi-tenant)",
    )
    cleanup_parser.add_argument(
        "--retention-count",
        type=int,
        help="Maximum snapshots to keep per sheet (overrides config)",
    )
    cleanup_parser.add_argument(
        "--retention-days",
        type=int,
        help="Delete snapshots older than N days (overrides config)",
    )
    cleanup_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # snapshot stats
    stats_parser = snapshot_subparsers.add_parser(
        "stats",
        help="Show snapshot storage statistics",
    )
    stats_parser.add_argument(
        "--org-slug",
        help="Organization slug (required for multi-tenant)",
    )
    stats_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # snapshot delete
    delete_parser = snapshot_subparsers.add_parser(
        "delete",
        help="Delete a specific snapshot",
    )
    delete_parser.add_argument(
        "snapshot_id",
        type=int,
        help="Snapshot ID to delete",
    )
    delete_parser.add_argument(
        "--org-slug",
        help="Organization slug (required for multi-tenant)",
    )
    delete_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def add_rollback_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add rollback command parser.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    rollback_parser = subparsers.add_parser(
        "rollback",
        help="Restore sheet from a snapshot",
    )
    rollback_parser.add_argument(
        "snapshot_id",
        type=int,
        help="Snapshot ID to restore from",
    )
    rollback_parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview changes without applying",
    )
    rollback_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup snapshot before rollback",
    )
    rollback_parser.add_argument(
        "--org-slug",
        help="Organization slug (required for multi-tenant)",
    )
    rollback_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def _get_org_id_or_default(org_slug: str | None, db_path: str) -> int:
    """Get organization ID from slug or use default (1).

    Args:
        org_slug: Optional organization slug.
        db_path: Database path.

    Returns:
        Organization ID.

    Raises:
        SystemExit: If org slug provided but not found.
    """
    if org_slug:
        org_id = get_organization_id(org_slug, db_path)
        if org_id is None:
            print(f"Error: Organization '{org_slug}' not found")
            raise SystemExit(1)
        return org_id
    return 1  # Default organization ID


@require_cli_tier("snapshots")
def cmd_snapshot(args: argparse.Namespace) -> int:
    """Execute snapshot command.

    Requires BUSINESS tier or higher license.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    action = getattr(args, "snapshot_action", None)

    if action is None:
        print("Error: Please specify a snapshot action (list, show, cleanup, stats, delete)")
        return 1

    db_path = ensure_data_dir()
    config = get_config()

    if action == "list":
        return _cmd_snapshot_list(args, db_path, config)
    elif action == "show":
        return _cmd_snapshot_show(args, db_path, config)
    elif action == "cleanup":
        return _cmd_snapshot_cleanup(args, db_path, config)
    elif action == "stats":
        return _cmd_snapshot_stats(args, db_path, config)
    elif action == "delete":
        return _cmd_snapshot_delete(args, db_path, config)
    else:
        print(f"Error: Unknown snapshot action '{action}'")
        return 1


def _cmd_snapshot_list(args: argparse.Namespace, db_path: str, config: Any) -> int:
    """List snapshots."""
    from mysql_to_sheets.core.snapshots import list_snapshots

    org_id = _get_org_id_or_default(getattr(args, "org_slug", None), db_path)

    snapshots = list_snapshots(
        organization_id=org_id,
        db_path=db_path,
        sheet_id=getattr(args, "sheet_id", None),
        limit=args.limit,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "snapshots": [s.to_dict() for s in snapshots],
                    "total": len(snapshots),
                },
                indent=2,
                default=str,
            )
        )
    else:
        if not snapshots:
            print("No snapshots found.")
        else:
            print(f"Snapshots ({len(snapshots)} found):\n")
            headers = ["ID", "Created", "Rows", "Cols", "Size", "Sheet ID"]
            rows = []
            for s in snapshots:
                created = s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "N/A"
                size = (
                    f"{s.size_bytes / 1024:.1f}KB"
                    if s.size_bytes < 1024 * 1024
                    else f"{s.size_bytes / (1024 * 1024):.1f}MB"
                )
                sheet_id = (s.sheet_id[:18] + "...") if len(s.sheet_id) > 21 else s.sheet_id
                rows.append([s.id, created, s.row_count, s.column_count, size, sheet_id])
            print(format_table(headers, rows))

    return 0


def _cmd_snapshot_show(args: argparse.Namespace, db_path: str, config: Any) -> int:
    """Show snapshot details."""
    from mysql_to_sheets.core.snapshots import get_snapshot

    org_id = _get_org_id_or_default(getattr(args, "org_slug", None), db_path)

    snapshot = get_snapshot(
        snapshot_id=args.snapshot_id,
        organization_id=org_id,
        db_path=db_path,
        include_data=False,
    )

    if snapshot is None:
        output_result(
            {"success": False, "message": f"Snapshot {args.snapshot_id} not found"},
            args.output,
        )
        return 1

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "snapshot": snapshot.to_dict(),
                },
                indent=2,
                default=str,
            )
        )
    else:
        print(f"Snapshot {snapshot.id}:")
        print(f"  Created: {snapshot.created_at}")
        print(f"  Sheet ID: {snapshot.sheet_id}")
        print(f"  Worksheet: {snapshot.worksheet_name}")
        print(f"  Rows: {snapshot.row_count}")
        print(f"  Columns: {snapshot.column_count}")
        print(f"  Size: {snapshot.size_bytes / 1024:.1f} KB")
        print(f"  Checksum: {snapshot.checksum[:16]}...")
        if snapshot.headers:
            print(
                f"  Headers: {', '.join(snapshot.headers[:5])}"
                + ("..." if len(snapshot.headers) > 5 else "")
            )

    return 0


def _cmd_snapshot_cleanup(args: argparse.Namespace, db_path: str, config: Any) -> int:
    """Clean up old snapshots."""
    from mysql_to_sheets.core.snapshot_retention import (
        RetentionConfig,
        cleanup_old_snapshots,
    )

    org_id = _get_org_id_or_default(getattr(args, "org_slug", None), db_path)

    retention_config = RetentionConfig(
        retention_count=getattr(args, "retention_count", None) or config.snapshot_retention_count,
        retention_days=getattr(args, "retention_days", None) or config.snapshot_retention_days,
        max_size_mb=config.snapshot_max_size_mb,
    )

    result = cleanup_old_snapshots(
        organization_id=org_id,
        db_path=db_path,
        retention_config=retention_config,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    **result.to_dict(),
                },
                indent=2,
            )
        )
    else:
        print("Cleanup completed:")
        print(f"  Deleted by count limit: {result.deleted_by_count}")
        print(f"  Deleted by age limit: {result.deleted_by_age}")
        print(f"  Total deleted: {result.total_deleted}")
        print(f"  Sheets processed: {result.sheets_processed}")

    return 0


def _cmd_snapshot_stats(args: argparse.Namespace, db_path: str, config: Any) -> int:
    """Show snapshot storage statistics."""
    from mysql_to_sheets.core.snapshot_retention import get_storage_stats

    org_id = _get_org_id_or_default(getattr(args, "org_slug", None), db_path)

    stats = get_storage_stats(
        organization_id=org_id,
        db_path=db_path,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    **stats.to_dict(),
                },
                indent=2,
            )
        )
    else:
        print("Snapshot Storage Statistics:\n")
        print(f"  Total snapshots: {stats.total_snapshots}")
        print(f"  Total size: {stats.total_size_mb:.2f} MB")
        if stats.oldest_snapshot:
            print(f"  Oldest: {stats.oldest_snapshot}")
        if stats.newest_snapshot:
            print(f"  Newest: {stats.newest_snapshot}")

        if stats.by_sheet:
            print("\n  By Sheet:")
            for sheet_id, sheet_stats in stats.by_sheet.items():
                short_id = (sheet_id[:18] + "...") if len(sheet_id) > 21 else sheet_id
                size_mb = sheet_stats.get("size_bytes", 0) / (1024 * 1024)
                print(f"    {short_id}: {sheet_stats['count']} snapshots, {size_mb:.2f} MB")

    return 0


def _cmd_snapshot_delete(args: argparse.Namespace, db_path: str, config: Any) -> int:
    """Delete a specific snapshot."""
    from mysql_to_sheets.core.snapshots import delete_snapshot

    org_id = _get_org_id_or_default(getattr(args, "org_slug", None), db_path)

    deleted = delete_snapshot(
        snapshot_id=args.snapshot_id,
        organization_id=org_id,
        db_path=db_path,
    )

    if deleted:
        output_result(
            {"success": True, "message": f"Deleted snapshot {args.snapshot_id}"},
            args.output,
        )
        return 0
    else:
        output_result(
            {"success": False, "message": f"Snapshot {args.snapshot_id} not found"},
            args.output,
        )
        return 1


@require_cli_tier("snapshots")
def cmd_rollback(args: argparse.Namespace) -> int:
    """Execute rollback command.

    Requires BUSINESS tier or higher license.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    from mysql_to_sheets.core.rollback import (
        can_rollback,
        preview_rollback,
        rollback_to_snapshot,
    )
    from mysql_to_sheets.core.snapshots import get_snapshot

    db_path = ensure_data_dir()
    config = get_config()
    org_id = _get_org_id_or_default(getattr(args, "org_slug", None), db_path)

    # Get snapshot to check sheet info
    snapshot = get_snapshot(
        snapshot_id=args.snapshot_id,
        organization_id=org_id,
        db_path=db_path,
        include_data=False,
    )

    if snapshot is None:
        output_result(
            {"success": False, "message": f"Snapshot {args.snapshot_id} not found"},
            args.output,
        )
        return 1

    # Create config with snapshot's sheet info
    rollback_config = config.with_overrides(
        google_sheet_id=snapshot.sheet_id,
        google_worksheet_name=snapshot.worksheet_name,
    )

    # Check if rollback is possible
    can_proceed, reason = can_rollback(
        snapshot_id=args.snapshot_id,
        organization_id=org_id,
        config=rollback_config,
        db_path=db_path,
    )

    if not can_proceed:
        output_result(
            {"success": False, "message": f"Cannot rollback: {reason}"},
            args.output,
        )
        return 1

    # Preview mode
    if args.preview:
        preview = preview_rollback(
            snapshot_id=args.snapshot_id,
            organization_id=org_id,
            config=rollback_config,
            db_path=db_path,
        )

        if args.output == "json":
            print(
                json.dumps(
                    {
                        "success": True,
                        "preview": True,
                        **preview.to_dict(),
                    },
                    indent=2,
                    default=str,
                )
            )
        else:
            print(f"Rollback Preview for Snapshot {args.snapshot_id}:\n")
            print(f"  Snapshot created: {preview.snapshot_created_at}")
            print(f"  Current rows: {preview.current_row_count}")
            print(f"  Snapshot rows: {preview.snapshot_row_count}")
            print(f"  Current columns: {preview.current_column_count}")
            print(f"  Snapshot columns: {preview.snapshot_column_count}")

            if preview.diff:
                print("\n  Changes:")
                print(f"    {preview.diff.summary()}")

        return 0

    # Execute rollback
    result = rollback_to_snapshot(
        snapshot_id=args.snapshot_id,
        organization_id=org_id,
        config=rollback_config,
        db_path=db_path,
        create_backup=not args.no_backup,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": result.success,
                    **result.to_dict(),
                },
                indent=2,
            )
        )
    else:
        if result.success:
            print("Rollback completed successfully!")
            print(f"  Restored {result.rows_restored} rows, {result.columns_restored} columns")
            if result.backup_snapshot_id:
                print(f"  Backup snapshot created: ID {result.backup_snapshot_id}")
        else:
            print(f"Rollback failed: {result.error}")

    return 0 if result.success else 1
