"""CLI commands for database migrations.

Contains: db upgrade/downgrade/current/history/revision commands.
Uses Alembic for schema migrations.
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from mysql_to_sheets.cli.utils import output_result


def add_db_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add database migration command parsers.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    db_parser = subparsers.add_parser(
        "db",
        help="Database migration commands",
    )
    db_subparsers = db_parser.add_subparsers(
        dest="db_command",
        help="Database commands",
    )

    # db upgrade
    upgrade_parser = db_subparsers.add_parser(
        "upgrade",
        help="Upgrade database to a revision",
    )
    upgrade_parser.add_argument(
        "--revision",
        default="head",
        help="Revision to upgrade to (default: head)",
    )
    upgrade_parser.add_argument(
        "--sql",
        action="store_true",
        help="Generate SQL without executing",
    )
    upgrade_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # db downgrade
    downgrade_parser = db_subparsers.add_parser(
        "downgrade",
        help="Downgrade database to a revision",
    )
    downgrade_parser.add_argument(
        "revision",
        help="Revision to downgrade to (e.g., -1, base, or revision ID)",
    )
    downgrade_parser.add_argument(
        "--sql",
        action="store_true",
        help="Generate SQL without executing",
    )
    downgrade_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # db current
    current_parser = db_subparsers.add_parser(
        "current",
        help="Show current database revision",
    )
    current_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output",
    )
    current_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # db history
    history_parser = db_subparsers.add_parser(
        "history",
        help="Show migration history",
    )
    history_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output with dates",
    )
    history_parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=20,
        help="Maximum number of revisions to show (default: 20)",
    )
    history_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # db revision (create new migration)
    revision_parser = db_subparsers.add_parser(
        "revision",
        help="Create a new migration revision",
    )
    revision_parser.add_argument(
        "-m",
        "--message",
        required=True,
        help="Migration message/description",
    )
    revision_parser.add_argument(
        "--autogenerate",
        action="store_true",
        help="Auto-generate migration from model changes",
    )
    revision_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # db heads
    heads_parser = db_subparsers.add_parser(
        "heads",
        help="Show current available heads",
    )
    heads_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def _get_alembic_config() -> Any:
    """Get Alembic configuration.

    Returns:
        Alembic Config object.

    Raises:
        ImportError: If Alembic is not installed.
        FileNotFoundError: If alembic.ini is not found.
    """
    try:
        from alembic.config import Config
    except ImportError:
        raise ImportError(
            "Alembic is required for database migrations. Install with: pip install alembic"
        )

    # Find alembic.ini
    # Look in current directory, then package root
    ini_paths = [
        "alembic.ini",
        os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini"),
    ]

    ini_path = None
    for path in ini_paths:
        if os.path.exists(path):
            ini_path = os.path.abspath(path)
            break

    if ini_path is None:
        raise FileNotFoundError(
            "alembic.ini not found. Ensure you're running from the project root "
            "or the package is properly installed."
        )

    config = Config(ini_path)

    # Allow database URL override via environment
    db_url = os.getenv("ALEMBIC_DATABASE_URL")
    if not db_url:
        db_path = os.getenv("TENANT_DB_PATH")
        if db_path:
            db_url = f"sqlite:///{db_path}"

    if db_url:
        config.set_main_option("sqlalchemy.url", db_url)

    return config


def cmd_db_upgrade(args: argparse.Namespace) -> int:
    """Handle db upgrade command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success).
    """
    from alembic import command

    try:
        config = _get_alembic_config()

        if args.sql:
            # Generate SQL without executing
            command.upgrade(config, args.revision, sql=True)
        else:
            command.upgrade(config, args.revision)

        result = {
            "success": True,
            "message": f"Database upgraded to {args.revision}",
        }
        output_result(result, args.output)
        return 0

    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
        }
        output_result(result, args.output)
        return 1


def cmd_db_downgrade(args: argparse.Namespace) -> int:
    """Handle db downgrade command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success).
    """
    from alembic import command

    try:
        config = _get_alembic_config()

        if args.sql:
            command.downgrade(config, args.revision, sql=True)
        else:
            command.downgrade(config, args.revision)

        result = {
            "success": True,
            "message": f"Database downgraded to {args.revision}",
        }
        output_result(result, args.output)
        return 0

    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
        }
        output_result(result, args.output)
        return 1


def cmd_db_current(args: argparse.Namespace) -> int:
    """Handle db current command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success).
    """
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine

    try:
        config = _get_alembic_config()
        db_url = config.get_main_option("sqlalchemy.url")
        engine = create_engine(db_url)

        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        if args.output == "json":
            result = {
                "success": True,
                "current_revision": current_rev,
            }
            output_result(result, "json")
        else:
            if current_rev:
                print(f"Current revision: {current_rev}")
            else:
                print("Database has no migration history (not initialized)")

        return 0

    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
        }
        output_result(result, args.output)
        return 1


def cmd_db_history(args: argparse.Namespace) -> int:
    """Handle db history command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success).
    """
    from alembic.script import ScriptDirectory

    try:
        config = _get_alembic_config()
        script = ScriptDirectory.from_config(config)

        revisions: list[dict[str, Any]] = []
        for rev in script.walk_revisions():
            rev_info = {
                "revision": rev.revision,
                "down_revision": rev.down_revision,
                "message": rev.doc or "",
            }
            revisions.append(rev_info)
            if len(revisions) >= args.limit:
                break

        if args.output == "json":
            result = {
                "success": True,
                "revisions": revisions,
            }
            output_result(result, "json")
        else:
            if not revisions:
                print("No migrations found")
            else:
                for rev_dict in revisions:
                    down = rev_dict["down_revision"] or "(base)"
                    print(f"{rev_dict['revision']} -> {down}: {rev_dict['message']}")

        return 0

    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
        }
        output_result(result, args.output)
        return 1


def cmd_db_revision(args: argparse.Namespace) -> int:
    """Handle db revision command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success).
    """
    from alembic import command

    try:
        config = _get_alembic_config()

        script = command.revision(
            config,
            message=args.message,
            autogenerate=args.autogenerate,
        )

        result = {
            "success": True,
            "message": f"Created new revision: {args.message}",
            "revision_id": script.revision if script else None,  # type: ignore[union-attr]
        }
        output_result(result, args.output)
        return 0

    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
        }
        output_result(result, args.output)
        return 1


def cmd_db_heads(args: argparse.Namespace) -> int:
    """Handle db heads command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success).
    """
    from alembic.script import ScriptDirectory

    try:
        config = _get_alembic_config()
        script = ScriptDirectory.from_config(config)

        heads = list(script.get_heads())

        if args.output == "json":
            result = {
                "success": True,
                "heads": heads,
            }
            output_result(result, "json")
        else:
            if not heads:
                print("No heads found")
            else:
                for head in heads:
                    print(f"Head: {head}")

        return 0

    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
        }
        output_result(result, args.output)
        return 1


def handle_db_command(args: argparse.Namespace) -> int:
    """Handle db subcommands.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    handlers = {
        "upgrade": cmd_db_upgrade,
        "downgrade": cmd_db_downgrade,
        "current": cmd_db_current,
        "history": cmd_db_history,
        "revision": cmd_db_revision,
        "heads": cmd_db_heads,
    }

    if not args.db_command:
        print("Usage: mysql-to-sheets db <command>")
        print("Commands: upgrade, downgrade, current, history, revision, heads")
        return 1

    handler = handlers.get(args.db_command)
    if handler:
        return handler(args)

    print(f"Unknown db command: {args.db_command}")
    return 1
