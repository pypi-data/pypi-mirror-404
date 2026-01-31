"""CLI commands for sync configuration management."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from mysql_to_sheets.cli.utils import (
    get_tenant_db_path,
)
from mysql_to_sheets.cli.utils import (
    output_result as base_output_result,
)
from mysql_to_sheets.core.multi_config import (
    DatabaseConfig,
    export_configs_to_file,
    load_config_file,
    validate_config_file,
)
from mysql_to_sheets.models.organizations import get_organization_repository
from mysql_to_sheets.models.sync_configs import (
    VALID_COLUMN_CASES,
    VALID_SYNC_MODES,
    SyncConfigDefinition,
    get_sync_config_repository,
)


def output_result(data: dict[str, Any], format: str) -> None:
    """Output result in the specified format.

    Args:
        data: Result data dictionary.
        format: Output format ('text' or 'json').
    """
    base_output_result(
        data,
        format,
        entity_key="config",
        entity_fields=["id", "name", "sheet_id"],
    )


def add_config_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add config management subcommands.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    config_parser = subparsers.add_parser(
        "config",
        help="Manage sync configurations (multi-tenant)",
    )
    config_subparsers = config_parser.add_subparsers(
        dest="config_command",
        help="Config commands",
    )

    # config add
    config_add = config_subparsers.add_parser(
        "add",
        help="Add a new sync configuration",
    )
    config_add.add_argument(
        "--name",
        required=True,
        help="Configuration name",
    )
    config_add.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    config_add.add_argument(
        "--query",
        required=True,
        help="SQL query to execute",
    )
    config_add.add_argument(
        "--sheet-id",
        required=True,
        help="Google Sheet ID",
    )
    config_add.add_argument(
        "--worksheet",
        default="Sheet1",
        help="Worksheet name (default: Sheet1)",
    )
    config_add.add_argument(
        "--description",
        help="Configuration description",
    )
    config_add.add_argument(
        "--mode",
        choices=list(VALID_SYNC_MODES),
        default="replace",
        help="Sync mode (default: replace)",
    )
    config_add.add_argument(
        "--column-map",
        help='Column mapping as JSON (e.g., \'{"old_col": "New Col"}\')',
    )
    config_add.add_argument(
        "--column-order",
        help="Comma-separated column order",
    )
    config_add.add_argument(
        "--column-case",
        choices=list(VALID_COLUMN_CASES),
        default="none",
        help="Column case transformation",
    )
    config_add.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # config list
    config_list = config_subparsers.add_parser(
        "list",
        help="List sync configurations",
    )
    config_list.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    config_list.add_argument(
        "--enabled-only",
        action="store_true",
        help="Show only enabled configurations",
    )
    config_list.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of configs to list",
    )
    config_list.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # config get
    config_get = config_subparsers.add_parser(
        "get",
        help="Get configuration details",
    )
    config_get.add_argument(
        "--id",
        type=int,
        help="Configuration ID",
    )
    config_get.add_argument(
        "--name",
        help="Configuration name",
    )
    config_get.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    config_get.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # config edit
    config_edit = config_subparsers.add_parser(
        "edit",
        help="Edit a sync configuration",
    )
    config_edit.add_argument(
        "--id",
        type=int,
        required=True,
        help="Configuration ID to edit",
    )
    config_edit.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    config_edit.add_argument(
        "--name",
        help="New configuration name",
    )
    config_edit.add_argument(
        "--query",
        help="New SQL query",
    )
    config_edit.add_argument(
        "--sheet-id",
        help="New Google Sheet ID",
    )
    config_edit.add_argument(
        "--worksheet",
        help="New worksheet name",
    )
    config_edit.add_argument(
        "--description",
        help="New description",
    )
    config_edit.add_argument(
        "--mode",
        choices=list(VALID_SYNC_MODES),
        help="New sync mode",
    )
    config_edit.add_argument(
        "--column-map",
        help="New column mapping as JSON",
    )
    config_edit.add_argument(
        "--column-order",
        help="New comma-separated column order",
    )
    config_edit.add_argument(
        "--column-case",
        choices=list(VALID_COLUMN_CASES),
        help="New column case transformation",
    )
    config_edit.add_argument(
        "--enable",
        action="store_true",
        help="Enable the configuration",
    )
    config_edit.add_argument(
        "--disable",
        action="store_true",
        help="Disable the configuration",
    )
    config_edit.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # config remove
    config_remove = config_subparsers.add_parser(
        "remove",
        help="Remove a sync configuration",
    )
    config_remove.add_argument(
        "--id",
        type=int,
        required=True,
        help="Configuration ID to remove",
    )
    config_remove.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    config_remove.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # config import
    config_import = config_subparsers.add_parser(
        "import",
        help="Import configurations from YAML/JSON file",
    )
    config_import.add_argument(
        "--file",
        required=True,
        help="Path to YAML or JSON configuration file",
    )
    config_import.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    config_import.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip configs with names that already exist",
    )
    config_import.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # config export
    config_export = config_subparsers.add_parser(
        "export",
        help="Export configurations to YAML/JSON file",
    )
    config_export.add_argument(
        "--file",
        required=True,
        help="Output file path (.yaml, .yml, or .json)",
    )
    config_export.add_argument(
        "--org-slug",
        required=True,
        help="Organization slug",
    )
    config_export.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)",
    )
    config_export.add_argument(
        "--enabled-only",
        action="store_true",
        help="Export only enabled configurations",
    )
    config_export.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def handle_config_command(args: argparse.Namespace) -> int:
    """Handle config management commands.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    db_path = get_tenant_db_path()

    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    if args.config_command == "add":
        return _handle_config_add(args, db_path)
    elif args.config_command == "list":
        return _handle_config_list(args, db_path)
    elif args.config_command == "get":
        return _handle_config_get(args, db_path)
    elif args.config_command == "edit":
        return _handle_config_edit(args, db_path)
    elif args.config_command == "remove":
        return _handle_config_remove(args, db_path)
    elif args.config_command == "import":
        return _handle_config_import(args, db_path)
    elif args.config_command == "export":
        return _handle_config_export(args, db_path)
    else:
        print("Error: No config command specified. Use --help for usage.")
        return 1


def _get_organization_id(org_slug: str, db_path: str) -> int | None:
    """Get organization ID from slug.

    Args:
        org_slug: Organization slug.
        db_path: Database path.

    Returns:
        Organization ID or None if not found.
    """
    org_repo = get_organization_repository(db_path)
    org = org_repo.get_by_slug(org_slug)
    return org.id if org else None


def _handle_config_add(args: argparse.Namespace, db_path: str) -> int:
    """Handle config add command."""
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

    # Parse column mapping
    column_mapping = None
    if args.column_map:
        try:
            column_mapping = json.loads(args.column_map)
        except json.JSONDecodeError as e:
            output_result(
                {
                    "success": False,
                    "message": f"Invalid column mapping JSON: {e}",
                },
                args.output,
            )
            return 1

    # Parse column order
    column_order = None
    if args.column_order:
        column_order = [c.strip() for c in args.column_order.split(",")]

    config_repo = get_sync_config_repository(db_path)

    config = SyncConfigDefinition(
        name=args.name,
        description=getattr(args, "description", "") or "",
        sql_query=args.query,
        sheet_id=args.sheet_id,
        worksheet_name=args.worksheet,
        organization_id=org_id,
        sync_mode=args.mode,
        column_mapping=column_mapping,
        column_order=column_order,
        column_case=args.column_case,
    )

    try:
        config = config_repo.create(config)
        output_result(
            {
                "success": True,
                "message": "Configuration created successfully",
                "config": config.to_dict(),
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


def _handle_config_list(args: argparse.Namespace, db_path: str) -> int:
    """Handle config list command."""
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

    config_repo = get_sync_config_repository(db_path)
    configs = config_repo.get_all(
        organization_id=org_id,
        enabled_only=args.enabled_only,
        limit=args.limit,
    )

    if args.output == "json":
        print(
            json.dumps(
                {
                    "success": True,
                    "configs": [c.to_dict() for c in configs],
                    "total": len(configs),
                },
                indent=2,
            )
        )
    else:
        if not configs:
            print("No configurations found.")
        else:
            print(f"Sync Configurations ({len(configs)} found):")
            print("-" * 80)
            for config in configs:
                status = "enabled" if config.enabled else "disabled"
                print(f"  {config.id:4d}  {config.name:30s}  {config.sync_mode:10s}  {status}")
                if config.description:
                    print(f"        {config.description[:50]}...")

    return 0


def _handle_config_get(args: argparse.Namespace, db_path: str) -> int:
    """Handle config get command."""
    if not args.id and not args.name:
        output_result(
            {
                "success": False,
                "message": "Either --id or --name is required",
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

    config_repo = get_sync_config_repository(db_path)

    if args.id:
        config = config_repo.get_by_id(args.id, organization_id=org_id)
    else:
        config = config_repo.get_by_name(args.name, organization_id=org_id)

    if not config:
        output_result(
            {
                "success": False,
                "message": "Configuration not found",
            },
            args.output,
        )
        return 1

    if args.output == "json":
        print(json.dumps({"success": True, "config": config.to_dict()}, indent=2))
    else:
        print(f"Configuration: {config.name}")
        print(f"  ID: {config.id}")
        print(f"  Description: {config.description or '(none)'}")
        print(f"  Status: {'Enabled' if config.enabled else 'Disabled'}")
        print(f"  Sheet ID: {config.sheet_id}")
        print(f"  Worksheet: {config.worksheet_name}")
        print(f"  Sync Mode: {config.sync_mode}")
        print(f"  SQL Query: {config.sql_query[:100]}...")
        if config.column_mapping:
            print(f"  Column Mapping: {config.column_mapping}")
        if config.column_order:
            print(f"  Column Order: {config.column_order}")
        print(f"  Column Case: {config.column_case}")
        print(f"  Created: {config.created_at.isoformat() if config.created_at else 'N/A'}")
        print(f"  Updated: {config.updated_at.isoformat() if config.updated_at else 'N/A'}")

    return 0


def _handle_config_edit(args: argparse.Namespace, db_path: str) -> int:
    """Handle config edit command."""
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

    config_repo = get_sync_config_repository(db_path)
    config = config_repo.get_by_id(args.id, organization_id=org_id)

    if not config:
        output_result(
            {
                "success": False,
                "message": f"Configuration with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    # Apply updates
    if args.name:
        config.name = args.name
    if args.query:
        config.sql_query = args.query
    if args.sheet_id:
        config.sheet_id = args.sheet_id
    if args.worksheet:
        config.worksheet_name = args.worksheet
    if args.description is not None:
        config.description = args.description
    if args.mode:
        config.sync_mode = args.mode
    if args.column_case:
        config.column_case = args.column_case
    if args.enable:
        config.enabled = True
    if args.disable:
        config.enabled = False

    # Parse column mapping
    if args.column_map:
        try:
            config.column_mapping = json.loads(args.column_map)
        except json.JSONDecodeError as e:
            output_result(
                {
                    "success": False,
                    "message": f"Invalid column mapping JSON: {e}",
                },
                args.output,
            )
            return 1

    # Parse column order
    if args.column_order:
        config.column_order = [c.strip() for c in args.column_order.split(",")]

    try:
        config = config_repo.update(config)
        output_result(
            {
                "success": True,
                "message": "Configuration updated successfully",
                "config": config.to_dict(),
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


def _handle_config_remove(args: argparse.Namespace, db_path: str) -> int:
    """Handle config remove command."""
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

    config_repo = get_sync_config_repository(db_path)
    config = config_repo.get_by_id(args.id, organization_id=org_id)

    if not config:
        output_result(
            {
                "success": False,
                "message": f"Configuration with ID {args.id} not found",
            },
            args.output,
        )
        return 1

    config_repo.delete(args.id, organization_id=org_id)

    output_result(
        {
            "success": True,
            "message": f"Configuration '{config.name}' has been removed",
        },
        args.output,
    )
    return 0


def _handle_config_import(args: argparse.Namespace, db_path: str) -> int:
    """Handle config import command."""
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

    file_path = Path(args.file)
    if not file_path.exists():
        output_result(
            {
                "success": False,
                "message": f"File not found: {args.file}",
            },
            args.output,
        )
        return 1

    # Validate file first
    is_valid, errors = validate_config_file(file_path)
    if not is_valid:
        output_result(
            {
                "success": False,
                "message": "Invalid configuration file",
                "errors": errors,
            },
            args.output,
        )
        return 1

    try:
        multi_config = load_config_file(file_path, organization_id=org_id)
    except Exception as e:
        output_result(
            {
                "success": False,
                "message": f"Failed to load configuration file: {e}",
            },
            args.output,
        )
        return 1

    config_repo = get_sync_config_repository(db_path)

    imported = 0
    skipped = 0
    errors = []

    for sync_config in multi_config.syncs:
        try:
            # Check if exists
            existing = config_repo.get_by_name(sync_config.name, organization_id=org_id)
            if existing:
                if args.skip_existing:
                    skipped += 1
                    continue
                else:
                    errors.append(f"Config '{sync_config.name}' already exists")
                    continue

            config_repo.create(sync_config)
            imported += 1
        except ValueError as e:
            errors.append(f"Config '{sync_config.name}': {e}")

    result = {
        "success": len(errors) == 0 or imported > 0,
        "message": f"Imported {imported} configs, skipped {skipped}",
        "imported": imported,
        "skipped": skipped,
    }
    if errors:
        result["errors"] = errors

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Import completed: {imported} imported, {skipped} skipped")
        if errors:
            print("Errors:")
            for err in errors:
                print(f"  - {err}")

    return 0 if imported > 0 or skipped > 0 else 1


def _handle_config_export(args: argparse.Namespace, db_path: str) -> int:
    """Handle config export command."""
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

    config_repo = get_sync_config_repository(db_path)
    configs = config_repo.get_all(
        organization_id=org_id,
        enabled_only=args.enabled_only,
    )

    if not configs:
        output_result(
            {
                "success": False,
                "message": "No configurations to export",
            },
            args.output,
        )
        return 1

    # Create database config from environment (for export template)
    database_config = DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user="${DB_USER}",
        password="${DB_PASSWORD}",
        name="${DB_NAME}",
        db_type=os.getenv("DB_TYPE", "mysql"),
    )

    file_path = Path(args.file)
    try:
        export_configs_to_file(
            configs=configs,
            path=file_path,
            database_config=database_config,
            format=args.format,
        )

        output_result(
            {
                "success": True,
                "message": f"Exported {len(configs)} configurations to {args.file}",
                "count": len(configs),
            },
            args.output,
        )
        return 0
    except Exception as e:
        output_result(
            {
                "success": False,
                "message": f"Failed to export configurations: {e}",
            },
            args.output,
        )
        return 1
