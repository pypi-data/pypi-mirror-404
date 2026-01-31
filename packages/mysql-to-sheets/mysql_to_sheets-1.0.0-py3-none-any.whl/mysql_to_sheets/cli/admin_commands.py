"""CLI commands for admin operations.

Provides administrative commands that don't require knowing specific IDs,
useful for first-time setup and recovery scenarios.
"""

from __future__ import annotations

import argparse
import getpass
import json
import secrets
import string
from typing import Any

from mysql_to_sheets.cli.utils import ensure_data_dir
from mysql_to_sheets.core.auth import hash_password, validate_password_strength
from mysql_to_sheets.models.users import get_user_repository

# Default admin email used by bootstrap
DEFAULT_ADMIN_EMAIL = "admin@localhost"


def _generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password.

    Args:
        length: Password length (default: 16).

    Returns:
        Random password with mixed case, digits, and special characters.
    """
    # Ensure at least one of each required character type
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]

    # Fill remaining length with random characters
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Shuffle to avoid predictable positions
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def output_result(data: dict[str, Any], format: str) -> None:
    """Output result in the specified format.

    Args:
        data: Result data dictionary.
        format: Output format ('text' or 'json').
    """
    if format == "json":
        print(json.dumps(data, indent=2))
    else:
        if data.get("success"):
            print(data.get("message", "Success"))
            if "password" in data:
                print(f"\n  New password: {data['password']}")
                print("\n  IMPORTANT: Save this password - it won't be shown again!")
        else:
            print(f"Error: {data.get('message', 'Unknown error')}")


def add_admin_parsers(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add admin management subcommands.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    admin_parser = subparsers.add_parser(
        "admin",
        help="Admin operations (password reset, etc.)",
    )
    admin_subparsers = admin_parser.add_subparsers(
        dest="admin_command",
        help="Admin commands",
    )

    # admin reset-password
    reset_parser = admin_subparsers.add_parser(
        "reset-password",
        help="Reset an admin user's password (works without knowing IDs)",
    )
    reset_parser.add_argument(
        "--email",
        default=DEFAULT_ADMIN_EMAIL,
        help=f"Admin email address (default: {DEFAULT_ADMIN_EMAIL})",
    )
    reset_parser.add_argument(
        "--generate",
        action="store_true",
        help="Auto-generate a secure random password",
    )
    reset_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def handle_admin_command(args: argparse.Namespace) -> int:
    """Handle admin management commands.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    db_path = ensure_data_dir()

    if args.admin_command == "reset-password":
        return _handle_reset_password(args, db_path)
    else:
        print("Error: No admin command specified. Use --help for usage.")
        return 1


def _handle_reset_password(args: argparse.Namespace, db_path: str) -> int:
    """Handle admin reset-password command.

    Looks up user by email across all organizations and resets their password.
    """
    user_repo = get_user_repository(db_path)

    # Look up user by email across all organizations
    user = user_repo.get_by_email_global(args.email)

    if not user:
        output_result(
            {
                "success": False,
                "message": f"No user found with email '{args.email}'. "
                "Has the web dashboard been started at least once to create the admin user?",
            },
            args.output,
        )
        return 1

    # Get password - either generate or prompt
    if args.generate:
        password = _generate_secure_password()
    else:
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

    # Update password
    user.password_hash = hash_password(password)
    user.force_password_change = False  # Clear the flag since they're setting it now
    user_repo.update(user)

    result: dict[str, Any] = {
        "success": True,
        "message": f"Password reset for user '{user.email}'",
        "email": user.email,
        "user_id": user.id,
    }

    # Include password in output if generated
    if args.generate:
        result["password"] = password

    output_result(result, args.output)
    return 0
