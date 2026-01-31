"""CLI commands for user management."""

from __future__ import annotations

import argparse
import getpass
import json
import os
from typing import Any

from mysql_to_sheets.cli.utils import (
    ensure_data_dir,
    output_user_result,
)
from mysql_to_sheets.cli.utils import (
    get_organization_id as get_org_id,
)
from mysql_to_sheets.core.auth import (
    hash_password,
    validate_password_strength,
)
from mysql_to_sheets.models.users import (
    VALID_ROLES,
    User,
    get_user_repository,
)


def output_result(data: dict[str, Any], format: str) -> None:
    """Output result in the specified format.

    Args:
        data: Result data dictionary.
        format: Output format ('text' or 'json').
    """
    output_user_result(data, format)


def add_user_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add user management subcommands.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    user_parser = subparsers.add_parser(
        "user",
        help="Manage users (multi-tenant)",
    )
    user_subparsers = user_parser.add_subparsers(
        dest="user_command",
        help="User commands",
    )

    # user create
    user_create = user_subparsers.add_parser(
        "create",
        help="Create a new user",
    )
    user_create.add_argument(
        "--email",
        required=True,
        help="User email address",
    )
    user_create.add_argument(
        "--name",
        required=True,
        help="User display name",
    )
    user_create.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    user_create.add_argument(
        "--role",
        default="viewer",
        choices=list(VALID_ROLES),
        help="User role (default: viewer)",
    )
    user_create.add_argument(
        "--password",
        help="User password (prompted if not provided)",
    )
    user_create.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # user list
    user_list = user_subparsers.add_parser(
        "list",
        help="List users in an organization",
    )
    user_list.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    user_list.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include inactive users",
    )
    user_list.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of users to list",
    )
    user_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # user get
    user_get = user_subparsers.add_parser(
        "get",
        help="Get user details",
    )
    user_get.add_argument(
        "--id",
        type=int,
        help="User ID",
    )
    user_get.add_argument(
        "--email",
        help="User email",
    )
    user_get.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    user_get.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # user update
    user_update = user_subparsers.add_parser(
        "update",
        help="Update a user",
    )
    user_update.add_argument(
        "--id",
        type=int,
        required=True,
        help="User ID to update",
    )
    user_update.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    user_update.add_argument(
        "--name",
        help="New display name",
    )
    user_update.add_argument(
        "--email",
        help="New email address",
    )
    user_update.add_argument(
        "--role",
        choices=list(VALID_ROLES),
        help="New role",
    )
    user_update.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # user delete
    user_delete = user_subparsers.add_parser(
        "delete",
        help="Delete (deactivate) a user",
    )
    user_delete.add_argument(
        "--id",
        type=int,
        required=True,
        help="User ID to delete",
    )
    user_delete.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    user_delete.add_argument(
        "--hard",
        action="store_true",
        help="Permanently delete instead of deactivate",
    )
    user_delete.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # user reset-password
    user_reset = user_subparsers.add_parser(
        "reset-password",
        help="Reset a user's password",
    )
    user_reset.add_argument(
        "--id",
        type=int,
        required=True,
        help="User ID",
    )
    user_reset.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    user_reset.add_argument(
        "--password",
        help="New password (prompted if not provided)",
    )
    user_reset.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # user whoami
    user_whoami = user_subparsers.add_parser(
        "whoami",
        help="Show current user information (from env)",
    )
    user_whoami.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def handle_user_command(args: argparse.Namespace) -> int:
    """Handle user management commands.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    db_path = ensure_data_dir()

    if args.user_command == "create":
        return _handle_user_create(args, db_path)
    elif args.user_command == "list":
        return _handle_user_list(args, db_path)
    elif args.user_command == "get":
        return _handle_user_get(args, db_path)
    elif args.user_command == "update":
        return _handle_user_update(args, db_path)
    elif args.user_command == "delete":
        return _handle_user_delete(args, db_path)
    elif args.user_command == "reset-password":
        return _handle_user_reset_password(args, db_path)
    elif args.user_command == "whoami":
        return _handle_user_whoami(args)
    else:
        print("Error: No user command specified. Use --help for usage.")
        return 1


def _get_organization_id(org_slug: str, db_path: str) -> int | None:
    """Get organization ID from slug.

    Args:
        org_slug: Organization slug.
        db_path: Database path.

    Returns:
        Organization ID or None if not found.
    """
    return get_org_id(org_slug, db_path)


def _handle_user_create(args: argparse.Namespace, db_path: str) -> int:
    """Handle user create command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    # Get or prompt for password
    password = args.password
    if not password:
        try:
            password = getpass.getpass("Password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                output_result(
                    {
                        "success": False,
                        "message": "Passwords do not match",
                    },
                    args.output,
                )
                return 1
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled")
            return 1

    # Validate password strength
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        output_result(
            {
                "success": False,
                "message": "Password does not meet requirements",
                "errors": errors,
            },
            args.output,
        )
        return 1

    user_repo = get_user_repository(db_path)

    user = User(
        email=args.email,
        display_name=args.name,
        organization_id=org_id,
        role=args.role,
        password_hash=hash_password(password),
    )

    try:
        user = user_repo.create(user)
        output_result(
            {
                "success": True,
                "message": "User created successfully",
                "user": user.to_dict(),
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


def _handle_user_list(args: argparse.Namespace, db_path: str) -> int:
    """Handle user list command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    user_repo = get_user_repository(db_path)
    users = user_repo.get_all(
        organization_id=org_id,
        include_inactive=args.include_inactive,
        limit=args.limit,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "users": [u.to_dict() for u in users],
                    "total": len(users),
                },
                indent=2,
            )
        )
    else:
        if not users:
            print("No users found.")
        else:
            print(f"Users ({len(users)} found):")
            print("-" * 80)
            for user in users:
                status = "active" if user.is_active else "inactive"
                print(f"  {user.id:4d}  {user.email:35s}  {user.role:10s}  {status}")

    return 0


def _handle_user_get(args: argparse.Namespace, db_path: str) -> int:
    """Handle user get command."""
    if not args.id and not args.email:
        output_result(
            {
                "success": False,
                "message": "Either --id or --email is required",
            },
            args.output,
        )
        return 1

    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    user_repo = get_user_repository(db_path)

    if args.id:
        user = user_repo.get_by_id(args.id, organization_id=org_id)
    else:
        user = user_repo.get_by_email(args.email, organization_id=org_id)

    if not user:
        output_result(
            {
                "success": False,
                "message": "User not found",
            },
            args.output,
        )
        return 1

    if args.output == "json":
        print(json.dumps({"success": True, "user": user.to_dict()}, indent=2))
    else:
        print(f"User: {user.display_name}")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role}")
        print(f"  Status: {'Active' if user.is_active else 'Inactive'}")
        print(f"  Created: {user.created_at.isoformat() if user.created_at else 'N/A'}")
        print(f"  Last Login: {user.last_login_at.isoformat() if user.last_login_at else 'Never'}")

    return 0


def _handle_user_update(args: argparse.Namespace, db_path: str) -> int:
    """Handle user update command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    user_repo = get_user_repository(db_path)
    user = user_repo.get_by_id(args.id, organization_id=org_id)

    if not user:
        output_result(
            {
                "success": False,
                "message": f"User with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    # Apply updates
    if args.name:
        user.display_name = args.name
    if args.email:
        user.email = args.email
    if args.role:
        user.role = args.role

    try:
        user = user_repo.update(user)
        output_result(
            {
                "success": True,
                "message": "User updated successfully",
                "user": user.to_dict(),
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


def _handle_user_delete(args: argparse.Namespace, db_path: str) -> int:
    """Handle user delete command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    user_repo = get_user_repository(db_path)
    user = user_repo.get_by_id(args.id, organization_id=org_id)

    if not user:
        output_result(
            {
                "success": False,
                "message": f"User with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    # Check if trying to delete owner
    if user.role == "owner":
        output_result(
            {
                "success": False,
                "message": "Cannot delete organization owner. Transfer ownership first.",
            },
            args.output,
        )
        return 1

    if args.hard:
        user_repo.delete(args.id, organization_id=org_id)
        message = f"User '{user.email}' has been permanently deleted"
    else:
        user_repo.deactivate(args.id, organization_id=org_id)
        message = f"User '{user.email}' has been deactivated"

    output_result(
        {
            "success": True,
            "message": message,
        },
        args.output,
    )
    return 0


def _handle_user_reset_password(args: argparse.Namespace, db_path: str) -> int:
    """Handle user reset-password command."""
    org_id = _get_organization_id(args.org_slug, db_path)
    if org_id is None:
        output_result(
            {
                "success": False,
                "message": f"Organization '{args.org_slug}' not found",
            },
            args.output,
        )
        return 1

    user_repo = get_user_repository(db_path)
    user = user_repo.get_by_id(args.id, organization_id=org_id)

    if not user:
        output_result(
            {
                "success": False,
                "message": f"User with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    # Get or prompt for password
    password = args.password
    if not password:
        try:
            password = getpass.getpass("New password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                output_result(
                    {
                        "success": False,
                        "message": "Passwords do not match",
                    },
                    args.output,
                )
                return 1
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled")
            return 1

    # Validate password strength
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        output_result(
            {
                "success": False,
                "message": "Password does not meet requirements",
                "errors": errors,
            },
            args.output,
        )
        return 1

    user_repo.update_password(args.id, hash_password(password))

    output_result(
        {
            "success": True,
            "message": f"Password reset for user '{user.email}'",
        },
        args.output,
    )
    return 0


def _handle_user_whoami(args: argparse.Namespace) -> int:
    """Handle user whoami command.

    Shows information about the current user from environment or config.
    In CLI context, this is primarily for testing/debugging.
    """
    # Check for environment variables that might indicate current user
    current_user_email = os.getenv("CURRENT_USER_EMAIL")
    current_user_id = os.getenv("CURRENT_USER_ID")
    current_org_slug = os.getenv("CURRENT_ORG_SLUG")

    if not current_user_email and not current_user_id:
        output_result(
            {
                "success": False,
                "message": "No current user context. Set CURRENT_USER_EMAIL or CURRENT_USER_ID",
            },
            args.output,
        )
        return 1

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "user": {
                        "email": current_user_email,
                        "id": int(current_user_id) if current_user_id else None,
                        "organization_slug": current_org_slug,
                    },
                },
                indent=2,
            )
        )
    else:
        print("Current User Context (from environment):")
        if current_user_email:
            print(f"  Email: {current_user_email}")
        if current_user_id:
            print(f"  ID: {current_user_id}")
        if current_org_slug:
            print(f"  Organization: {current_org_slug}")

    return 0
