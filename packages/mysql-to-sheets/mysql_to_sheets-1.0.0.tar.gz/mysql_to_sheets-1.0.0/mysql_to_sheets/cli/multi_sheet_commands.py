"""CLI commands for multi-sheet sync.

Provides commands to sync data from a database to multiple Google Sheets:
- multi-sync: Execute multi-sheet sync operation

NOTE: Multi-sheet sync requires BUSINESS tier or higher.
"""

from __future__ import annotations

import argparse
import json

from mysql_to_sheets.cli.tier_check import require_cli_tier
from mysql_to_sheets.core.config import SheetTarget, get_config, reset_config


def add_multi_sheet_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add multi-sync subparser to the main parser.

    Args:
        subparsers: Subparsers action from main parser.
    """
    multi_parser = subparsers.add_parser(
        "multi-sync",
        help="Sync data to multiple Google Sheets",
        description="Push query results to multiple sheet targets with optional filtering",
    )

    # Targets configuration
    multi_parser.add_argument(
        "--targets",
        "-t",
        help="Path to JSON file with target configurations",
    )
    multi_parser.add_argument(
        "--targets-json",
        help='Inline JSON array of targets (e.g., \'[{"sheet_id": "abc123"}]\')',
    )

    # Simple target (single sheet with different options)
    multi_parser.add_argument(
        "--sheet-id",
        action="append",
        dest="sheet_ids",
        help="Target sheet ID (can specify multiple times)",
    )
    multi_parser.add_argument(
        "--worksheet",
        action="append",
        dest="worksheets",
        help="Worksheet name for corresponding --sheet-id",
    )

    # Processing options
    multi_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Push to sheets in parallel",
    )
    multi_parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum parallel workers (default: 4)",
    )

    # Output options
    multi_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without pushing to sheets",
    )
    multi_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output in JSON format",
    )
    multi_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    # Database overrides
    multi_parser.add_argument(
        "--db-type",
        choices=["mysql", "postgres", "sqlite", "mssql"],
        help="Database type (overrides .env)",
    )
    multi_parser.add_argument(
        "--query",
        help="SQL query (overrides .env)",
    )


@require_cli_tier("multi_sheet")
def cmd_multi_sync(args: argparse.Namespace) -> int:
    """Execute multi-sheet sync command.

    Requires BUSINESS tier or higher license.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    from mysql_to_sheets.core.multi_sheet_sync import run_multi_sheet_sync
    from mysql_to_sheets.core.sync import setup_logging

    # Reset config to pick up any overrides
    reset_config()

    # Load base config
    config = get_config()

    # Apply command-line overrides
    overrides = {}
    if args.db_type:
        overrides["db_type"] = args.db_type
    if args.query:
        overrides["sql_query"] = args.query

    if overrides:
        config = config.with_overrides(**overrides)

    # Setup logging
    if args.verbose:
        config = config.with_overrides(log_level="DEBUG")
    logger = setup_logging(config)

    # Build targets list
    targets = []

    # Option 1: Targets from JSON file
    if args.targets:
        try:
            with open(args.targets) as f:
                targets_data = json.load(f)
            targets = [SheetTarget.from_dict(t) for t in targets_data]
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading targets file: {e}")
            return 1

    # Option 2: Inline JSON
    elif args.targets_json:
        try:
            targets_data = json.loads(args.targets_json)
            targets = [SheetTarget.from_dict(t) for t in targets_data]
        except json.JSONDecodeError as e:
            print(f"Error parsing targets JSON: {e}")
            return 1

    # Option 3: Simple sheet IDs
    elif args.sheet_ids:
        worksheets = args.worksheets or []
        for i, sheet_id in enumerate(args.sheet_ids):
            worksheet = worksheets[i] if i < len(worksheets) else "Sheet1"
            targets.append(SheetTarget(sheet_id=sheet_id, worksheet_name=worksheet))

    # Option 4: Use config targets
    else:
        targets = config.multi_sheet_targets

    if not targets:
        print("Error: No targets specified. Use --targets, --targets-json, or --sheet-id")
        return 1

    # Execute multi-sheet sync
    try:
        result = run_multi_sheet_sync(
            config=config,
            targets=targets,
            logger=logger,
            dry_run=args.dry_run,
            parallel=args.parallel,
            max_workers=args.max_workers,
        )

        if args.json_output:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            if result.success:
                print("\nMulti-sheet sync completed successfully!")
                print(f"  Rows fetched: {result.total_rows_fetched}")
                print(f"  Targets:      {len(result.target_results)}")
                print("\nTarget Results:")
                for tr in result.target_results:
                    status = "OK" if tr.success else "FAILED"
                    print(f"  [{status}] {tr.target.sheet_id}/{tr.target.worksheet_name}")
                    print(f"         Rows synced: {tr.rows_synced}")
                    if tr.error:
                        print(f"         Error: {tr.error}")
            else:
                print("\nMulti-sheet sync failed!")
                if result.error:
                    print(f"Error: {result.error}")
                for tr in result.target_results:
                    if not tr.success:
                        print(f"  FAILED: {tr.target.sheet_id} - {tr.error}")

        return 0 if result.success else 1

    except Exception as e:
        if args.json_output:
            print(json.dumps({"success": False, "error": str(e)}, indent=2))
        else:
            print(f"\nError: {e}")
        return 1
