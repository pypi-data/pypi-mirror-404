"""SyncResult conversion utilities.

This module provides centralized converters for SyncResult to various
output formats, eliminating duplicated response marshalling code across
the API, Web, and CLI layers.

Usage:
    from mysql_to_sheets.core.sync.converters import (
        sync_result_to_dict,
        sync_result_to_api_response,
    )

    # For API responses (returns SyncResponse Pydantic model)
    return sync_result_to_api_response(result)

    # For JSON/dict output (API, Web, CLI)
    return sync_result_to_dict(result, include_timestamp=True)

    # For CLI JSON output
    return sync_result_to_dict(result, dry_run=args.dry_run)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mysql_to_sheets.api.schemas import DiffResponse, SchemaChangeResponse, SyncResponse
    from mysql_to_sheets.core.diff import DiffResult
    from mysql_to_sheets.core.sync.dataclasses import SyncResult


def diff_result_to_dict(diff: DiffResult | None) -> dict[str, Any] | None:
    """Convert DiffResult to dictionary.

    Provides consistent diff serialization across all layers.

    Args:
        diff: DiffResult to convert, or None.

    Returns:
        Dictionary representation or None.
    """
    if diff is None:
        return None

    return {
        "has_changes": diff.has_changes,
        "sheet_row_count": diff.sheet_row_count,
        "query_row_count": diff.query_row_count,
        "rows_to_add": diff.rows_to_add,
        "rows_to_remove": diff.rows_to_remove,
        "rows_to_modify": getattr(diff, "rows_to_modify", 0),
        "rows_unchanged": diff.rows_unchanged,
        "header_changes": {
            "added": diff.header_changes.added,
            "removed": diff.header_changes.removed,
            "reordered": diff.header_changes.reordered,
        },
        "summary": diff.summary(),
    }


def schema_changes_to_dict(
    schema_changes: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Convert schema changes to dictionary.

    Args:
        schema_changes: Schema change info or None.

    Returns:
        Normalized dictionary or None.
    """
    if schema_changes is None:
        return None

    return {
        "has_changes": schema_changes.get("has_changes", False),
        "added_columns": schema_changes.get("added_columns", []),
        "removed_columns": schema_changes.get("removed_columns", []),
        "reordered": schema_changes.get("reordered", False),
        "expected_headers": schema_changes.get("expected_headers", []),
        "actual_headers": schema_changes.get("actual_headers", []),
        "policy_applied": schema_changes.get("policy_applied"),
    }


@dataclass
class SyncResultConverter:
    """Converter for SyncResult to various output formats.

    Provides a single source of truth for response marshalling.
    Supports options for including/excluding various fields.

    Attributes:
        result: The SyncResult to convert.
        include_timestamp: Whether to include a timestamp field.
        include_dry_run: Whether to include the dry_run field.
        dry_run: Value of dry_run if included.
        include_resumable: Whether to include resumable fields.
        resumable: Value of resumable if included.
        checkpoint_chunk: Checkpoint chunk if resumable.
    """

    result: SyncResult
    include_timestamp: bool = False
    include_dry_run: bool = False
    dry_run: bool = False
    include_resumable: bool = False
    resumable: bool = False
    checkpoint_chunk: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation with all relevant fields.
        """
        data: dict[str, Any] = {
            "success": self.result.success,
            "rows_synced": self.result.rows_synced,
            "columns": self.result.columns,
            "headers": self.result.headers,
            "message": self.result.message,
            "error": self.result.error,
            "preview": self.result.preview,
        }

        # Optional fields
        if self.include_timestamp:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()

        if self.include_dry_run:
            data["dry_run"] = self.dry_run

        if self.include_resumable:
            data["resumable"] = self.resumable
            if self.checkpoint_chunk is not None:
                data["checkpoint_chunk"] = self.checkpoint_chunk

        # Diff - always include if present
        if self.result.diff is not None:
            data["diff"] = diff_result_to_dict(self.result.diff)

        # Schema changes
        if self.result.schema_changes is not None:
            data["schema_changes"] = schema_changes_to_dict(self.result.schema_changes)

        # EC-53 & EC-56: Warnings and empty result indicator
        if self.result.warnings:
            data["warnings"] = self.result.warnings

        if self.result.empty_result_skipped:
            data["empty_result_skipped"] = True

        return data

    def to_api_response(self) -> SyncResponse:
        """Convert to API SyncResponse Pydantic model.

        Returns:
            SyncResponse model for FastAPI endpoints.
        """
        # Import here to avoid circular imports
        from mysql_to_sheets.api.schemas import (
            DiffResponse,
            SchemaChangeResponse,
            SyncResponse,
        )

        diff_response = None
        if self.result.diff is not None:
            diff_response = DiffResponse(
                has_changes=self.result.diff.has_changes,
                sheet_row_count=self.result.diff.sheet_row_count,
                query_row_count=self.result.diff.query_row_count,
                rows_to_add=self.result.diff.rows_to_add,
                rows_to_remove=self.result.diff.rows_to_remove,
                rows_unchanged=self.result.diff.rows_unchanged,
                header_changes={
                    "added": self.result.diff.header_changes.added,
                    "removed": self.result.diff.header_changes.removed,
                    "reordered": self.result.diff.header_changes.reordered,
                },
                summary=self.result.diff.summary(),
            )

        schema_response = None
        if self.result.schema_changes is not None:
            schema_response = SchemaChangeResponse(
                has_changes=self.result.schema_changes.get("has_changes", False),
                added_columns=self.result.schema_changes.get("added_columns", []),
                removed_columns=self.result.schema_changes.get("removed_columns", []),
                reordered=self.result.schema_changes.get("reordered", False),
                expected_headers=self.result.schema_changes.get("expected_headers", []),
                actual_headers=self.result.schema_changes.get("actual_headers", []),
                policy_applied=self.result.schema_changes.get("policy_applied"),
            )

        return SyncResponse(
            success=self.result.success,
            rows_synced=self.result.rows_synced,
            columns=self.result.columns,
            headers=self.result.headers,
            message=self.result.message,
            error=self.result.error,
            preview=self.result.preview,
            diff=diff_response,
            schema_changes=schema_response,
            resumable=self.resumable,
            checkpoint_chunk=self.checkpoint_chunk,
        )

    def to_cli_dict(self) -> dict[str, Any]:
        """Convert to CLI-friendly dictionary.

        Includes timestamp and dry_run by default for CLI output.

        Returns:
            Dictionary for CLI JSON output.
        """
        return SyncResultConverter(
            result=self.result,
            include_timestamp=True,
            include_dry_run=self.include_dry_run,
            dry_run=self.dry_run,
            include_resumable=self.include_resumable,
            resumable=self.resumable,
            checkpoint_chunk=self.checkpoint_chunk,
        ).to_dict()


# Convenience functions


def sync_result_to_dict(
    result: SyncResult,
    *,
    include_timestamp: bool = False,
    include_dry_run: bool = False,
    dry_run: bool = False,
    include_resumable: bool = False,
    resumable: bool = False,
    checkpoint_chunk: int | None = None,
) -> dict[str, Any]:
    """Convert SyncResult to dictionary.

    Convenience function that wraps SyncResultConverter.to_dict().

    Args:
        result: SyncResult to convert.
        include_timestamp: Whether to include timestamp field.
        include_dry_run: Whether to include dry_run field.
        dry_run: Value of dry_run if included.
        include_resumable: Whether to include resumable fields.
        resumable: Value of resumable if included.
        checkpoint_chunk: Checkpoint chunk if resumable.

    Returns:
        Dictionary representation.

    Example:
        result = run_sync(config)
        data = sync_result_to_dict(result, include_timestamp=True)
        return jsonify(data)
    """
    return SyncResultConverter(
        result=result,
        include_timestamp=include_timestamp,
        include_dry_run=include_dry_run,
        dry_run=dry_run,
        include_resumable=include_resumable,
        resumable=resumable,
        checkpoint_chunk=checkpoint_chunk,
    ).to_dict()


def sync_result_to_api_response(
    result: SyncResult,
    *,
    resumable: bool = False,
    checkpoint_chunk: int | None = None,
) -> SyncResponse:
    """Convert SyncResult to API SyncResponse.

    Convenience function for FastAPI endpoints.

    Args:
        result: SyncResult to convert.
        resumable: Whether this was a resumable sync.
        checkpoint_chunk: Checkpoint chunk if resumable.

    Returns:
        SyncResponse Pydantic model.

    Example:
        @router.post("/sync", response_model=SyncResponse)
        async def execute_sync(request: SyncRequest):
            config = apply_request_overrides(request)
            result = run_sync(config)
            return sync_result_to_api_response(result)
    """
    return SyncResultConverter(
        result=result,
        include_resumable=resumable or checkpoint_chunk is not None,
        resumable=resumable,
        checkpoint_chunk=checkpoint_chunk,
    ).to_api_response()


def sync_result_to_web_dict(
    result: SyncResult,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Convert SyncResult to dictionary for web dashboard.

    Includes dry_run flag for web context.

    Args:
        result: SyncResult to convert.
        dry_run: Whether this was a dry run.

    Returns:
        Dictionary for Flask jsonify.

    Example:
        result = run_sync(config, dry_run=dry_run)
        return jsonify(sync_result_to_web_dict(result, dry_run=dry_run))
    """
    return sync_result_to_dict(
        result,
        include_dry_run=True,
        dry_run=dry_run,
    )


__all__ = [
    "SyncResultConverter",
    "diff_result_to_dict",
    "schema_changes_to_dict",
    "sync_result_to_api_response",
    "sync_result_to_dict",
    "sync_result_to_web_dict",
]
