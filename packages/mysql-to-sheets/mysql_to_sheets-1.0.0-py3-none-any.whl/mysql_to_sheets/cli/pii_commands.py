"""CLI commands for PII detection and management.

Contains: pii detect, pii policy list/set, pii acknowledge commands.
"""

from __future__ import annotations

import argparse
import json
import sys

from mysql_to_sheets.cli.output import error, info, success, warning
from mysql_to_sheets.cli.utils import output_result
from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.exceptions import ConfigError, DatabaseError


def add_pii_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add PII-related command parsers.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    # Main pii command with subcommands
    pii_parser = subparsers.add_parser(
        "pii",
        help="PII detection and management commands",
    )
    pii_subparsers = pii_parser.add_subparsers(dest="pii_command", help="PII commands")

    # pii detect command
    detect_parser = pii_subparsers.add_parser(
        "detect",
        help="Detect PII in query results",
    )
    detect_parser.add_argument(
        "--query",
        dest="sql_query",
        help="SQL query to analyze (overrides .env)",
    )
    detect_parser.add_argument(
        "--db-type",
        dest="db_type",
        choices=["mysql", "postgres", "sqlite", "mssql"],
        help="Database type (overrides .env)",
    )
    detect_parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Number of rows to sample for content detection (default: 100)",
    )
    detect_parser.add_argument(
        "--confidence",
        type=float,
        default=0.7,
        help="Minimum confidence threshold for detection (default: 0.7)",
    )
    detect_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # pii policy command with subcommands
    policy_parser = pii_subparsers.add_parser(
        "policy",
        help="Manage organization PII policies",
    )
    policy_subparsers = policy_parser.add_subparsers(dest="policy_command", help="Policy commands")

    # pii policy list
    policy_list_parser = policy_subparsers.add_parser(
        "list",
        help="List organization PII policies",
    )
    policy_list_parser.add_argument(
        "--org-slug",
        dest="org_slug",
        required=True,
        help="Organization slug",
    )
    policy_list_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # pii policy set
    policy_set_parser = policy_subparsers.add_parser(
        "set",
        help="Set organization PII policy",
    )
    policy_set_parser.add_argument(
        "--org-slug",
        dest="org_slug",
        required=True,
        help="Organization slug",
    )
    policy_set_parser.add_argument(
        "--auto-detect",
        action="store_true",
        default=None,
        dest="auto_detect",
        help="Enable auto-detection for the organization",
    )
    policy_set_parser.add_argument(
        "--no-auto-detect",
        action="store_false",
        dest="auto_detect",
        help="Disable auto-detection for the organization",
    )
    policy_set_parser.add_argument(
        "--default-transform",
        dest="default_transform",
        choices=["none", "hash", "redact", "partial_mask"],
        help="Default transform for detected PII",
    )
    policy_set_parser.add_argument(
        "--require-acknowledgment",
        action="store_true",
        default=None,
        dest="require_acknowledgment",
        help="Require acknowledgment before sync",
    )
    policy_set_parser.add_argument(
        "--no-require-acknowledgment",
        action="store_false",
        dest="require_acknowledgment",
        help="Do not require acknowledgment",
    )
    policy_set_parser.add_argument(
        "--block-unacknowledged",
        action="store_true",
        default=None,
        dest="block_unacknowledged",
        help="Block sync of unacknowledged PII (ENTERPRISE only)",
    )

    # pii acknowledge command
    ack_parser = pii_subparsers.add_parser(
        "acknowledge",
        help="Acknowledge PII column for syncing",
    )
    ack_parser.add_argument(
        "--config-id",
        dest="config_id",
        type=int,
        required=True,
        help="Sync config ID",
    )
    ack_parser.add_argument(
        "--column",
        dest="column_name",
        required=True,
        help="Column name to acknowledge",
    )
    ack_parser.add_argument(
        "--transform",
        dest="transform",
        choices=["none", "hash", "redact", "partial_mask"],
        default="none",
        help="Transform to apply (default: none)",
    )
    ack_parser.add_argument(
        "--org-slug",
        dest="org_slug",
        required=True,
        help="Organization slug",
    )

    # pii preview command
    preview_parser = pii_subparsers.add_parser(
        "preview",
        help="Preview PII transforms without syncing",
    )
    preview_parser.add_argument(
        "--query",
        dest="sql_query",
        help="SQL query to analyze (overrides .env)",
    )
    preview_parser.add_argument(
        "--transform",
        dest="transform_json",
        help="Transform configuration as JSON",
    )
    preview_parser.add_argument(
        "--rows",
        type=int,
        default=5,
        help="Number of preview rows (default: 5)",
    )
    preview_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def handle_pii_command(args: argparse.Namespace) -> int:
    """Handle PII commands.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    pii_command = getattr(args, "pii_command", None)

    if pii_command == "detect":
        return _handle_detect(args)
    elif pii_command == "policy":
        return _handle_policy(args)
    elif pii_command == "acknowledge":
        return _handle_acknowledge(args)
    elif pii_command == "preview":
        return _handle_preview(args)
    else:
        error("No PII command specified. Use: pii detect, pii policy, pii acknowledge, pii preview")
        return 1


def _handle_detect(args: argparse.Namespace) -> int:
    """Handle pii detect command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    from mysql_to_sheets.core.logging_config import setup_logging
    from mysql_to_sheets.core.pii import PIITransformConfig
    from mysql_to_sheets.core.pii_detection import detect_pii_in_columns
    from mysql_to_sheets.core.sync import clean_data, fetch_data

    try:
        # Load config with overrides
        config = get_config()
        if args.sql_query:
            config = config.with_overrides(sql_query=args.sql_query)
        if args.db_type:
            config = config.with_overrides(db_type=args.db_type)

        logger = setup_logging(
            log_level="INFO",
            logger_name="mysql_to_sheets",
        )

        info(f"Fetching data from {config.db_type.upper()} database...")

        # Fetch and clean data
        headers, rows = fetch_data(config, logger)

        if not rows:
            warning("Query returned no rows")
            return 0

        cleaned_rows = clean_data(rows, logger, db_type=config.db_type)

        # Configure detection
        pii_config = PIITransformConfig(
            enabled=True,
            auto_detect=True,
            confidence_threshold=args.confidence,
            sample_size=args.sample_size,
        )

        info(f"Analyzing {len(headers)} columns (sampling {min(args.sample_size, len(rows))} rows)...")

        # Run detection
        result = detect_pii_in_columns(headers, cleaned_rows, pii_config, logger)

        # Output results
        if args.output == "json":
            output_result(result.to_dict(), output_format="json")
        else:
            if result.has_pii:
                success(f"PII detected in {len(result.columns)} column(s)")
                print()
                for col in result.columns:
                    print(f"  {col.column_name}")
                    print(f"    Category: {col.category.value}")
                    print(f"    Confidence: {col.confidence:.0%}")
                    print(f"    Detection: {col.detection_method}")
                    print(f"    Suggested: {col.suggested_transform.value}")
                    print()
            else:
                info("No PII detected")

        return 0

    except ConfigError as e:
        error(f"Configuration error: {e}")
        return 1
    except DatabaseError as e:
        error(f"Database error: {e}")
        return 1
    except (OSError, ValueError) as e:
        error(f"Error: {e}")
        return 1


def _handle_policy(args: argparse.Namespace) -> int:
    """Handle pii policy commands.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    policy_command = getattr(args, "policy_command", None)

    if policy_command == "list":
        return _handle_policy_list(args)
    elif policy_command == "set":
        return _handle_policy_set(args)
    else:
        error("No policy command specified. Use: pii policy list, pii policy set")
        return 1


def _handle_policy_list(args: argparse.Namespace) -> int:
    """Handle pii policy list command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    from mysql_to_sheets.core.config import get_config

    config = get_config()

    try:
        from mysql_to_sheets.models.pii_policies import get_pii_policy_repository

        repo = get_pii_policy_repository(config.tenant_db_path)

        # Get organization by slug
        from mysql_to_sheets.models.organizations import get_organization_repository

        org_repo = get_organization_repository(config.tenant_db_path)
        org = org_repo.get_by_slug(args.org_slug)

        if not org:
            error(f"Organization not found: {args.org_slug}")
            return 1

        policy = repo.get_by_organization(org.id)

        if args.output == "json":
            if policy:
                output_result(policy.to_dict(), output_format="json")
            else:
                output_result({"message": "No policy configured"}, output_format="json")
        else:
            if policy:
                success(f"PII Policy for {args.org_slug}")
                print()
                print(f"  Auto-detect enabled: {policy.auto_detect_enabled}")
                print(f"  Require acknowledgment: {policy.require_acknowledgment}")
                print(f"  Block unacknowledged: {policy.block_unacknowledged}")
                if policy.default_transforms:
                    print(f"  Default transforms: {json.dumps(policy.default_transforms)}")
            else:
                info("No PII policy configured for this organization")
                info("Using default settings (auto-detect off)")

        return 0

    except (ImportError, OSError) as e:
        error(f"Error accessing policies: {e}")
        return 1


def _handle_policy_set(args: argparse.Namespace) -> int:
    """Handle pii policy set command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.core.tier import Tier, check_feature_access, get_tier_from_license

    config = get_config()

    try:
        # Check tier for org-level policies
        current_tier = get_tier_from_license()
        if not check_feature_access(current_tier, "pii_org_policy"):
            error(f"Organization PII policies require BUSINESS tier or higher. Current: {current_tier.value}")
            return 1

        # Check ENTERPRISE for block_unacknowledged
        if args.block_unacknowledged and not check_feature_access(current_tier, "pii_block_unacknowledged"):
            error("Block unacknowledged requires ENTERPRISE tier")
            return 1

        from mysql_to_sheets.models.organizations import get_organization_repository
        from mysql_to_sheets.models.pii_policies import PIIPolicyModel, get_pii_policy_repository

        org_repo = get_organization_repository(config.tenant_db_path)
        org = org_repo.get_by_slug(args.org_slug)

        if not org:
            error(f"Organization not found: {args.org_slug}")
            return 1

        repo = get_pii_policy_repository(config.tenant_db_path)
        policy = repo.get_by_organization(org.id)

        if policy:
            # Update existing policy
            if args.auto_detect is not None:
                policy.auto_detect_enabled = args.auto_detect
            if args.require_acknowledgment is not None:
                policy.require_acknowledgment = args.require_acknowledgment
            if args.block_unacknowledged is not None:
                policy.block_unacknowledged = args.block_unacknowledged
            if args.default_transform:
                policy.default_transforms = {"default": args.default_transform}

            repo.update(policy)
            success(f"Updated PII policy for {args.org_slug}")
        else:
            # Create new policy
            policy = PIIPolicyModel(
                organization_id=org.id,
                auto_detect_enabled=args.auto_detect if args.auto_detect is not None else True,
                require_acknowledgment=args.require_acknowledgment if args.require_acknowledgment is not None else True,
                block_unacknowledged=args.block_unacknowledged if args.block_unacknowledged is not None else False,
                default_transforms={"default": args.default_transform} if args.default_transform else {},
            )
            repo.create(policy)
            success(f"Created PII policy for {args.org_slug}")

        return 0

    except (ImportError, OSError) as e:
        error(f"Error setting policy: {e}")
        return 1


def _handle_acknowledge(args: argparse.Namespace) -> int:
    """Handle pii acknowledge command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    from mysql_to_sheets.core.config import get_config

    config = get_config()

    try:
        from mysql_to_sheets.models.organizations import get_organization_repository
        from mysql_to_sheets.models.pii_acknowledgments import (
            PIIAcknowledgmentModel,
            get_pii_acknowledgment_repository,
        )

        org_repo = get_organization_repository(config.tenant_db_path)
        org = org_repo.get_by_slug(args.org_slug)

        if not org:
            error(f"Organization not found: {args.org_slug}")
            return 1

        ack_repo = get_pii_acknowledgment_repository(config.tenant_db_path)

        # Check if already acknowledged
        existing = ack_repo.get_for_config(args.config_id, args.column_name)
        if existing:
            info(f"Column '{args.column_name}' already acknowledged with transform: {existing.transform}")
            return 0

        # Create acknowledgment
        from datetime import datetime, timezone

        ack = PIIAcknowledgmentModel(
            sync_config_id=args.config_id,
            column_name=args.column_name,
            category="unknown",  # Will be updated on next detection
            transform=args.transform,
            acknowledged_by_user_id=None,  # TODO: Get from auth context
            acknowledged_at=datetime.now(timezone.utc),
        )
        ack_repo.create(ack)

        success(f"Acknowledged column '{args.column_name}' with transform: {args.transform}")
        return 0

    except (ImportError, OSError) as e:
        error(f"Error creating acknowledgment: {e}")
        return 1


def _handle_preview(args: argparse.Namespace) -> int:
    """Handle pii preview command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    from mysql_to_sheets.core.logging_config import setup_logging
    from mysql_to_sheets.core.pii import PIITransformConfig
    from mysql_to_sheets.core.pii_detection import detect_pii_in_columns
    from mysql_to_sheets.core.pii_transform import get_transform_preview
    from mysql_to_sheets.core.sync import clean_data, fetch_data

    try:
        config = get_config()
        if args.sql_query:
            config = config.with_overrides(sql_query=args.sql_query)

        logger = setup_logging(
            log_level="INFO",
            logger_name="mysql_to_sheets",
        )

        info(f"Fetching data from {config.db_type.upper()} database...")

        # Fetch and clean data
        headers, rows = fetch_data(config, logger)

        if not rows:
            warning("Query returned no rows")
            return 0

        cleaned_rows = clean_data(rows, logger, db_type=config.db_type)

        # Parse transform config
        transform_map = {}
        if args.transform_json:
            try:
                transform_map = json.loads(args.transform_json)
            except json.JSONDecodeError as e:
                error(f"Invalid transform JSON: {e}")
                return 1

        pii_config = PIITransformConfig(
            enabled=True,
            auto_detect=True,
            transform_map=transform_map,
        )

        # Detect PII
        detection_result = detect_pii_in_columns(headers, cleaned_rows, pii_config, logger)

        # Get preview
        preview = get_transform_preview(
            headers, cleaned_rows, pii_config, detection_result, args.rows
        )

        if args.output == "json":
            output_result(preview, output_format="json")
        else:
            if preview["transforms_applied"] > 0:
                success(f"Transform preview ({preview['transforms_applied']} columns)")
                print()
                for col_info in preview["columns"]:
                    print(f"  {col_info['column']}")
                    print(f"    Transform: {col_info['transform']}")
                    if "category" in col_info:
                        print(f"    Category: {col_info['category']}")
                        print(f"    Confidence: {col_info.get('confidence', 'N/A'):.0%}")
                    if "sample_before" in col_info:
                        print(f"    Before: {col_info['sample_before']}")
                        print(f"    After:  {col_info['sample_after']}")
                    print()
            else:
                info("No transforms to apply")

        return 0

    except ConfigError as e:
        error(f"Configuration error: {e}")
        return 1
    except DatabaseError as e:
        error(f"Database error: {e}")
        return 1
    except (OSError, ValueError) as e:
        error(f"Error: {e}")
        return 1
