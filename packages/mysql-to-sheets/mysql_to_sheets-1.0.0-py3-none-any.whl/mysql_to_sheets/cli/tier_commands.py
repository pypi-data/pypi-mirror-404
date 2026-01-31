"""CLI commands for tier management.

Provides commands to view tier status, usage, and limits:
- tier status: View current tier and limits
- tier usage: View current usage against limits
- tier features: List features available in each tier
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from mysql_to_sheets.cli.utils import get_organization_id, get_tenant_db_path
from mysql_to_sheets.core.exceptions import SyncError
from mysql_to_sheets.core.tier import (
    FEATURE_TIERS,
    TIER_LIMITS,
    Tier,
    get_tier_display_info,
)


def add_tier_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add tier subparsers to the main parser.

    Args:
        subparsers: Subparsers action from main parser.
    """
    tier_parser = subparsers.add_parser(
        "tier",
        help="Manage subscription tiers and view usage",
        description="View tier status, limits, and feature availability",
    )
    tier_subparsers = tier_parser.add_subparsers(dest="tier_command", help="Tier commands")

    # tier status
    status_parser = tier_subparsers.add_parser(
        "status",
        help="View current tier and limits",
        description="Display the current tier and resource limits for an organization",
    )
    status_parser.add_argument(
        "--org-slug",
        help="Organization slug (uses default if not specified)",
    )
    status_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output in JSON format",
    )

    # tier usage
    usage_parser = tier_subparsers.add_parser(
        "usage",
        help="View current usage against limits",
        description="Display current resource usage compared to tier limits",
    )
    usage_parser.add_argument(
        "--org-slug",
        help="Organization slug (uses default if not specified)",
    )
    usage_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output in JSON format",
    )

    # tier features
    features_parser = tier_subparsers.add_parser(
        "features",
        help="List features available in each tier",
        description="Display all features and their required tiers",
    )
    features_parser.add_argument(
        "--tier",
        choices=["free", "pro", "business", "enterprise"],
        help="Filter features for a specific tier",
    )
    features_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output in JSON format",
    )

    # tier compare
    compare_parser = tier_subparsers.add_parser(
        "compare",
        help="Compare tier limits",
        description="Compare limits and features between tiers",
    )
    compare_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output in JSON format",
    )


def handle_tier_command(args: argparse.Namespace) -> int:
    """Handle tier commands.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    if not hasattr(args, "tier_command") or not args.tier_command:
        print("Usage: mysql-to-sheets tier <command>")
        print("\nCommands:")
        print("  status    View current tier and limits")
        print("  usage     View current usage against limits")
        print("  features  List features available in each tier")
        print("  compare   Compare tier limits")
        return 0

    command_handlers = {
        "status": cmd_tier_status,
        "usage": cmd_tier_usage,
        "features": cmd_tier_features,
        "compare": cmd_tier_compare,
    }

    handler = command_handlers.get(args.tier_command)
    if handler:
        return handler(args)

    print(f"Unknown tier command: {args.tier_command}")
    return 1


def cmd_tier_status(args: argparse.Namespace) -> int:
    """Show tier status for an organization.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    try:
        db_path = get_tenant_db_path()
        org_slug = getattr(args, "org_slug", None) or ""
        org_id = get_organization_id(org_slug, db_path)

        if org_id is None:
            print("Error: Organization not found. Use --org-slug to specify.")
            return 1

        from mysql_to_sheets.models.organizations import get_organization_repository

        repo = get_organization_repository(db_path)
        org = repo.get_by_id(org_id)

        if org is None:
            print(f"Error: Organization with ID {org_id} not found")
            return 1

        tier_info = get_tier_display_info(org.tier)
        tier_info["organization"] = {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
        }

        if getattr(args, "json_output", False):
            print(json.dumps(tier_info, indent=2))
        else:
            print(f"\nOrganization: {org.name} ({org.slug})")
            print(f"Subscription Tier: {tier_info['name']}")
            print("\nResource Limits:")
            print(f"  Configs:     {tier_info['limits']['configs']}")
            print(f"  Users:       {tier_info['limits']['users']}")
            print(f"  History:     {tier_info['limits']['history_days']} days")
            print(f"  Schedules:   {tier_info['limits']['schedules']}")
            print(f"  Webhooks:    {tier_info['limits']['webhooks']}")
            print(f"  API Rate:    {tier_info['limits']['api_requests_per_minute']} req/min")

        return 0

    except SyncError as e:
        print(f"Error: {e.message}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_tier_usage(args: argparse.Namespace) -> int:
    """Show current usage against tier limits.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    try:
        db_path = get_tenant_db_path()
        org_slug = getattr(args, "org_slug", None) or ""
        org_id = get_organization_id(org_slug, db_path)

        if org_id is None:
            print("Error: Organization not found. Use --org-slug to specify.")
            return 1

        from mysql_to_sheets.models.organizations import get_organization_repository

        repo = get_organization_repository(db_path)
        org = repo.get_by_id(org_id)

        if org is None:
            print(f"Error: Organization with ID {org_id} not found")
            return 1

        limits = org.tier_limits

        # Get current counts (try to import repositories, handle missing gracefully)
        usage: dict[str, Any] = {
            "configs": {"used": 0, "limit": limits.max_configs},
            "users": {"used": 0, "limit": limits.max_users},
            "schedules": {"used": 0, "limit": limits.max_schedules},
            "webhooks": {"used": 0, "limit": limits.max_webhooks},
        }

        # Try to get actual counts
        try:
            from mysql_to_sheets.models.sync_configs import get_sync_config_repository

            config_repo = get_sync_config_repository(db_path)
            usage["configs"]["used"] = config_repo.count(org_id)
        except Exception:
            pass

        try:
            from mysql_to_sheets.models.users import get_user_repository

            user_repo = get_user_repository(db_path)
            usage["users"]["used"] = user_repo.count(org_id)
        except Exception:
            pass

        try:
            from mysql_to_sheets.core.scheduler import get_schedule_repository

            schedule_repo = get_schedule_repository(db_path)
            usage["schedules"]["used"] = len(schedule_repo.get_all())
        except Exception:
            pass

        try:
            from mysql_to_sheets.models.webhooks import get_webhook_repository

            webhook_repo = get_webhook_repository(db_path)
            usage["webhooks"]["used"] = len(webhook_repo.get_all_subscriptions(org_id))
        except Exception:
            pass

        result = {
            "organization": {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
            },
            "tier": org.tier.value,
            "usage": usage,
        }

        if getattr(args, "json_output", False):
            print(json.dumps(result, indent=2))
        else:
            print(f"\nOrganization: {org.name} ({org.slug})")
            print(f"Tier: {org.tier.value.title()}")
            print("\nResource Usage:")
            for resource, data in usage.items():
                limit_str = str(data["limit"]) if data["limit"] is not None else "Unlimited"
                pct = ""
                if data["limit"] is not None and data["limit"] > 0:
                    pct = f" ({data['used'] * 100 // data['limit']}%)"
                print(f"  {resource.title():12} {data['used']:4} / {limit_str:>10}{pct}")

        return 0

    except SyncError as e:
        print(f"Error: {e.message}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_tier_features(args: argparse.Namespace) -> int:
    """List features available in each tier.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    tier_filter = args.tier.lower() if args.tier else None

    # Group features by tier
    features_by_tier: dict[str, list[str]] = {
        "free": [],
        "pro": [],
        "business": [],
        "enterprise": [],
    }

    for feature, tier in FEATURE_TIERS.items():
        features_by_tier[tier.value].append(feature)

    result = {
        "tiers": {
            tier: {
                "features": sorted(features),
                "limits": {
                    "configs": TIER_LIMITS[Tier(tier)].max_configs,
                    "users": TIER_LIMITS[Tier(tier)].max_users,
                },
            }
            for tier, features in features_by_tier.items()
            if tier_filter is None or tier == tier_filter
        }
    }

    if getattr(args, "json_output", False):
        print(json.dumps(result, indent=2))
    else:
        print("\nFeatures by Tier:")
        print("=" * 60)
        for tier_name in ["free", "pro", "business", "enterprise"]:
            if tier_filter and tier_name != tier_filter:
                continue

            features = sorted(features_by_tier[tier_name])
            tier_obj = Tier(tier_name)
            limits = TIER_LIMITS[tier_obj]

            print(f"\n{tier_name.upper()} TIER")
            print("-" * 40)
            print(
                f"Limits: {limits.max_configs or 'Unlimited'} configs, "
                f"{limits.max_users or 'Unlimited'} users"
            )
            print("Features:")
            for feature in features:
                print(f"  - {feature.replace('_', ' ').title()}")

    return 0


def cmd_tier_compare(args: argparse.Namespace) -> int:
    """Compare all tier limits.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    comparison: dict[str, dict[str, Any]] = {}

    for tier in Tier:
        limits = TIER_LIMITS[tier]
        comparison[tier.value] = {
            "configs": limits.max_configs if limits.max_configs is not None else "Unlimited",
            "users": limits.max_users if limits.max_users is not None else "Unlimited",
            "history_days": limits.history_days if limits.history_days is not None else "Unlimited",
            "schedules": limits.max_schedules if limits.max_schedules is not None else "Unlimited",
            "webhooks": limits.max_webhooks if limits.max_webhooks is not None else "Unlimited",
            "api_rate": limits.api_requests_per_minute,
            "snapshots": limits.snapshot_retention_count
            if limits.snapshot_retention_count is not None
            else "Unlimited",
            "audit_days": limits.audit_retention_days
            if limits.audit_retention_days is not None
            else "Unlimited",
        }

    if getattr(args, "json_output", False):
        print(json.dumps({"tiers": comparison}, indent=2))
    else:
        print("\nTier Comparison")
        print("=" * 80)
        print(f"{'Resource':<15} {'Free':>12} {'Pro':>12} {'Business':>12} {'Enterprise':>12}")
        print("-" * 80)

        resources = [
            ("configs", "Configs"),
            ("users", "Users"),
            ("history_days", "History Days"),
            ("schedules", "Schedules"),
            ("webhooks", "Webhooks"),
            ("api_rate", "API Rate/min"),
            ("snapshots", "Snapshots"),
            ("audit_days", "Audit Days"),
        ]

        for key, label in resources:
            values = [str(comparison[tier.value][key]) for tier in Tier]
            print(f"{label:<15} {values[0]:>12} {values[1]:>12} {values[2]:>12} {values[3]:>12}")

    return 0
