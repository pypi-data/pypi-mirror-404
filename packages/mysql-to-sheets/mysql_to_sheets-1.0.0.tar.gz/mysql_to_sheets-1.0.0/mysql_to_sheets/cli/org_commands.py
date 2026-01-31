"""CLI commands for organization management."""

from __future__ import annotations

import argparse
import json
import re
import secrets
from typing import Any

from mysql_to_sheets.cli.utils import (
    ensure_data_dir,
    get_tenant_db_path,
    output_org_result,
)
from mysql_to_sheets.models.organizations import (
    Organization,
    OrganizationRepository,
    get_organization_repository,
)
from mysql_to_sheets.models.users import (
    get_user_repository,
)


def slugify(name: str) -> str:
    """Convert organization name to URL-safe slug.

    Args:
        name: Organization name.

    Returns:
        URL-safe slug.
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    suffix = secrets.token_hex(4)
    return f"{slug}-{suffix}"


def output_result(data: dict[str, Any], format: str) -> None:
    """Output result in the specified format.

    Args:
        data: Result data dictionary.
        format: Output format ('text' or 'json').
    """
    output_org_result(data, format)


def add_org_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add organization management subcommands.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    org_parser = subparsers.add_parser(
        "org",
        help="Manage organizations (multi-tenant)",
    )
    org_subparsers = org_parser.add_subparsers(
        dest="org_command",
        help="Organization commands",
    )

    # org create
    org_create = org_subparsers.add_parser(
        "create",
        help="Create a new organization",
    )
    org_create.add_argument(
        "--name",
        required=True,
        help="Organization display name",
    )
    org_create.add_argument(
        "--slug",
        help="URL-safe identifier (auto-generated if not provided)",
    )
    org_create.add_argument(
        "--tier",
        default="free",
        choices=["free", "pro", "enterprise"],
        help="Subscription tier (default: free)",
    )
    org_create.add_argument(
        "--max-users",
        type=int,
        default=5,
        help="Maximum number of users (default: 5)",
    )
    org_create.add_argument(
        "--max-configs",
        type=int,
        default=10,
        help="Maximum number of sync configs (default: 10)",
    )
    org_create.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # org list
    org_list = org_subparsers.add_parser(
        "list",
        help="List all organizations",
    )
    org_list.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include inactive organizations",
    )
    org_list.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of organizations to list",
    )
    org_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # org get
    org_get = org_subparsers.add_parser(
        "get",
        help="Get organization details",
    )
    org_get.add_argument(
        "--slug",
        required=True,
        help="Organization slug",
    )
    org_get.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # org update
    org_update = org_subparsers.add_parser(
        "update",
        help="Update an organization",
    )
    org_update.add_argument(
        "--slug",
        required=True,
        help="Organization slug to update",
    )
    org_update.add_argument(
        "--name",
        help="New organization name",
    )
    org_update.add_argument(
        "--tier",
        choices=["free", "pro", "enterprise"],
        help="New subscription tier",
    )
    org_update.add_argument(
        "--max-users",
        type=int,
        help="New maximum users limit",
    )
    org_update.add_argument(
        "--max-configs",
        type=int,
        help="New maximum configs limit",
    )
    org_update.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # org delete
    org_delete = org_subparsers.add_parser(
        "delete",
        help="Delete (deactivate) an organization",
    )
    org_delete.add_argument(
        "--slug",
        required=True,
        help="Organization slug to delete",
    )
    org_delete.add_argument(
        "--force",
        action="store_true",
        help="Force delete even if organization has users",
    )
    org_delete.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def handle_org_command(args: argparse.Namespace) -> int:
    """Handle organization management commands.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    db_path = ensure_data_dir()
    org_repo = get_organization_repository(db_path)

    if args.org_command == "create":
        return _handle_org_create(args, org_repo)
    elif args.org_command == "list":
        return _handle_org_list(args, org_repo)
    elif args.org_command == "get":
        return _handle_org_get(args, org_repo)
    elif args.org_command == "update":
        return _handle_org_update(args, org_repo)
    elif args.org_command == "delete":
        return _handle_org_delete(args, org_repo)
    else:
        print("Error: No org command specified. Use --help for usage.")
        return 1


def _handle_org_create(
    args: argparse.Namespace,
    org_repo: OrganizationRepository,
) -> int:
    """Handle org create command."""
    slug = args.slug or slugify(args.name)

    org = Organization(
        name=args.name,
        slug=slug,
        subscription_tier=args.tier,
        max_users=args.max_users,
        max_configs=args.max_configs,
    )

    try:
        org = org_repo.create(org)
        output_result(
            {
                "success": True,
                "message": "Organization created successfully",
                "organization": org.to_dict(),
            },
            args.output,
        )
        return 0
    except ValueError as e:
        output_result(
            {
                "success": False,
                "message": str(e),
            },
            args.output,
        )
        return 1


def _handle_org_list(
    args: argparse.Namespace,
    org_repo: OrganizationRepository,
) -> int:
    """Handle org list command."""
    orgs = org_repo.get_all(
        include_inactive=args.include_inactive,
        limit=args.limit,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "organizations": [o.to_dict() for o in orgs],
                    "total": len(orgs),
                },
                indent=2,
            )
        )
    else:
        if not orgs:
            print("No organizations found.")
        else:
            print(f"Organizations ({len(orgs)} found):")
            print("-" * 60)
            for org in orgs:
                status = "active" if org.is_active else "inactive"
                print(f"  {org.id:4d}  {org.slug:30s}  {org.name[:20]:20s}  {status}")

    return 0


def _handle_org_get(
    args: argparse.Namespace,
    org_repo: OrganizationRepository,
) -> int:
    """Handle org get command."""
    org = org_repo.get_by_slug(args.slug)

    if not org:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.slug}' not found",
            },
            args.output,
        )
        return 1

    if args.output == "json":
        print(json.dumps({"success": True, "organization": org.to_dict()}, indent=2))
    else:
        print(f"Organization: {org.name}")
        print(f"  ID: {org.id}")
        print(f"  Slug: {org.slug}")
        print(f"  Status: {'Active' if org.is_active else 'Inactive'}")
        print(f"  Tier: {org.subscription_tier}")
        print(f"  Max Users: {org.max_users}")
        print(f"  Max Configs: {org.max_configs}")
        print(f"  Created: {org.created_at.isoformat() if org.created_at else 'N/A'}")

    return 0


def _handle_org_update(
    args: argparse.Namespace,
    org_repo: OrganizationRepository,
) -> int:
    """Handle org update command."""
    org = org_repo.get_by_slug(args.slug)

    if not org:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.slug}' not found",
            },
            args.output,
        )
        return 1

    # Apply updates
    if args.name:
        org.name = args.name
    if args.tier:
        org.subscription_tier = args.tier
    if args.max_users is not None:
        org.max_users = args.max_users
    if args.max_configs is not None:
        org.max_configs = args.max_configs

    try:
        org = org_repo.update(org)
        output_result(
            {
                "success": True,
                "message": "Organization updated successfully",
                "organization": org.to_dict(),
            },
            args.output,
        )
        return 0
    except ValueError as e:
        output_result(
            {
                "success": False,
                "message": str(e),
            },
            args.output,
        )
        return 1


def _handle_org_delete(
    args: argparse.Namespace,
    org_repo: OrganizationRepository,
) -> int:
    """Handle org delete command."""
    org = org_repo.get_by_slug(args.slug)

    if not org:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.slug}' not found",
            },
            args.output,
        )
        return 1

    # Check for users if not forced
    if not args.force:
        user_repo = get_user_repository(get_tenant_db_path())
        assert org.id is not None
        user_count = user_repo.count(org.id)
        if user_count > 0:
            output_result(
                {
                    "success": False,
                    "message": f"Organization has {user_count} users. Use --force to delete anyway.",
                },
                args.output,
            )
            return 1

    # Soft delete (deactivate)
    assert org.id is not None
    org_repo.deactivate(org.id)

    output_result(
        {
            "success": True,
            "message": f"Organization '{org.slug}' has been deactivated",
        },
        args.output,
    )
    return 0
