"""Diff and preview functionality for sync operations.

This module provides utilities for computing differences between
database query results and existing Google Sheets data, enabling
preview mode to show changes before applying them.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import gspread

from mysql_to_sheets.core.config import Config
from mysql_to_sheets.core.exceptions import SheetsError


@dataclass
class HeaderChange:
    """Changes detected in sheet headers.

    Attributes:
        added: Column names that will be added.
        removed: Column names that will be removed.
        reordered: Whether column order has changed.
    """

    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    reordered: bool = False


@dataclass
class RowChange:
    """A single row change for preview display.

    Attributes:
        change_type: Type of change ('add', 'remove', 'modify').
        row_index: Index of the row (0-based, excluding header).
        old_values: Previous row values (for remove/modify).
        new_values: New row values (for add/modify).
    """

    change_type: str
    row_index: int
    old_values: list[Any] = field(default_factory=list)
    new_values: list[Any] = field(default_factory=list)


@dataclass
class DiffResult:
    """Result of comparing query data with existing sheet data.

    Attributes:
        has_changes: Whether any changes were detected.
        sheet_row_count: Number of rows currently in the sheet.
        query_row_count: Number of rows from the query.
        rows_to_add: Count of rows to be added.
        rows_to_remove: Count of rows to be removed.
        rows_to_modify: Count of rows to be modified.
        rows_unchanged: Count of rows that are unchanged.
        header_changes: Changes in column headers.
        sample_changes: Sample of row changes for preview.
        message: Human-readable summary of changes.
    """

    has_changes: bool = False
    sheet_row_count: int = 0
    query_row_count: int = 0
    rows_to_add: int = 0
    rows_to_remove: int = 0
    rows_to_modify: int = 0
    rows_unchanged: int = 0
    header_changes: HeaderChange = field(default_factory=HeaderChange)
    sample_changes: list[RowChange] = field(default_factory=list)
    message: str = ""

    def summary(self) -> str:
        """Generate a human-readable summary of changes.

        Returns:
            Summary string like '+50 rows, -10 rows, +2 columns'.
        """
        parts = []

        if self.rows_to_add > 0:
            parts.append(f"+{self.rows_to_add} rows")
        if self.rows_to_remove > 0:
            parts.append(f"-{self.rows_to_remove} rows")
        if self.rows_to_modify > 0:
            parts.append(f"~{self.rows_to_modify} modified")
        if self.header_changes.added:
            parts.append(f"+{len(self.header_changes.added)} columns")
        if self.header_changes.removed:
            parts.append(f"-{len(self.header_changes.removed)} columns")
        if self.header_changes.reordered:
            parts.append("columns reordered")

        if not parts:
            return "No changes"

        return ", ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses.

        Returns:
            Dictionary representation of the diff result.
        """
        return {
            "has_changes": self.has_changes,
            "sheet_row_count": self.sheet_row_count,
            "query_row_count": self.query_row_count,
            "rows_to_add": self.rows_to_add,
            "rows_to_remove": self.rows_to_remove,
            "rows_to_modify": self.rows_to_modify,
            "rows_unchanged": self.rows_unchanged,
            "header_changes": {
                "added": self.header_changes.added,
                "removed": self.header_changes.removed,
                "reordered": self.header_changes.reordered,
            },
            "sample_changes": [
                {
                    "change_type": c.change_type,
                    "row_index": c.row_index,
                    "old_values": c.old_values,
                    "new_values": c.new_values,
                }
                for c in self.sample_changes
            ],
            "message": self.message,
            "summary": self.summary(),
        }


def _normalize_value(value: Any) -> str:
    """Normalize a value for comparison.

    Converts values to strings for consistent comparison between
    database types and sheet values.

    Args:
        value: Value to normalize.

    Returns:
        Normalized string representation.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).upper()
    if isinstance(value, float):
        # Handle floating point comparison
        return f"{value:.10g}"
    return str(value).strip()


def _normalize_row(row: list[Any]) -> tuple[str, ...]:
    """Normalize a row for comparison.

    Args:
        row: List of values.

    Returns:
        Tuple of normalized string values.
    """
    return tuple(_normalize_value(v) for v in row)


def fetch_sheet_data(
    config: Config,
    logger: logging.Logger | None = None,
) -> tuple[list[str], list[list[Any]]]:
    """Fetch current data from Google Sheets.

    Args:
        config: Configuration with Google Sheets settings.
        logger: Optional logger instance.

    Returns:
        Tuple of (headers, rows).

    Raises:
        SheetsError: On Google Sheets API errors.
    """
    from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier

    if logger:
        logger.info(f"Fetching current sheet data from {config.google_sheet_id}")

    try:
        gc = gspread.service_account(filename=config.service_account_file)  # type: ignore[attr-defined]
        spreadsheet = gc.open_by_key(config.google_sheet_id)

        # Resolve worksheet name from GID URL if needed
        try:
            worksheet_name = parse_worksheet_identifier(
                config.google_worksheet_name,
                spreadsheet=spreadsheet,
            )
        except ValueError as e:
            raise SheetsError(
                message=str(e),
                sheet_id=config.google_sheet_id,
                worksheet_name=config.google_worksheet_name,
            ) from e

        worksheet = spreadsheet.worksheet(worksheet_name)

        # Get all values from sheet
        all_values = worksheet.get_all_values()

        if not all_values:
            if logger:
                logger.debug("Sheet is empty")
            return [], []

        # First row is headers
        headers = all_values[0]
        rows = all_values[1:]

        if logger:
            logger.info(f"Fetched {len(rows)} rows and {len(headers)} columns from sheet")

        return headers, rows

    except gspread.exceptions.SpreadsheetNotFound as e:
        raise SheetsError(
            message="Spreadsheet not found",
            sheet_id=config.google_sheet_id,
            original_error=e,
        ) from e
    except gspread.exceptions.WorksheetNotFound as e:
        raise SheetsError(
            message=f"Worksheet '{config.google_worksheet_name}' not found",
            sheet_id=config.google_sheet_id,
            worksheet_name=config.google_worksheet_name,
            original_error=e,
        ) from e
    except (OSError, gspread.exceptions.GSpreadException) as e:
        raise SheetsError(
            message=f"Failed to fetch sheet data: {e}",
            sheet_id=config.google_sheet_id,
            original_error=e,
        ) from e


def compute_header_changes(
    sheet_headers: list[str],
    query_headers: list[str],
) -> HeaderChange:
    """Compute changes between sheet headers and query headers.

    Args:
        sheet_headers: Current headers in the sheet.
        query_headers: Headers from the query.

    Returns:
        HeaderChange describing the differences.
    """
    sheet_set = set(sheet_headers)
    query_set = set(query_headers)

    added = [h for h in query_headers if h not in sheet_set]
    removed = [h for h in sheet_headers if h not in query_set]

    # Check if order changed (only for common columns)
    common_sheet = [h for h in sheet_headers if h in query_set]
    common_query = [h for h in query_headers if h in sheet_set]
    reordered = common_sheet != common_query

    return HeaderChange(
        added=added,
        removed=removed,
        reordered=reordered,
    )


def compute_diff(
    query_headers: list[str],
    query_rows: list[list[Any]],
    sheet_headers: list[str],
    sheet_rows: list[list[Any]],
    max_sample_changes: int = 10,
) -> DiffResult:
    """Compute differences between query results and sheet data.

    For 'replace' mode, this compares the full datasets to identify
    rows to add, remove, or modify.

    Args:
        query_headers: Headers from the database query.
        query_rows: Rows from the database query.
        sheet_headers: Current headers in the sheet.
        sheet_rows: Current rows in the sheet.
        max_sample_changes: Maximum number of sample changes to include.

    Returns:
        DiffResult with change statistics and samples.
    """
    # Compute header changes
    header_changes = compute_header_changes(sheet_headers, query_headers)

    # Normalize rows for comparison
    query_normalized = {_normalize_row(row) for row in query_rows}
    sheet_normalized = {_normalize_row(row) for row in sheet_rows}

    # Find differences
    rows_to_add_set = query_normalized - sheet_normalized
    rows_to_remove_set = sheet_normalized - query_normalized
    unchanged_set = query_normalized & sheet_normalized

    rows_to_add = len(rows_to_add_set)
    rows_to_remove = len(rows_to_remove_set)
    rows_unchanged = len(unchanged_set)

    # Determine if there are changes
    has_changes = (
        rows_to_add > 0
        or rows_to_remove > 0
        or bool(header_changes.added)
        or bool(header_changes.removed)
        or header_changes.reordered
    )

    # Create sample changes
    sample_changes: list[RowChange] = []

    # Sample additions
    add_count = 0
    for i, row in enumerate(query_rows):
        if add_count >= max_sample_changes // 2:
            break
        if _normalize_row(row) in rows_to_add_set:
            sample_changes.append(
                RowChange(
                    change_type="add",
                    row_index=i,
                    new_values=list(row),
                )
            )
            add_count += 1

    # Sample removals
    remove_count = 0
    for i, row in enumerate(sheet_rows):
        if remove_count >= max_sample_changes // 2:
            break
        if _normalize_row(row) in rows_to_remove_set:
            sample_changes.append(
                RowChange(
                    change_type="remove",
                    row_index=i,
                    old_values=list(row),
                )
            )
            remove_count += 1

    # Build result
    result = DiffResult(
        has_changes=has_changes,
        sheet_row_count=len(sheet_rows),
        query_row_count=len(query_rows),
        rows_to_add=rows_to_add,
        rows_to_remove=rows_to_remove,
        rows_to_modify=0,  # For replace mode, we don't track modifications separately
        rows_unchanged=rows_unchanged,
        header_changes=header_changes,
        sample_changes=sample_changes,
    )

    result.message = result.summary()

    return result


def run_preview(
    config: Config,
    query_headers: list[str],
    query_rows: list[list[Any]],
    logger: logging.Logger | None = None,
) -> DiffResult:
    """Run preview mode to compare query results with sheet data.

    Args:
        config: Configuration with Google Sheets settings.
        query_headers: Headers from the database query.
        query_rows: Rows from the database query.
        logger: Optional logger instance.

    Returns:
        DiffResult with change preview.
    """
    if logger:
        logger.info("Running preview mode - comparing with current sheet data")

    # Fetch current sheet data
    sheet_headers, sheet_rows = fetch_sheet_data(config, logger)

    # Compute differences
    diff = compute_diff(
        query_headers=query_headers,
        query_rows=query_rows,
        sheet_headers=sheet_headers,
        sheet_rows=sheet_rows,
    )

    if logger:
        logger.info(f"Preview complete: {diff.summary()}")

    return diff
