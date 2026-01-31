"""CLI commands for reverse sync (Sheets -> DB).

Provides commands to sync data from Google Sheets back to a database:
- reverse-sync: Execute reverse sync operation

NOTE: Reverse sync requires PRO tier or higher.
"""

from __future__ import annotations

import argparse
import json

from mysql_to_sheets.cli.tier_check import require_cli_tier
from mysql_to_sheets.core.config import get_config, reset_config


def add_reverse_sync_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add reverse-sync subparser to the main parser.

    Args:
        subparsers: Subparsers action from main parser.
    """
    reverse_parser = subparsers.add_parser(
        "reverse-sync",
        help="Sync data from Google Sheets to database",
        description="Pull data from Google Sheets and push to a database table",
    )

    # Required arguments
    reverse_parser.add_argument(
        "--table",
        "-t",
        required=True,
        dest="table_name",
        help="Target database table name",
    )

    # Key columns for upsert/conflict detection
    reverse_parser.add_argument(
        "--key-columns",
        "-k",
        help="Comma-separated list of key columns for conflict detection",
    )

    # Conflict mode
    reverse_parser.add_argument(
        "--conflict",
        "-c",
        choices=["overwrite", "skip", "error"],
        default="overwrite",
        dest="conflict_mode",
        help="How to handle existing rows (default: overwrite)",
    )

    # Column mapping
    reverse_parser.add_argument(
        "--column-mapping",
        help='Column mapping as JSON (e.g., \'{"Sheet Col": "db_col"}\')',
    )

    # Source configuration
    reverse_parser.add_argument(
        "--sheet-id",
        help="Google Sheets spreadsheet ID (overrides .env)",
    )
    reverse_parser.add_argument(
        "--worksheet",
        help="Worksheet name (overrides .env)",
    )
    reverse_parser.add_argument(
        "--range",
        dest="sheet_range",
        help="Specific range to read (e.g., 'A1:E100')",
    )

    # Database configuration
    reverse_parser.add_argument(
        "--db-type",
        choices=["mysql", "postgres", "sqlite", "mssql"],
        help="Database type (overrides .env)",
    )
    reverse_parser.add_argument(
        "--db-host",
        help="Database host (overrides .env)",
    )
    reverse_parser.add_argument(
        "--db-port",
        type=int,
        help="Database port (overrides .env)",
    )
    reverse_parser.add_argument(
        "--db-name",
        help="Database name (overrides .env)",
    )

    # Processing options
    reverse_parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of rows per batch (default: 1000)",
    )
    reverse_parser.add_argument(
        "--no-header",
        action="store_true",
        help="Sheet does not have a header row",
    )

    # Output options
    reverse_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without writing to database",
    )
    reverse_parser.add_argument(
        "--preview",
        action="store_true",
        help="Show data preview without writing",
    )
    reverse_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output in JSON format",
    )
    reverse_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )


@require_cli_tier("reverse_sync")
def cmd_reverse_sync(args: argparse.Namespace) -> int:
    """Execute reverse sync command.

    Requires PRO tier or higher license.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    from mysql_to_sheets.core.reverse_sync import (
        ConflictMode,
        ReverseSyncConfig,
        run_reverse_sync,
    )
    from mysql_to_sheets.core.sync import setup_logging

    # Reset config to pick up any overrides
    reset_config()

    # Load base config
    config = get_config()

    # Apply command-line overrides
    overrides = {}
    if args.sheet_id:
        overrides["google_sheet_id"] = args.sheet_id
    if args.worksheet:
        overrides["google_worksheet_name"] = args.worksheet
    if args.db_type:
        overrides["db_type"] = args.db_type
    if args.db_host:
        overrides["db_host"] = args.db_host
    if args.db_port:
        overrides["db_port"] = args.db_port
    if args.db_name:
        overrides["db_name"] = args.db_name

    if overrides:
        config = config.with_overrides(**overrides)

    # Setup logging
    if args.verbose:
        config = config.with_overrides(log_level="DEBUG")
    logger = setup_logging(config)

    # Parse key columns
    key_columns = []
    if args.key_columns:
        key_columns = [col.strip() for col in args.key_columns.split(",")]

    # Parse column mapping
    column_mapping = None
    if args.column_mapping:
        try:
            column_mapping = json.loads(args.column_mapping)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid column mapping JSON: {e}")
            return 1

    # Build reverse sync config
    reverse_config = ReverseSyncConfig(
        table_name=args.table_name,
        key_columns=key_columns,
        conflict_mode=ConflictMode(args.conflict_mode),
        column_mapping=column_mapping,
        batch_size=args.batch_size,
        skip_header=not args.no_header,
        sheet_range=args.sheet_range,
    )

    # Execute reverse sync
    try:
        result = run_reverse_sync(
            config=config,
            reverse_config=reverse_config,
            logger=logger,
            dry_run=args.dry_run,
            preview=args.preview,
        )

        if args.json_output:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            if result.success:
                print("\nReverse sync completed successfully!")
                print(f"  Rows processed: {result.rows_processed}")
                print(f"  Rows inserted:  {result.rows_inserted}")
                print(f"  Rows updated:   {result.rows_updated}")
                print(f"  Rows skipped:   {result.rows_skipped}")
            else:
                print(f"\nReverse sync failed: {result.error}")

        return 0 if result.success else 1

    except Exception as e:
        if args.json_output:
            print(json.dumps({"success": False, "error": str(e)}, indent=2))
        else:
            print(f"\nError: {e}")
        return 1
