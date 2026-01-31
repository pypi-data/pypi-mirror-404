"""CLI commands for sync operations.

Contains: sync, validate, test-db, test-sheets commands.
"""

from __future__ import annotations

import argparse
import json
import sys

from mysql_to_sheets.cli.output import Spinner, warning
from mysql_to_sheets.cli.tier_check import check_cli_tier
from mysql_to_sheets.cli.utils import output_result
from mysql_to_sheets.core.config import get_config, reset_config
from mysql_to_sheets.core.exceptions import ConfigError, DatabaseError, LicenseError, SheetsError
from mysql_to_sheets.core.logging_config import setup_logging
from mysql_to_sheets.core.sync import SyncService, run_sync
from mysql_to_sheets.core.tier import Tier, get_tier_from_license


def add_sync_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add sync-related command parsers.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    # Sync command
    sync_parser = subparsers.add_parser(
        "sync",
        help="Execute sync from MySQL to Google Sheets",
    )
    sync_parser.add_argument(
        "--sheet-id",
        dest="google_sheet_id",
        help="Google Sheet ID or full URL (overrides .env)",
    )
    sync_parser.add_argument(
        "--worksheet",
        dest="google_worksheet_name",
        help="Target worksheet name or full Google Sheets URL with #gid= (overrides .env)",
    )
    sync_parser.add_argument(
        "--query",
        dest="sql_query",
        help="SQL query to execute (overrides .env)",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and fetch data but don't push to Sheets",
    )
    sync_parser.add_argument(
        "--preview",
        action="store_true",
        help="Show diff with current sheet data without pushing",
    )
    sync_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging",
    )
    sync_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    sync_parser.add_argument(
        "--mode",
        choices=["replace", "append", "streaming"],
        default=None,
        help="Sync mode (default: from config or 'replace')",
    )
    sync_parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help="Chunk size for streaming mode (default: from config or 1000)",
    )
    sync_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Enable incremental sync",
    )
    sync_parser.add_argument(
        "--since",
        dest="incremental_since",
        help="Timestamp for incremental sync (ISO format)",
    )
    sync_parser.add_argument(
        "--notify",
        action="store_true",
        dest="notify",
        default=None,
        help="Send notifications (overrides config)",
    )
    sync_parser.add_argument(
        "--no-notify",
        action="store_false",
        dest="notify",
        help="Disable notifications (overrides config)",
    )
    sync_parser.add_argument(
        "--db-type",
        dest="db_type",
        choices=["mysql", "postgres"],
        help="Database type (overrides .env)",
    )
    sync_parser.add_argument(
        "--column-map",
        dest="column_map",
        help="Column rename mapping (JSON or 'old=new,old2=new2' format)",
    )
    sync_parser.add_argument(
        "--columns",
        dest="column_order",
        help="Comma-separated list of columns to include and their order",
    )
    sync_parser.add_argument(
        "--column-case",
        dest="column_case",
        choices=["none", "upper", "lower", "title"],
        help="Apply case transformation to column names",
    )
    sync_parser.add_argument(
        "--use-query",
        dest="use_query",
        help="Use a saved favorite query by name (requires --org-slug)",
    )
    sync_parser.add_argument(
        "--use-sheet",
        dest="use_sheet",
        help="Use a saved favorite sheet by name (requires --org-slug)",
    )
    sync_parser.add_argument(
        "--org-slug",
        dest="org_slug",
        help="Organization slug (required when using --use-query or --use-sheet)",
    )
    sync_parser.add_argument(
        "--create-worksheet",
        action="store_true",
        dest="create_worksheet",
        default=None,
        help="Create the worksheet if it doesn't exist (overrides config)",
    )
    sync_parser.add_argument(
        "--no-create-worksheet",
        action="store_false",
        dest="create_worksheet",
        help="Do not create the worksheet if it doesn't exist (overrides config)",
    )
    sync_parser.add_argument(
        "--no-atomic",
        action="store_false",
        dest="atomic",
        default=None,
        help="Disable atomic streaming mode (allows partial data on failure)",
    )
    sync_parser.add_argument(
        "--preserve-gid",
        action="store_true",
        dest="preserve_gid",
        default=None,
        help="Preserve worksheet GID during atomic streaming (slower but stable URLs)",
    )
    sync_parser.add_argument(
        "--schema-policy",
        dest="schema_policy",
        choices=["strict", "additive", "flexible", "notify_only"],
        default=None,
        help="Schema evolution policy (default: strict). PRO+ required for non-strict.",
    )
    sync_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        dest="yes",
        help="Skip confirmation prompt (requires PRO+ license for automation)",
    )
    sync_parser.add_argument(
        "--headless",
        action="store_true",
        dest="headless",
        help="Run in headless mode for CI/CD pipelines (requires ENTERPRISE license)",
    )
    sync_parser.add_argument(
        "--detect-pii",
        action="store_true",
        dest="detect_pii",
        default=None,
        help="Enable PII detection (scans columns for personally identifiable information)",
    )
    sync_parser.add_argument(
        "--no-detect-pii",
        action="store_false",
        dest="detect_pii",
        help="Disable PII detection",
    )
    sync_parser.add_argument(
        "--pii-transform",
        dest="pii_transform",
        help="PII transform configuration as JSON (e.g., '{\"email\": \"hash\", \"phone\": \"redact\"}')",
    )
    sync_parser.add_argument(
        "--pii-acknowledged",
        action="store_true",
        dest="pii_acknowledged",
        default=False,
        help="Acknowledge detected PII and proceed without transforms",
    )
    sync_parser.add_argument(
        "--pii-default-transform",
        dest="pii_default_transform",
        choices=["none", "hash", "redact", "partial_mask"],
        default=None,
        help="Default transform for detected PII columns",
    )
    sync_parser.add_argument(
        "--resumable",
        action="store_true",
        dest="resumable",
        default=False,
        help="Enable checkpoint/resume for large streaming syncs (preserves staging on failure)",
    )
    sync_parser.add_argument(
        "--resume-job",
        type=int,
        dest="resume_job_id",
        default=None,
        help="Resume a previously failed streaming sync by job ID",
    )
    sync_parser.add_argument(
        "--demo",
        action="store_true",
        dest="demo",
        default=False,
        help="Run sync with demo database (no external setup needed)",
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate configuration without running sync",
    )
    validate_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # Test database command
    test_db_parser = subparsers.add_parser(
        "test-db",
        help="Test database connection (MySQL or PostgreSQL)",
    )
    test_db_parser.add_argument(
        "--db-type",
        dest="db_type",
        choices=["mysql", "postgres"],
        help="Database type (overrides .env)",
    )
    test_db_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    test_db_parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Show detailed failure diagnostics with remediation hints",
    )

    # Test sheets command
    test_sheets_parser = subparsers.add_parser(
        "test-sheets",
        help="Test Google Sheets connection",
    )
    test_sheets_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    test_sheets_parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Show detailed failure diagnostics with remediation hints",
    )


def cmd_sync(args: argparse.Namespace) -> int:
    """Execute sync command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Set up logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level=log_level)

    # Load config
    reset_config()
    config = get_config()

    # Handle demo mode
    if getattr(args, "demo", False):
        from mysql_to_sheets.core.demo import create_demo_database, get_demo_db_path

        create_demo_database()
        demo_path = get_demo_db_path()

        # Apply demo overrides
        config = config.with_overrides(
            db_type="sqlite",
            db_name=str(demo_path),
            sql_query="SELECT * FROM sample_customers LIMIT 10",
        )
        args.dry_run = True  # No Google Sheets connection needed

        if args.output != "json":
            print("\n  Demo Mode: Using built-in sample database")
            print(f"  Database: {demo_path}")
            print("  Query: SELECT * FROM sample_customers LIMIT 10")
            print("  Note: --dry-run enabled (no Google Sheets needed)\n")

    # Validate license if configured
    if config.license_key:
        from mysql_to_sheets.core.license import LicenseStatus, validate_license

        license_info = validate_license(
            config.license_key,
            config.license_public_key or None,
            config.license_offline_grace_days,
        )

        if license_info.status == LicenseStatus.EXPIRED:
            expires_str = (
                license_info.expires_at.strftime("%Y-%m-%d")
                if license_info.expires_at
                else "unknown date"
            )
            output_result(
                {
                    "success": False,
                    "message": f"License expired on {expires_str}. Please renew your subscription.",
                    "error": "license_expired",
                    "code": "LICENSE_003",
                },
                args.output,
            )
            return 1

        if license_info.status == LicenseStatus.INVALID:
            output_result(
                {
                    "success": False,
                    "message": f"Invalid license key: {license_info.error}",
                    "error": "license_invalid",
                    "code": "LICENSE_002",
                },
                args.output,
            )
            return 1

        # Show warnings for expiring licenses (non-JSON output only)
        if args.output != "json":
            if license_info.status == LicenseStatus.GRACE_PERIOD:
                days_expired = (
                    -license_info.days_until_expiry if license_info.days_until_expiry else 0
                )
                warning(
                    f"License expired! Grace period ends in {config.license_offline_grace_days - days_expired} days."
                )
            elif (
                license_info.status == LicenseStatus.VALID
                and license_info.days_until_expiry is not None
                and license_info.days_until_expiry <= 7
            ):
                warning(f"License expires in {license_info.days_until_expiry} days.")

    # Check for headless mode (requires ENTERPRISE tier)
    from mysql_to_sheets.cli.main import EXIT_LICENSE, EXIT_TIER

    if getattr(args, "headless", False):
        tier = get_tier_from_license()
        if tier < Tier.ENTERPRISE:
            output_result(
                {
                    "success": False,
                    "message": "Headless mode requires ENTERPRISE license.",
                    "error": "tier_insufficient",
                    "code": "LICENSE_004",
                    "required_tier": "enterprise",
                    "current_tier": tier.value,
                    "upgrade_url": "https://mysql-to-sheets.com/pricing",
                },
                "json",  # Force JSON output for headless mode errors
            )
            return EXIT_TIER

        # In headless mode, force JSON output and set --yes
        args.output = "json"
        args.yes = True

    # Handle --yes flag confirmation bypass (requires PRO+ tier for automation)
    # Skip confirmation for dry-run and preview modes (no data is pushed)
    is_push_operation = not args.dry_run and not args.preview

    if is_push_operation and getattr(args, "yes", False):
        tier = get_tier_from_license()
        if tier < Tier.PRO:
            output_result(
                {
                    "success": False,
                    "message": "The --yes flag requires PRO license or higher for automated syncs.",
                    "error": "tier_insufficient",
                    "code": "LICENSE_004",
                    "required_tier": "pro",
                    "current_tier": tier.value,
                    "remediation": "Remove --yes to use interactive confirmation, or upgrade to PRO.",
                },
                args.output,
            )
            return EXIT_TIER

    # Handle favorite lookups if --use-query or --use-sheet is specified
    favorite_query = None
    favorite_sheet = None

    if args.use_query or args.use_sheet:
        if not args.org_slug:
            output_result(
                {
                    "success": False,
                    "message": "--org-slug is required when using --use-query or --use-sheet",
                },
                args.output,
            )
            return 1

        from mysql_to_sheets.cli.utils import get_organization_id, get_tenant_db_path

        db_path = get_tenant_db_path()
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

        if args.use_query:
            from mysql_to_sheets.models.favorites import get_favorite_query_repository

            query_repo = get_favorite_query_repository(db_path)
            favorite_query = query_repo.get_by_name(args.use_query, organization_id=org_id)
            if not favorite_query:
                output_result(
                    {
                        "success": False,
                        "message": f"Favorite query '{args.use_query}' not found",
                    },
                    args.output,
                )
                return 1

        if args.use_sheet:
            from mysql_to_sheets.models.favorites import get_favorite_sheet_repository

            sheet_repo = get_favorite_sheet_repository(db_path)
            favorite_sheet = sheet_repo.get_by_name(args.use_sheet, organization_id=org_id)
            if not favorite_sheet:
                output_result(
                    {
                        "success": False,
                        "message": f"Favorite sheet '{args.use_sheet}' not found",
                    },
                    args.output,
                )
                return 1

    # Apply overrides
    overrides = {}

    # Apply favorite query if specified (before explicit overrides)
    if favorite_query:
        overrides["sql_query"] = favorite_query.sql_query

    # Apply favorite sheet if specified (before explicit overrides)
    if favorite_sheet:
        overrides["google_sheet_id"] = favorite_sheet.sheet_id
        overrides["google_worksheet_name"] = favorite_sheet.default_worksheet

    # Explicit CLI arguments override favorites
    if args.google_sheet_id:
        from mysql_to_sheets.core.sheets_utils import parse_sheet_id

        try:
            overrides["google_sheet_id"] = parse_sheet_id(args.google_sheet_id)
        except ValueError as e:
            output_result({"success": False, "message": str(e)}, args.output)
            return 1
    if args.google_worksheet_name:
        overrides["google_worksheet_name"] = args.google_worksheet_name
    if args.sql_query:
        overrides["sql_query"] = args.sql_query
    # Check tier requirements for premium features
    if args.mode == "streaming":
        allowed, tier_error = check_cli_tier("streaming_sync")
        if not allowed:
            assert tier_error is not None
            output_result(tier_error, args.output)
            return 1

    if args.incremental:
        allowed, tier_error = check_cli_tier("incremental_sync")
        if not allowed:
            assert tier_error is not None
            output_result(tier_error, args.output)
            return 1

    if args.mode:
        overrides["sync_mode"] = args.mode
    if args.chunk_size is not None:
        # Validate chunk-size bounds to prevent crashes or infinite loops
        if args.chunk_size <= 0:
            output_result(
                {
                    "success": False,
                    "message": f"--chunk-size must be a positive integer, got {args.chunk_size}",
                    "error": "invalid_chunk_size",
                    "code": "CONFIG_102",
                    "remediation": "Use a value between 100 and 10000 for optimal performance.",
                },
                args.output,
            )
            return 1
        if args.chunk_size > 100000:
            output_result(
                {
                    "success": False,
                    "message": f"--chunk-size {args.chunk_size} is too large (max 100000)",
                    "error": "invalid_chunk_size",
                    "code": "CONFIG_102",
                    "remediation": "Use a value between 100 and 10000 for optimal performance.",
                },
                args.output,
            )
            return 1
        overrides["streaming_chunk_size"] = args.chunk_size
    if args.incremental:
        overrides["incremental_enabled"] = args.incremental
    if args.incremental_since:
        overrides["incremental_since"] = args.incremental_since
    if args.notify is not None:
        overrides["notify_on_success"] = args.notify
        overrides["notify_on_failure"] = args.notify
    if args.db_type:
        overrides["db_type"] = args.db_type

    # Column mapping overrides - requires PRO tier
    if args.column_map or args.column_order or args.column_case:
        allowed, tier_error = check_cli_tier("column_mapping")
        if not allowed:
            assert tier_error is not None
            output_result(tier_error, args.output)
            return 1

    if args.column_map:
        overrides["column_mapping_enabled"] = args.column_map
        # Parse column_map - could be JSON or simple format
        if args.column_map.startswith("{"):
            overrides["column_mapping"] = args.column_map
        else:
            # Convert old=new,old2=new2 to JSON
            mapping = {}
            for pair in args.column_map.split(","):
                if "=" in pair:
                    old, new = pair.split("=", 1)
                    mapping[old.strip()] = new.strip()
            overrides["column_mapping"] = json.dumps(mapping)

    if args.column_order:
        overrides["column_mapping_enabled"] = args.column_order
        overrides["column_order"] = args.column_order

    if args.column_case:
        overrides["column_mapping_enabled"] = args.column_case
        overrides["column_case"] = args.column_case

    # Schema policy tier check - non-strict policies require PRO tier
    schema_policy = args.schema_policy
    if schema_policy and schema_policy != "strict":
        from mysql_to_sheets.core.schema_evolution import get_policy_tier_requirement

        feature_key = get_policy_tier_requirement(schema_policy)
        if feature_key:
            allowed, tier_error = check_cli_tier(feature_key)
            if not allowed:
                assert tier_error is not None
                output_result(tier_error, args.output)
                return EXIT_TIER

    if overrides:
        config = config.with_overrides(**overrides)

    # Interactive confirmation for FREE tier users (unless --yes or non-push operation)
    # This prevents unattended/cron automation without a PRO license
    if is_push_operation and not getattr(args, "yes", False) and args.output != "json":
        tier = get_tier_from_license()
        # Show sync summary
        print("\n  Sync Summary:")
        print(f"    Sheet ID:   {config.google_sheet_id[:40]}...")
        print(f"    Worksheet:  {config.google_worksheet_name}")
        print(f"    Mode:       {config.sync_mode}")
        if tier < Tier.PRO:
            print(f"\n  Tier: FREE (Use --yes with PRO license to skip this prompt)")
        print()

        try:
            response = input("  Push data to Google Sheets? [y/N]: ").strip().lower()
            if response not in ("y", "yes"):
                output_result(
                    {
                        "success": False,
                        "message": "Sync cancelled by user.",
                        "cancelled": True,
                    },
                    args.output,
                )
                return 0  # User chose to cancel, not an error
        except (EOFError, KeyboardInterrupt):
            print("\n")
            output_result(
                {
                    "success": False,
                    "message": "Sync cancelled.",
                    "cancelled": True,
                },
                args.output,
            )
            return 0

    try:
        # Handle --resume-job: Resume from checkpoint instead of starting fresh
        resume_job_id = getattr(args, "resume_job_id", None)
        if resume_job_id is not None:
            from mysql_to_sheets.cli.utils import get_tenant_db_path
            from mysql_to_sheets.core.atomic_streaming import (
                AtomicStreamingConfig,
                resume_atomic_streaming_sync,
            )
            from mysql_to_sheets.models.checkpoints import get_checkpoint_repository

            # Load checkpoint
            db_path = get_tenant_db_path()
            checkpoint_repo = get_checkpoint_repository(db_path)
            checkpoint = checkpoint_repo.get_checkpoint(resume_job_id)

            if not checkpoint:
                output_result(
                    {
                        "success": False,
                        "message": f"No checkpoint found for job {resume_job_id}",
                        "error": "checkpoint_not_found",
                    },
                    args.output,
                )
                return 1

            # Show spinner for resume
            if args.output != "json":
                spinner = Spinner(
                    f"Resuming sync from checkpoint ({checkpoint.rows_pushed} rows)"
                )
                spinner.start()
            else:
                spinner = None

            preserve_gid = args.preserve_gid if args.preserve_gid is not None else False

            ac = AtomicStreamingConfig(
                chunk_size=config.streaming_chunk_size or 1000,
                preserve_gid=preserve_gid,
                resumable=True,
            )

            from mysql_to_sheets.core.atomic_streaming import AtomicStreamingResult

            resume_result = resume_atomic_streaming_sync(
                config,
                checkpoint,
                atomic_config=ac,
                job_id=resume_job_id,
            )

            if spinner:
                if resume_result.swap_successful:
                    spinner.stop(
                        f"Resumed and synced {resume_result.total_rows} rows",
                        success_status=True,
                    )
                else:
                    spinner.stop("Resume failed", success_status=False)

            output_result(
                {
                    "success": resume_result.swap_successful,
                    "rows_synced": resume_result.total_rows,
                    "message": f"Resumed from checkpoint. {resume_result.total_rows} rows synced.",
                    "resumed_from_chunk": checkpoint.chunks_completed,
                    "resumed_from_rows": checkpoint.rows_pushed,
                },
                args.output,
            )
            return 0 if resume_result.swap_successful else 1

        # Show spinner for non-JSON output during sync
        if args.output != "json" and not args.dry_run:
            spinner = Spinner("Syncing data to Google Sheets")
            spinner.start()
        else:
            spinner = None

        # Determine atomic mode from args or config
        atomic = args.atomic if args.atomic is not None else True
        preserve_gid = args.preserve_gid if args.preserve_gid is not None else False
        resumable = getattr(args, "resumable", False)

        # Build PII config from CLI args
        pii_config = None
        pii_acknowledged = getattr(args, "pii_acknowledged", False)
        detect_pii = getattr(args, "detect_pii", None)

        pii_transform_arg = getattr(args, "pii_transform", None)
        pii_default = getattr(args, "pii_default_transform", None)

        if pii_transform_arg or pii_default or detect_pii:
            from mysql_to_sheets.core.pii import PIITransform, PIITransformConfig

            transform_map = {}
            if pii_transform_arg:
                # EC-54: Separate JSON syntax errors from invalid transform values
                try:
                    raw_map = json.loads(pii_transform_arg)
                except json.JSONDecodeError as e:
                    output_result(
                        {"success": False, "error": f"Invalid JSON syntax in --pii-transform: {e}"},
                        args.output,
                    )
                    return 1

                for col, transform in raw_map.items():
                    try:
                        transform_map[col] = PIITransform.from_string(transform)
                    except ValueError:
                        valid = ", ".join(t.value for t in PIITransform)
                        output_result(
                            {
                                "success": False,
                                "error": f"Invalid PII transform '{transform}' for column '{col}'. "
                                f"Valid values: {valid}",
                                "code": "PII_005",
                            },
                            args.output,
                        )
                        return 1

            default_transform = PIITransform.HASH
            if pii_default:
                default_transform = PIITransform.from_string(pii_default)

            pii_config = PIITransformConfig(
                enabled=True,
                auto_detect=detect_pii if detect_pii is not None else bool(transform_map),
                transform_map=transform_map,
                default_transform=default_transform,
            )

        result = run_sync(
            config,
            dry_run=args.dry_run,
            preview=args.preview,
            create_worksheet=args.create_worksheet,
            atomic=atomic,
            preserve_gid=preserve_gid,
            schema_policy=schema_policy,
            pii_config=pii_config,
            pii_acknowledged=pii_acknowledged,
            detect_pii=detect_pii,
            resumable=resumable,
        )

        if spinner:
            if result.success:
                spinner.stop(f"Synced {result.rows_synced} rows", success_status=True)
            else:
                spinner.stop(result.error or "Sync failed", success_status=False)

        data = {
            "success": result.success,
            "rows_synced": result.rows_synced,
            "columns": result.columns,
            "headers": result.headers,
            "message": result.message,
            "error": result.error,
            "preview": result.preview,
        }

        if result.diff:
            data["diff"] = {
                "has_changes": result.diff.has_changes,
                "sheet_row_count": result.diff.sheet_row_count,
                "query_row_count": result.diff.query_row_count,
                "rows_to_add": result.diff.rows_to_add,
                "rows_to_remove": result.diff.rows_to_remove,
                "rows_unchanged": result.diff.rows_unchanged,
                "header_changes": {
                    "added": result.diff.header_changes.added,
                    "removed": result.diff.header_changes.removed,
                    "reordered": result.diff.header_changes.reordered,
                },
            }

        if result.schema_changes:
            data["schema_changes"] = result.schema_changes

        # Increment use counts for favorites if sync was successful (and not dry-run/preview)
        if result.success and not args.dry_run and not args.preview:
            if favorite_query:
                from mysql_to_sheets.cli.utils import get_organization_id, get_tenant_db_path
                from mysql_to_sheets.models.favorites import get_favorite_query_repository

                db_path = get_tenant_db_path()
                org_id = get_organization_id(args.org_slug, db_path)
                if org_id and favorite_query.id is not None:
                    query_repo = get_favorite_query_repository(db_path)
                    query_repo.increment_use_count(favorite_query.id, org_id)

            if favorite_sheet:
                from mysql_to_sheets.cli.utils import get_organization_id, get_tenant_db_path
                from mysql_to_sheets.models.favorites import get_favorite_sheet_repository

                db_path = get_tenant_db_path()
                org_id = get_organization_id(args.org_slug, db_path)
                if org_id and favorite_sheet.id is not None:
                    sheet_repo = get_favorite_sheet_repository(db_path)
                    sheet_repo.increment_use_count(favorite_sheet.id, org_id)

        output_result(data, args.output)
        return 0 if result.success else 1

    except (ConfigError, DatabaseError, SheetsError, LicenseError) as e:
        from mysql_to_sheets.cli.main import (
            EXIT_AUTH,
            EXIT_CONFIG,
            EXIT_DATABASE,
            EXIT_LICENSE,
            EXIT_SHEETS,
        )

        output_result(
            {
                "success": False,
                "message": e.message,
                "error": e.message,
                "code": e.code,
                "category": e.category.value if e.category else None,
                "remediation": e.remediation,
            },
            args.output,
        )
        exit_code_map: dict[type, int] = {
            ConfigError: EXIT_CONFIG,
            DatabaseError: EXIT_DATABASE,
            SheetsError: EXIT_SHEETS,
            LicenseError: EXIT_LICENSE,
        }
        return exit_code_map.get(type(e), EXIT_AUTH)


def cmd_validate(args: argparse.Namespace) -> int:
    """Execute validate command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    reset_config()
    config = get_config()

    errors = config.validate()

    if errors:
        output_result(
            {
                "success": False,
                "message": "Configuration is invalid",
                "errors": errors,
            },
            args.output,
        )
        return 1

    output_result(
        {
            "success": True,
            "message": "Configuration is valid",
        },
        args.output,
    )
    return 0


def cmd_test_db(args: argparse.Namespace) -> int:
    """Execute test-db command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    reset_config()
    config = get_config()

    if args.db_type:
        config = config.with_overrides(db_type=args.db_type)

    service = SyncService(config)

    # Show spinner for non-JSON output
    if args.output != "json":
        spinner = Spinner(f"Connecting to {config.db_type} database")
        spinner.start()
    else:
        spinner = None

    try:
        service.test_database_connection()

        if spinner:
            spinner.stop(f"Connected to {config.db_host}/{config.db_name}", success_status=True)

        output_result(
            {
                "success": True,
                "message": f"Successfully connected to {config.db_type} database",
                "host": config.db_host,
                "database": config.db_name,
            },
            args.output,
        )
        return 0
    except DatabaseError as e:
        from mysql_to_sheets.cli.main import EXIT_DATABASE

        if spinner:
            spinner.stop(f"Connection failed: {e.message}", success_status=False)
        result = {
            "success": False,
            "message": f"Failed to connect to database: {e.message}",
            "error": e.message,
            "code": e.code,
            "category": e.category.value if e.category else None,
            "remediation": e.remediation,
        }

        # Enhanced diagnostics when --diagnose flag is used
        if getattr(args, "diagnose", False) and args.output == "text":
            print("\nDiagnostic Details:")
            print("-" * 40)
            print(f"Database Type: {config.db_type}")
            print(f"Host: {config.db_host}")
            print(f"Port: {config.db_port}")
            print(f"Database: {config.db_name}")
            print(f"User: {config.db_user}")
            print(f"\nError Code: {e.code}")
            print(f"Category: {e.category.value if e.category else 'unknown'}")

            # Provide specific guidance based on error
            if e.code:
                from mysql_to_sheets.core.exceptions import ErrorCode

                print("\nChecklist:")
                if e.code == ErrorCode.DB_CONNECTION_REFUSED:
                    print("  1. Verify database server is running")
                    print(
                        f"  2. Test connectivity: telnet {config.db_host} {config.db_port}"
                    )
                    print("  3. Check firewall rules allow connections")
                    print("  4. Verify DB_HOST and DB_PORT in .env")
                elif e.code == ErrorCode.DB_AUTH_FAILED:
                    print("  1. Verify DB_USER in .env is correct")
                    print("  2. Verify DB_PASSWORD in .env is correct")
                    print(f"  3. Check grants: SHOW GRANTS FOR '{config.db_user}'@'%'")
                    print("  4. Ensure user can connect from this host")
                elif e.code == ErrorCode.DB_NOT_FOUND:
                    print("  1. Verify DB_NAME in .env matches an existing database")
                    print("  2. List databases: SHOW DATABASES")
                    print("  3. Check user has access to this database")
                elif e.code == ErrorCode.DB_TIMEOUT:
                    print("  1. Check database server load and responsiveness")
                    print("  2. Test network latency to database host")
                    print("  3. Increase DB_CONNECT_TIMEOUT in .env")
                else:
                    print(f"  1. Review error: {e.message}")
                    print(f"  2. {e.remediation}")
            print()
            return EXIT_DATABASE

        output_result(result, args.output)
        return EXIT_DATABASE


def cmd_test_sheets(args: argparse.Namespace) -> int:
    """Execute test-sheets command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    reset_config()
    config = get_config()

    service = SyncService(config)

    # Show spinner for non-JSON output
    if args.output != "json":
        spinner = Spinner("Connecting to Google Sheets")
        spinner.start()
    else:
        spinner = None

    try:
        service.test_sheets_connection()

        if spinner:
            spinner.stop(
                f"Connected to sheet {config.google_sheet_id[:15]}...", success_status=True
            )

        result = {
            "success": True,
            "message": "Successfully connected to Google Sheets",
            "sheet_id": config.google_sheet_id,
            "worksheet": config.google_worksheet_name,
        }

        # Enhanced output when --diagnose flag is used
        if getattr(args, "diagnose", False) and args.output == "text":
            # Get service account email
            import json

            sa_email = None
            try:
                with open(config.service_account_file) as f:
                    sa_data = json.load(f)
                    sa_email = sa_data.get("client_email")
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            print("\nConnection Details:")
            print("-" * 40)
            print(f"Sheet ID: {config.google_sheet_id}")
            print(f"Worksheet: {config.google_worksheet_name}")
            print(f"Service Account: {sa_email or 'unknown'}")
            print(f"Credentials file: {config.service_account_file}")
            print("\nStatus: Connected successfully")
            return 0

        output_result(result, args.output)
        return 0
    except SheetsError as e:
        from mysql_to_sheets.cli.main import EXIT_SHEETS

        if spinner:
            spinner.stop(f"Connection failed: {e.message}", success_status=False)

        result = {
            "success": False,
            "message": f"Failed to connect to Google Sheets: {e.message}",
            "error": e.message,
            "code": e.code,
            "category": e.category.value if e.category else None,
            "remediation": e.remediation,
        }

        # Enhanced diagnostics when --diagnose flag is used
        if getattr(args, "diagnose", False) and args.output == "text":
            import json

            print("\nDiagnostic Details:")
            print("-" * 40)
            print(f"Sheet ID: {config.google_sheet_id}")
            print(f"Worksheet: {config.google_worksheet_name}")
            print(f"Credentials file: {config.service_account_file}")

            # Try to get service account email
            sa_email = None
            try:
                with open(config.service_account_file) as f:
                    sa_data = json.load(f)
                    sa_email = sa_data.get("client_email")
                    print(f"Service Account: {sa_email}")
            except FileNotFoundError:
                print(f"Service Account: FILE NOT FOUND at {config.service_account_file}")
            except json.JSONDecodeError:
                print(f"Service Account: INVALID JSON in {config.service_account_file}")

            print(f"\nError Code: {e.code}")
            print(f"Category: {e.category.value if e.category else 'unknown'}")

            # Provide specific guidance based on error
            if e.code:
                from mysql_to_sheets.core.exceptions import ErrorCode

                print("\nChecklist:")
                if e.code == ErrorCode.SHEETS_NOT_FOUND:
                    print("  1. Get sheet ID from URL: docs.google.com/spreadsheets/d/<SHEET_ID>/")
                    print("  2. Verify GOOGLE_SHEET_ID in .env matches")
                    print("  3. Confirm spreadsheet has not been deleted")
                elif e.code == ErrorCode.SHEETS_PERMISSION_DENIED:
                    if sa_email:
                        print("  1. Open the Google Sheet in your browser")
                        print(f"  2. Click 'Share' and add: {sa_email}")
                        print("  3. Set permission to 'Editor'")
                        print("  4. Re-run: mysql-to-sheets test-sheets --diagnose")
                    else:
                        print("  1. Open service_account.json and find 'client_email'")
                        print("  2. Share the Google Sheet with that email as Editor")
                        print("  3. Re-run: mysql-to-sheets test-sheets --diagnose")
                elif e.code == ErrorCode.SHEETS_AUTH_FAILED:
                    print("  1. Verify SERVICE_ACCOUNT_FILE path in .env")
                    print("  2. Re-download JSON from Google Cloud Console if needed")
                    print("  3. Ensure Google Sheets API is enabled in your GCP project")
                elif e.code == ErrorCode.SHEETS_RATE_LIMITED:
                    print("  1. Wait 60 seconds before retrying")
                    print("  2. Reduce sync frequency if this recurs")
                    print("  3. Check quota: https://console.cloud.google.com/apis/")
                else:
                    print(f"  1. Review error: {e.message}")
                    print(f"  2. {e.remediation}")
            print()
            return EXIT_SHEETS

        output_result(result, args.output)
        return EXIT_SHEETS
