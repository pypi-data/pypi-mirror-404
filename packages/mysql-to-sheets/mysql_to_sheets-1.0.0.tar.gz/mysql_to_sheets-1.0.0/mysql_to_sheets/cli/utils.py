"""Shared utility functions for CLI commands.

This module extracts common functionality used across multiple CLI command files
to eliminate code duplication and provide a consistent interface.
"""

import json
import os
from typing import Any

# Default tenant database path
DEFAULT_TENANT_DB_PATH = "./data/tenant.db"


def get_tenant_db_path() -> str:
    """Get tenant database path from environment.

    Returns:
        Path to the tenant database file.
    """
    return os.getenv("TENANT_DB_PATH", DEFAULT_TENANT_DB_PATH)


def ensure_data_dir(db_path: str | None = None) -> str:
    """Ensure data directory exists and return db path.

    Args:
        db_path: Optional database path. Uses default if not provided.

    Returns:
        The database path with directory created.
    """
    path = db_path or get_tenant_db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    return path


def output_result(
    data: dict[str, Any],
    format: str,
    entity_key: str | None = None,
    entity_fields: list[str] | None = None,
) -> None:
    """Output result in the specified format.

    Args:
        data: Result data dictionary.
        format: Output format ('text' or 'json').
        entity_key: Optional key for entity data (e.g., 'user', 'organization').
        entity_fields: Optional list of fields to display for the entity.
    """
    if format == "json":
        print(json.dumps(data, indent=2, default=str))
    else:
        if data.get("success"):
            print(f"Success: {data.get('message', 'Operation completed')}")

            # Display entity fields if provided
            if entity_key and entity_key in data and entity_fields:
                entity = data[entity_key]
                for field in entity_fields:
                    if field in entity:
                        # Convert field name from snake_case to display format
                        display_name = field.replace("_", " ").title()
                        print(f"  {display_name}: {entity[field]}")

            # Display sync-specific fields
            if data.get("rows_synced") is not None:
                print(f"  Rows synced: {data['rows_synced']}")
            if data.get("columns") is not None:
                print(f"  Columns: {data['columns']}")

            # Show preview/diff information
            if data.get("preview") and data.get("diff"):
                diff = data["diff"]
                print("\n  Preview Summary:")
                print(f"    Current sheet rows: {diff.get('sheet_row_count', 0)}")
                print(f"    Query result rows: {diff.get('query_row_count', 0)}")
                if diff.get("rows_to_add", 0) > 0:
                    print(f"    Rows to add: +{diff['rows_to_add']}")
                if diff.get("rows_to_remove", 0) > 0:
                    print(f"    Rows to remove: -{diff['rows_to_remove']}")
                if diff.get("rows_unchanged", 0) > 0:
                    print(f"    Rows unchanged: {diff['rows_unchanged']}")

                header_changes = diff.get("header_changes", {})
                if header_changes.get("added"):
                    print(f"    Columns to add: {', '.join(header_changes['added'])}")
                if header_changes.get("removed"):
                    print(f"    Columns to remove: {', '.join(header_changes['removed'])}")
        else:
            # Format error output with error code if available
            error_code = data.get("code")
            message = data.get("message", data.get("error", "Operation failed"))

            if error_code:
                print(f"Error [{error_code}]: {message}")
            else:
                print(f"Error: {message}")

            # Show remediation hint if available
            if data.get("remediation"):
                print(f"  Hint: {data['remediation']}")

            # Show error category for context
            if data.get("category"):
                category = data["category"]
                if category == "transient":
                    print("  Note: This error may be temporary. Retry may succeed.")
                elif category == "config":
                    print("  Note: This is a configuration issue. Check your settings.")

            # Show detailed errors
            if data.get("errors"):
                for error in data["errors"]:
                    print(f"  - {error}")


def output_user_result(data: dict[str, Any], format: str) -> None:
    """Output user-related result with standard fields.

    Args:
        data: Result data dictionary.
        format: Output format ('text' or 'json').
    """
    output_result(
        data,
        format,
        entity_key="user",
        entity_fields=["id", "email", "display_name", "role"],
    )


def output_org_result(data: dict[str, Any], format: str) -> None:
    """Output organization-related result with standard fields.

    Args:
        data: Result data dictionary.
        format: Output format ('text' or 'json').
    """
    output_result(
        data,
        format,
        entity_key="organization",
        entity_fields=["id", "name", "slug"],
    )


def get_organization_id(org_slug: str, db_path: str | None = None) -> int | None:
    """Get organization ID from slug.

    Args:
        org_slug: Organization slug.
        db_path: Optional database path. Uses default if not provided.

    Returns:
        Organization ID or None if not found.
    """
    from mysql_to_sheets.models.organizations import get_organization_repository

    path = db_path or get_tenant_db_path()
    org_repo = get_organization_repository(path)
    org = org_repo.get_by_slug(org_slug)
    return org.id if org else None


def format_table(
    headers: list[str],
    rows: list[list[Any]],
    widths: list[int] | None = None,
) -> str:
    """Format data as a simple text table.

    Args:
        headers: Column headers.
        rows: Data rows.
        widths: Optional column widths. Auto-calculated if not provided.

    Returns:
        Formatted table string.
    """
    if not widths:
        widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(str(val)))

    lines = []

    # Header
    header_parts = [str(h).ljust(widths[i]) for i, h in enumerate(headers)]
    lines.append("  ".join(header_parts))

    # Separator
    lines.append("-" * (sum(widths) + 2 * (len(widths) - 1)))

    # Rows
    for row in rows:
        row_parts = [str(v).ljust(widths[i]) for i, v in enumerate(row)]
        lines.append("  ".join(row_parts))

    return "\n".join(lines)
