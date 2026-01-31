"""CLI commands for API key management.

Contains: api-key create/list/revoke commands.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from mysql_to_sheets.cli.utils import output_result
from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.security import generate_api_key, generate_api_key_salt, hash_api_key
from mysql_to_sheets.models.api_keys import get_api_key_repository


def add_api_key_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add API key management command parsers.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    api_key_parser = subparsers.add_parser(
        "api-key",
        help="Manage API keys",
    )
    api_key_subparsers = api_key_parser.add_subparsers(
        dest="api_key_command",
        help="API key commands",
    )

    # api-key create
    api_key_create = api_key_subparsers.add_parser(
        "create",
        help="Create a new API key",
    )
    api_key_create.add_argument(
        "--name",
        required=True,
        help="Name for the API key",
    )
    api_key_create.add_argument(
        "--description",
        help="Optional description for the key",
    )
    api_key_create.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # api-key list
    api_key_list = api_key_subparsers.add_parser(
        "list",
        help="List all API keys",
    )
    api_key_list.add_argument(
        "--include-revoked",
        action="store_true",
        help="Include revoked keys in the list",
    )
    api_key_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # api-key revoke
    api_key_revoke = api_key_subparsers.add_parser(
        "revoke",
        help="Revoke an API key",
    )
    api_key_revoke.add_argument(
        "--id",
        type=int,
        required=True,
        help="ID of the API key to revoke",
    )
    api_key_revoke.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def cmd_api_key(args: argparse.Namespace) -> int:
    """Execute api-key command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    config = get_config()
    db_path = config.history_db_path or "./data/sync_history.db"

    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    repo = get_api_key_repository(db_path)

    if args.api_key_command == "create":
        return cmd_api_key_create(args, repo)
    elif args.api_key_command == "list":
        return cmd_api_key_list(args, repo)
    elif args.api_key_command == "revoke":
        return cmd_api_key_revoke(args, repo)
    else:
        print("Error: No api-key command specified. Use --help for usage.")
        return 1


def cmd_api_key_create(args: argparse.Namespace, repo: Any) -> int:
    """Execute api-key create command.

    Args:
        args: Parsed command line arguments.
        repo: API key repository instance.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Generate a new API key with per-key salt
    raw_key = generate_api_key()
    key_salt = generate_api_key_salt()
    key_hash = hash_api_key(raw_key, key_salt)

    try:
        api_key = repo.create(
            name=args.name,
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=raw_key[:8],
            description=getattr(args, "description", None),
        )

        if args.output == "json":
            print(
                json.dumps(
                    {
                        "success": True,
                        "message": "API key created successfully",
                        "api_key": {
                            "id": api_key.id,
                            "name": api_key.name,
                            "key": raw_key,  # Only shown once!
                            "prefix": api_key.key_prefix,
                            "created_at": api_key.created_at.isoformat()
                            if api_key.created_at
                            else None,
                        },
                    },
                    indent=2,
                )
            )
        else:
            print("API key created successfully!")
            print()
            print(f"  Name:       {api_key.name}")
            print(f"  API Key:    {raw_key}")
            print()
            print("  IMPORTANT: Save this key now. It cannot be retrieved later!")

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


def cmd_api_key_list(args: argparse.Namespace, repo: Any) -> int:
    """Execute api-key list command.

    Args:
        args: Parsed command line arguments.
        repo: API key repository instance.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    keys = repo.get_all(include_revoked=args.include_revoked)

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "api_keys": [
                        {
                            "id": k.id,
                            "name": k.name,
                            "description": k.description,
                            "prefix": k.key_prefix,
                            "is_active": k.is_active,
                            "created_at": k.created_at.isoformat() if k.created_at else None,
                            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                        }
                        for k in keys
                    ],
                    "total": len(keys),
                },
                indent=2,
            )
        )
    else:
        if not keys:
            print("No API keys found.")
        else:
            print(f"API Keys ({len(keys)} found):")
            print("-" * 80)
            print(f"  {'ID':>4}  {'Name':30}  {'Prefix':10}  {'Status':8}  {'Last Used'}")
            print("-" * 80)
            for key in keys:
                status = "active" if key.is_active else "revoked"
                last_used = (
                    key.last_used_at.strftime("%Y-%m-%d %H:%M") if key.last_used_at else "never"
                )
                print(
                    f"  {key.id:>4}  {key.name[:30]:30}  {key.key_prefix:10}  {status:8}  {last_used}"
                )

    return 0


def cmd_api_key_revoke(args: argparse.Namespace, repo: Any) -> int:
    """Execute api-key revoke command.

    Args:
        args: Parsed command line arguments.
        repo: API key repository instance.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    api_key = repo.get_by_id(args.id)

    if not api_key:
        output_result(
            {
                "success": False,
                "message": f"API key with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    if not api_key.is_active:
        output_result(
            {
                "success": False,
                "message": f"API key '{api_key.name}' is already revoked",
            },
            args.output,
        )
        return 1

    repo.revoke(args.id)

    output_result(
        {
            "success": True,
            "message": f"API key '{api_key.name}' has been revoked",
        },
        args.output,
    )
    return 0
