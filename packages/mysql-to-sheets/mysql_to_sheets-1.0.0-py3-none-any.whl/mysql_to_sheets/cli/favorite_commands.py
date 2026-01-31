"""CLI commands for favorites management.

Provides commands to manage favorite queries and sheets:
- favorite query add/list/get/edit/remove
- favorite sheet add/list/get/edit/remove/verify
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from mysql_to_sheets.cli.utils import (
    get_organization_id,
    get_tenant_db_path,
)
from mysql_to_sheets.cli.utils import (
    output_result as base_output_result,
)
from mysql_to_sheets.models.favorites import (
    FavoriteQuery,
    FavoriteSheet,
    get_favorite_query_repository,
    get_favorite_sheet_repository,
)


def output_result(data: dict[str, Any], format: str, entity_key: str = "favorite") -> None:
    """Output result in the specified format.

    Args:
        data: Result data dictionary.
        format: Output format ('text' or 'json').
        entity_key: Key for entity data in response.
    """
    base_output_result(
        data,
        format,
        entity_key=entity_key,
        entity_fields=["id", "name", "description"],
    )


def add_favorite_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add favorite management subcommands.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    favorite_parser = subparsers.add_parser(
        "favorite",
        help="Manage favorite queries and sheets",
    )
    favorite_subparsers = favorite_parser.add_subparsers(
        dest="favorite_type",
        help="Favorite type (query or sheet)",
    )

    # =========================================================================
    # favorite query commands
    # =========================================================================
    query_parser = favorite_subparsers.add_parser(
        "query",
        help="Manage favorite queries",
    )
    query_subparsers = query_parser.add_subparsers(
        dest="favorite_command",
        help="Query commands",
    )

    # favorite query add
    query_add = query_subparsers.add_parser(
        "add",
        help="Add a new favorite query",
    )
    query_add.add_argument(
        "--name",
        required=True,
        help="Name for the favorite query",
    )
    query_add.add_argument(
        "--query",
        required=True,
        help="SQL query to save",
    )
    query_add.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    query_add.add_argument(
        "--description",
        help="Description of the query",
    )
    query_add.add_argument(
        "--tags",
        help="Comma-separated list of tags",
    )
    query_add.add_argument(
        "--private",
        action="store_true",
        help="Make this favorite private (only visible to you)",
    )
    query_add.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # favorite query list
    query_list = query_subparsers.add_parser(
        "list",
        help="List favorite queries",
    )
    query_list.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    query_list.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include inactive favorites",
    )
    query_list.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of results",
    )
    query_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # favorite query get
    query_get = query_subparsers.add_parser(
        "get",
        help="Get favorite query details",
    )
    query_get.add_argument(
        "--name",
        help="Favorite query name",
    )
    query_get.add_argument(
        "--id",
        type=int,
        help="Favorite query ID",
    )
    query_get.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    query_get.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # favorite query edit
    query_edit = query_subparsers.add_parser(
        "edit",
        help="Edit a favorite query",
    )
    query_edit.add_argument(
        "--id",
        type=int,
        required=True,
        help="Favorite query ID to edit",
    )
    query_edit.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    query_edit.add_argument(
        "--name",
        help="New name",
    )
    query_edit.add_argument(
        "--query",
        help="New SQL query",
    )
    query_edit.add_argument(
        "--description",
        help="New description",
    )
    query_edit.add_argument(
        "--tags",
        help="New comma-separated list of tags",
    )
    query_edit.add_argument(
        "--private",
        action="store_true",
        help="Make private",
    )
    query_edit.add_argument(
        "--shared",
        action="store_true",
        help="Make shared (visible to org)",
    )
    query_edit.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # favorite query remove
    query_remove = query_subparsers.add_parser(
        "remove",
        help="Remove a favorite query",
    )
    query_remove.add_argument(
        "--id",
        type=int,
        required=True,
        help="Favorite query ID to remove",
    )
    query_remove.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    query_remove.add_argument(
        "--hard",
        action="store_true",
        help="Permanently delete instead of deactivate",
    )
    query_remove.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # =========================================================================
    # favorite sheet commands
    # =========================================================================
    sheet_parser = favorite_subparsers.add_parser(
        "sheet",
        help="Manage favorite sheets",
    )
    sheet_subparsers = sheet_parser.add_subparsers(
        dest="favorite_command",
        help="Sheet commands",
    )

    # favorite sheet add
    sheet_add = sheet_subparsers.add_parser(
        "add",
        help="Add a new favorite sheet",
    )
    sheet_add.add_argument(
        "--name",
        required=True,
        help="Name for the favorite sheet",
    )
    sheet_add.add_argument(
        "--sheet-id",
        required=True,
        help="Google Sheet ID or full URL (e.g., https://docs.google.com/spreadsheets/d/SHEET_ID/edit)",
    )
    sheet_add.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    sheet_add.add_argument(
        "--description",
        help="Description of the sheet",
    )
    sheet_add.add_argument(
        "--worksheet",
        default="Sheet1",
        help="Default worksheet name (default: Sheet1)",
    )
    sheet_add.add_argument(
        "--tags",
        help="Comma-separated list of tags",
    )
    sheet_add.add_argument(
        "--private",
        action="store_true",
        help="Make this favorite private (only visible to you)",
    )
    sheet_add.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # favorite sheet list
    sheet_list = sheet_subparsers.add_parser(
        "list",
        help="List favorite sheets",
    )
    sheet_list.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    sheet_list.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include inactive favorites",
    )
    sheet_list.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of results",
    )
    sheet_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # favorite sheet get
    sheet_get = sheet_subparsers.add_parser(
        "get",
        help="Get favorite sheet details",
    )
    sheet_get.add_argument(
        "--name",
        help="Favorite sheet name",
    )
    sheet_get.add_argument(
        "--id",
        type=int,
        help="Favorite sheet ID",
    )
    sheet_get.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    sheet_get.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # favorite sheet edit
    sheet_edit = sheet_subparsers.add_parser(
        "edit",
        help="Edit a favorite sheet",
    )
    sheet_edit.add_argument(
        "--id",
        type=int,
        required=True,
        help="Favorite sheet ID to edit",
    )
    sheet_edit.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    sheet_edit.add_argument(
        "--name",
        help="New name",
    )
    sheet_edit.add_argument(
        "--sheet-id",
        help="New Google Sheet ID or full URL",
    )
    sheet_edit.add_argument(
        "--worksheet",
        help="New default worksheet name",
    )
    sheet_edit.add_argument(
        "--description",
        help="New description",
    )
    sheet_edit.add_argument(
        "--tags",
        help="New comma-separated list of tags",
    )
    sheet_edit.add_argument(
        "--private",
        action="store_true",
        help="Make private",
    )
    sheet_edit.add_argument(
        "--shared",
        action="store_true",
        help="Make shared (visible to org)",
    )
    sheet_edit.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # favorite sheet remove
    sheet_remove = sheet_subparsers.add_parser(
        "remove",
        help="Remove a favorite sheet",
    )
    sheet_remove.add_argument(
        "--id",
        type=int,
        required=True,
        help="Favorite sheet ID to remove",
    )
    sheet_remove.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    sheet_remove.add_argument(
        "--hard",
        action="store_true",
        help="Permanently delete instead of deactivate",
    )
    sheet_remove.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # favorite sheet verify
    sheet_verify = sheet_subparsers.add_parser(
        "verify",
        help="Verify access to a favorite sheet",
    )
    sheet_verify.add_argument(
        "--id",
        type=int,
        required=True,
        help="Favorite sheet ID to verify",
    )
    sheet_verify.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    sheet_verify.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def handle_favorite_command(args: argparse.Namespace) -> int:
    """Handle favorite management commands.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    db_path = get_tenant_db_path()

    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    if args.favorite_type == "query":
        return _handle_query_command(args, db_path)
    elif args.favorite_type == "sheet":
        return _handle_sheet_command(args, db_path)
    else:
        print("Error: No favorite type specified. Use 'query' or 'sheet'.")
        return 1


def _handle_query_command(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite query subcommands."""
    if args.favorite_command == "add":
        return _handle_query_add(args, db_path)
    elif args.favorite_command == "list":
        return _handle_query_list(args, db_path)
    elif args.favorite_command == "get":
        return _handle_query_get(args, db_path)
    elif args.favorite_command == "edit":
        return _handle_query_edit(args, db_path)
    elif args.favorite_command == "remove":
        return _handle_query_remove(args, db_path)
    else:
        print("Error: No command specified. Use --help for usage.")
        return 1


def _handle_sheet_command(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite sheet subcommands."""
    if args.favorite_command == "add":
        return _handle_sheet_add(args, db_path)
    elif args.favorite_command == "list":
        return _handle_sheet_list(args, db_path)
    elif args.favorite_command == "get":
        return _handle_sheet_get(args, db_path)
    elif args.favorite_command == "edit":
        return _handle_sheet_edit(args, db_path)
    elif args.favorite_command == "remove":
        return _handle_sheet_remove(args, db_path)
    elif args.favorite_command == "verify":
        return _handle_sheet_verify(args, db_path)
    else:
        print("Error: No command specified. Use --help for usage.")
        return 1


# =============================================================================
# Query command handlers
# =============================================================================


def _handle_query_add(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite query add command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    # Parse tags
    tags = []
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    query_repo = get_favorite_query_repository(db_path)

    favorite = FavoriteQuery(
        name=args.name.strip(),
        sql_query=args.query,
        organization_id=org_id,
        description=args.description or "",
        tags=tags,
        is_private=args.private,
    )

    try:
        favorite = query_repo.create(favorite)

        output_result(
            {
                "success": True,
                "message": "Favorite query created successfully",
                "favorite": favorite.to_dict(),
            },
            args.output,
            entity_key="favorite",
        )
        return 0
    except ValueError as e:
        output_result(
            {"success": False, "message": str(e)},
            args.output,
        )
        return 1


def _handle_query_list(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite query list command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    query_repo = get_favorite_query_repository(db_path)
    favorites = query_repo.get_all(
        organization_id=org_id,
        include_inactive=args.include_inactive,
        limit=args.limit,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "favorites": [f.to_dict() for f in favorites],
                    "total": len(favorites),
                },
                indent=2,
            )
        )
    else:
        if not favorites:
            print("No favorite queries found.")
        else:
            print(f"Favorite Queries ({len(favorites)} found):")
            print("-" * 80)
            for fav in favorites:
                visibility = "private" if fav.is_private else "shared"
                status = "active" if fav.is_active else "inactive"
                query_preview = (
                    fav.sql_query[:50] + "..." if len(fav.sql_query) > 50 else fav.sql_query
                )
                query_preview = query_preview.replace("\n", " ")
                print(f"  {fav.id:4d}  {fav.name:30s}  {visibility:8s}  uses: {fav.use_count}")
                print(f"        {query_preview}")
                if fav.tags:
                    print(f"        Tags: {', '.join(fav.tags)}")

    return 0


def _handle_query_get(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite query get command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    if not args.name and not args.id:
        output_result(
            {"success": False, "message": "Either --name or --id is required"},
            args.output,
        )
        return 1

    query_repo = get_favorite_query_repository(db_path)

    if args.id:
        favorite = query_repo.get_by_id(args.id, organization_id=org_id)
    else:
        favorite = query_repo.get_by_name(args.name, organization_id=org_id)

    if not favorite:
        identifier = f"ID {args.id}" if args.id else f"name '{args.name}'"
        output_result(
            {"success": False, "message": f"Favorite query with {identifier} not found"},
            args.output,
        )
        return 1

    if args.output == "json":
        print(json.dumps({"success": True, "favorite": favorite.to_dict()}, indent=2))
    else:
        visibility = "Private" if favorite.is_private else "Shared"
        print(f"Favorite Query: {favorite.name}")
        print(f"  ID: {favorite.id}")
        print(f"  Visibility: {visibility}")
        if favorite.description:
            print(f"  Description: {favorite.description}")
        print(f"  SQL Query:\n    {favorite.sql_query}")
        if favorite.tags:
            print(f"  Tags: {', '.join(favorite.tags)}")
        print(f"  Use Count: {favorite.use_count}")
        if favorite.last_used_at:
            print(f"  Last Used: {favorite.last_used_at.isoformat()}")
        if favorite.created_at:
            print(f"  Created: {favorite.created_at.isoformat()}")

    return 0


def _handle_query_edit(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite query edit command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    query_repo = get_favorite_query_repository(db_path)
    favorite = query_repo.get_by_id(args.id, organization_id=org_id)

    if not favorite:
        output_result(
            {"success": False, "message": f"Favorite query with ID {args.id} not found"},
            args.output,
        )
        return 1

    # Apply updates
    if args.name:
        favorite.name = args.name.strip()
    if args.query:
        favorite.sql_query = args.query
    if args.description is not None:
        favorite.description = args.description
    if args.tags is not None:
        favorite.tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    if args.private:
        favorite.is_private = True
    if args.shared:
        favorite.is_private = False

    try:
        favorite = query_repo.update(favorite)
        output_result(
            {
                "success": True,
                "message": "Favorite query updated successfully",
                "favorite": favorite.to_dict(),
            },
            args.output,
            entity_key="favorite",
        )
        return 0
    except ValueError as e:
        output_result(
            {"success": False, "message": str(e)},
            args.output,
        )
        return 1


def _handle_query_remove(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite query remove command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    query_repo = get_favorite_query_repository(db_path)
    favorite = query_repo.get_by_id(args.id, organization_id=org_id)

    if not favorite:
        output_result(
            {"success": False, "message": f"Favorite query with ID {args.id} not found"},
            args.output,
        )
        return 1

    if args.hard:
        query_repo.delete(args.id, organization_id=org_id)
        message = f"Favorite query '{favorite.name}' permanently deleted"
    else:
        query_repo.deactivate(args.id, organization_id=org_id)
        message = f"Favorite query '{favorite.name}' deactivated"

    output_result(
        {"success": True, "message": message},
        args.output,
    )
    return 0


# =============================================================================
# Sheet command handlers
# =============================================================================


def _handle_sheet_add(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite sheet add command."""
    from mysql_to_sheets.core.sheets_utils import parse_sheet_id

    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    # Parse sheet ID from URL or raw ID
    try:
        sheet_id = parse_sheet_id(args.sheet_id)
    except ValueError as e:
        output_result({"success": False, "message": str(e)}, args.output)
        return 1

    # Parse tags
    tags = []
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    sheet_repo = get_favorite_sheet_repository(db_path)

    favorite = FavoriteSheet(
        name=args.name.strip(),
        sheet_id=sheet_id,
        organization_id=org_id,
        description=args.description or "",
        default_worksheet=args.worksheet,
        tags=tags,
        is_private=args.private,
    )

    try:
        favorite = sheet_repo.create(favorite)

        output_result(
            {
                "success": True,
                "message": "Favorite sheet created successfully",
                "favorite": favorite.to_dict(),
            },
            args.output,
            entity_key="favorite",
        )
        return 0
    except ValueError as e:
        output_result(
            {"success": False, "message": str(e)},
            args.output,
        )
        return 1


def _handle_sheet_list(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite sheet list command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    sheet_repo = get_favorite_sheet_repository(db_path)
    favorites = sheet_repo.get_all(
        organization_id=org_id,
        include_inactive=args.include_inactive,
        limit=args.limit,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "favorites": [f.to_dict() for f in favorites],
                    "total": len(favorites),
                },
                indent=2,
            )
        )
    else:
        if not favorites:
            print("No favorite sheets found.")
        else:
            print(f"Favorite Sheets ({len(favorites)} found):")
            print("-" * 80)
            for fav in favorites:
                visibility = "private" if fav.is_private else "shared"
                sheet_preview = (
                    fav.sheet_id[:20] + "..." if len(fav.sheet_id) > 20 else fav.sheet_id
                )
                print(f"  {fav.id:4d}  {fav.name:30s}  {visibility:8s}  uses: {fav.use_count}")
                print(f"        Sheet: {sheet_preview}  Worksheet: {fav.default_worksheet}")
                if fav.tags:
                    print(f"        Tags: {', '.join(fav.tags)}")

    return 0


def _handle_sheet_get(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite sheet get command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    if not args.name and not args.id:
        output_result(
            {"success": False, "message": "Either --name or --id is required"},
            args.output,
        )
        return 1

    sheet_repo = get_favorite_sheet_repository(db_path)

    if args.id:
        favorite = sheet_repo.get_by_id(args.id, organization_id=org_id)
    else:
        favorite = sheet_repo.get_by_name(args.name, organization_id=org_id)

    if not favorite:
        identifier = f"ID {args.id}" if args.id else f"name '{args.name}'"
        output_result(
            {"success": False, "message": f"Favorite sheet with {identifier} not found"},
            args.output,
        )
        return 1

    if args.output == "json":
        print(json.dumps({"success": True, "favorite": favorite.to_dict()}, indent=2))
    else:
        visibility = "Private" if favorite.is_private else "Shared"
        print(f"Favorite Sheet: {favorite.name}")
        print(f"  ID: {favorite.id}")
        print(f"  Visibility: {visibility}")
        if favorite.description:
            print(f"  Description: {favorite.description}")
        print(f"  Sheet ID: {favorite.sheet_id}")
        print(f"  Default Worksheet: {favorite.default_worksheet}")
        if favorite.tags:
            print(f"  Tags: {', '.join(favorite.tags)}")
        print(f"  Use Count: {favorite.use_count}")
        if favorite.last_used_at:
            print(f"  Last Used: {favorite.last_used_at.isoformat()}")
        if favorite.last_verified_at:
            print(f"  Last Verified: {favorite.last_verified_at.isoformat()}")
        if favorite.created_at:
            print(f"  Created: {favorite.created_at.isoformat()}")

    return 0


def _handle_sheet_edit(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite sheet edit command."""
    from mysql_to_sheets.core.sheets_utils import parse_sheet_id

    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    sheet_repo = get_favorite_sheet_repository(db_path)
    favorite = sheet_repo.get_by_id(args.id, organization_id=org_id)

    if not favorite:
        output_result(
            {"success": False, "message": f"Favorite sheet with ID {args.id} not found"},
            args.output,
        )
        return 1

    # Apply updates
    if args.name:
        favorite.name = args.name.strip()
    if args.sheet_id:
        # Parse sheet ID from URL or raw ID
        try:
            favorite.sheet_id = parse_sheet_id(args.sheet_id)
        except ValueError as e:
            output_result({"success": False, "message": str(e)}, args.output)
            return 1
    if args.worksheet:
        favorite.default_worksheet = args.worksheet
    if args.description is not None:
        favorite.description = args.description
    if args.tags is not None:
        favorite.tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    if args.private:
        favorite.is_private = True
    if args.shared:
        favorite.is_private = False

    try:
        favorite = sheet_repo.update(favorite)
        output_result(
            {
                "success": True,
                "message": "Favorite sheet updated successfully",
                "favorite": favorite.to_dict(),
            },
            args.output,
            entity_key="favorite",
        )
        return 0
    except ValueError as e:
        output_result(
            {"success": False, "message": str(e)},
            args.output,
        )
        return 1


def _handle_sheet_remove(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite sheet remove command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    sheet_repo = get_favorite_sheet_repository(db_path)
    favorite = sheet_repo.get_by_id(args.id, organization_id=org_id)

    if not favorite:
        output_result(
            {"success": False, "message": f"Favorite sheet with ID {args.id} not found"},
            args.output,
        )
        return 1

    if args.hard:
        sheet_repo.delete(args.id, organization_id=org_id)
        message = f"Favorite sheet '{favorite.name}' permanently deleted"
    else:
        sheet_repo.deactivate(args.id, organization_id=org_id)
        message = f"Favorite sheet '{favorite.name}' deactivated"

    output_result(
        {"success": True, "message": message},
        args.output,
    )
    return 0


def _handle_sheet_verify(args: argparse.Namespace, db_path: str) -> int:
    """Handle favorite sheet verify command."""
    org_id = get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {"success": False, "message": f"Organization '{args.org_slug}' not found"},
            args.output,
        )
        return 1

    sheet_repo = get_favorite_sheet_repository(db_path)
    favorite = sheet_repo.get_by_id(args.id, organization_id=org_id)

    if not favorite:
        output_result(
            {"success": False, "message": f"Favorite sheet with ID {args.id} not found"},
            args.output,
        )
        return 1

    print(f"Verifying access to sheet '{favorite.name}'...")

    try:
        import gspread

        from mysql_to_sheets.core.config import get_config
        from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier

        config = get_config()
        gc = gspread.service_account(filename=config.service_account_file)  # type: ignore[attr-defined]

        # Try to open the sheet
        spreadsheet = gc.open_by_key(favorite.sheet_id)

        # Resolve worksheet name from GID URL if needed
        worksheet_name = parse_worksheet_identifier(
            favorite.default_worksheet,
            spreadsheet=spreadsheet,
        )

        # Try to access the worksheet
        worksheet = spreadsheet.worksheet(worksheet_name)

        # Update verified timestamp
        sheet_repo.update_verified(args.id, organization_id=org_id)

        output_result(
            {
                "success": True,
                "message": f"Access verified for sheet '{favorite.name}'",
                "spreadsheet_title": spreadsheet.title,
                "worksheet_name": worksheet.title,
                "row_count": worksheet.row_count,
                "col_count": worksheet.col_count,
            },
            args.output,
        )
        return 0

    except gspread.exceptions.SpreadsheetNotFound:
        output_result(
            {
                "success": False,
                "message": "Spreadsheet not found or not shared with service account",
                "sheet_id": favorite.sheet_id,
            },
            args.output,
        )
        return 1
    except gspread.exceptions.WorksheetNotFound:
        output_result(
            {
                "success": False,
                "message": f"Worksheet '{favorite.default_worksheet}' not found",
                "sheet_id": favorite.sheet_id,
            },
            args.output,
        )
        return 1
    except Exception as e:
        output_result(
            {
                "success": False,
                "message": f"Failed to verify sheet access: {e}",
            },
            args.output,
        )
        return 1
