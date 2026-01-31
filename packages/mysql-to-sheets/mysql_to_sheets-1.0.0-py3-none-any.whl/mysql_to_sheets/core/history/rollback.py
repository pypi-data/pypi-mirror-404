"""Rollback service for restoring sheet state from snapshots.

This module provides functions to preview and execute rollbacks
from snapshots, allowing users to restore Google Sheets to a
previous state captured before a sync operation.
"""

import logging
from dataclasses import dataclass
from typing import Any

import gspread

from mysql_to_sheets.core.config import Config
from mysql_to_sheets.core.diff import DiffResult, compute_diff, fetch_sheet_data
from mysql_to_sheets.core.history.snapshots import (
    create_snapshot,
    get_snapshot,
    get_snapshot_data,
)


def _col_letter(col_num: int) -> str:
    """Convert a column number (1-indexed) to Excel-style column letter.

    Args:
        col_num: Column number (1=A, 26=Z, 27=AA, etc.)

    Returns:
        Column letter string.

    Examples:
        >>> _col_letter(1)
        'A'
        >>> _col_letter(26)
        'Z'
        >>> _col_letter(27)
        'AA'
    """
    result = ""
    while col_num > 0:
        col_num, remainder = divmod(col_num - 1, 26)
        result = chr(65 + remainder) + result
    return result


@dataclass
class RollbackResult:
    """Result of a rollback operation.

    Attributes:
        success: Whether the rollback completed successfully.
        snapshot_id: ID of the snapshot that was restored.
        rows_restored: Number of rows restored.
        columns_restored: Number of columns restored.
        backup_snapshot_id: ID of the backup snapshot created before rollback.
        message: Human-readable status message.
        error: Error details if rollback failed.
    """

    success: bool
    snapshot_id: int
    rows_restored: int = 0
    columns_restored: int = 0
    backup_snapshot_id: int | None = None
    message: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "success": self.success,
            "snapshot_id": self.snapshot_id,
            "rows_restored": self.rows_restored,
            "columns_restored": self.columns_restored,
            "backup_snapshot_id": self.backup_snapshot_id,
            "message": self.message,
            "error": self.error,
        }


@dataclass
class RollbackPreview:
    """Preview of what a rollback would change.

    Attributes:
        snapshot_id: ID of the snapshot to restore.
        snapshot_created_at: When the snapshot was created.
        current_row_count: Current number of rows in sheet.
        snapshot_row_count: Number of rows in snapshot.
        current_column_count: Current number of columns in sheet.
        snapshot_column_count: Number of columns in snapshot.
        diff: Detailed diff showing changes.
        message: Human-readable summary.
    """

    snapshot_id: int
    snapshot_created_at: str | None = None
    current_row_count: int = 0
    snapshot_row_count: int = 0
    current_column_count: int = 0
    snapshot_column_count: int = 0
    diff: DiffResult | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            "snapshot_id": self.snapshot_id,
            "snapshot_created_at": self.snapshot_created_at,
            "current_row_count": self.current_row_count,
            "snapshot_row_count": self.snapshot_row_count,
            "current_column_count": self.current_column_count,
            "snapshot_column_count": self.snapshot_column_count,
            "message": self.message,
        }
        if self.diff:
            result["diff"] = self.diff.to_dict()  # type: ignore[assignment]
        return result


def preview_rollback(
    snapshot_id: int,
    organization_id: int,
    config: Config,
    db_path: str | None = None,
    logger: logging.Logger | None = None,
) -> RollbackPreview:
    """Preview what changes a rollback would make.

    Compares the snapshot data with current sheet data to show
    what would change if the rollback is executed.

    Args:
        snapshot_id: ID of the snapshot to preview.
        organization_id: Organization ID for access control.
        config: Configuration with Google Sheets settings.
        db_path: Path to snapshot database. Uses config.tenant_db_path if None.
        logger: Optional logger instance.

    Returns:
        RollbackPreview with diff information.

    Raises:
        ValueError: If snapshot not found or data corrupted.
        SheetsError: On Google Sheets API errors.
    """
    db_path = db_path or config.tenant_db_path

    if logger:
        logger.info(f"Previewing rollback to snapshot {snapshot_id}")

    # Get snapshot metadata
    snapshot = get_snapshot(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        db_path=db_path,
        include_data=False,
        logger=logger,
    )

    if snapshot is None:
        raise ValueError(f"Snapshot {snapshot_id} not found")

    # Get snapshot data
    snapshot_data = get_snapshot_data(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        db_path=db_path,
        logger=logger,
    )

    if snapshot_data is None:
        raise ValueError(f"Snapshot {snapshot_id} data not found")

    snapshot_headers, snapshot_rows = snapshot_data

    # Fetch current sheet data
    current_headers, current_rows = fetch_sheet_data(config, logger)

    # Compute diff (snapshot is "new" data, current is "old" data)
    diff = compute_diff(
        query_headers=snapshot_headers,
        query_rows=snapshot_rows,
        sheet_headers=current_headers,
        sheet_rows=current_rows,
    )

    preview = RollbackPreview(
        snapshot_id=snapshot_id,
        snapshot_created_at=snapshot.created_at.isoformat() if snapshot.created_at else None,
        current_row_count=len(current_rows),
        snapshot_row_count=len(snapshot_rows),
        current_column_count=len(current_headers),
        snapshot_column_count=len(snapshot_headers),
        diff=diff,
        message=f"Rollback would restore {len(snapshot_rows)} rows from snapshot taken at {snapshot.created_at}",
    )

    if logger:
        logger.info(f"Preview complete: {diff.summary()}")

    return preview


def rollback_to_snapshot(
    snapshot_id: int,
    organization_id: int,
    config: Config,
    db_path: str | None = None,
    create_backup: bool = True,
    logger: logging.Logger | None = None,
) -> RollbackResult:
    """Execute a rollback to restore sheet from snapshot.

    This function:
    1. Optionally creates a backup snapshot of current state
    2. Clears the sheet
    3. Pushes snapshot data to the sheet

    Args:
        snapshot_id: ID of the snapshot to restore.
        organization_id: Organization ID for access control.
        config: Configuration with Google Sheets settings.
        db_path: Path to snapshot database. Uses config.tenant_db_path if None.
        create_backup: Whether to create a backup snapshot before rollback.
        logger: Optional logger instance.

    Returns:
        RollbackResult with operation status.

    Raises:
        ValueError: If snapshot not found or data corrupted.
        SheetsError: On Google Sheets API errors.
    """
    db_path = db_path or config.tenant_db_path

    if logger:
        logger.info(f"Starting rollback to snapshot {snapshot_id}")

    # Get snapshot data
    snapshot_data = get_snapshot_data(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        db_path=db_path,
        logger=logger,
    )

    if snapshot_data is None:
        return RollbackResult(
            success=False,
            snapshot_id=snapshot_id,
            error=f"Snapshot {snapshot_id} not found",
            message="Rollback failed: snapshot not found",
        )

    snapshot_headers, snapshot_rows = snapshot_data

    # Get snapshot metadata
    snapshot = get_snapshot(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        db_path=db_path,
        include_data=False,
        logger=logger,
    )

    backup_snapshot_id = None

    try:
        # Create backup snapshot of current state
        if create_backup:
            if logger:
                logger.info("Creating backup snapshot of current state")
            backup_snapshot = create_snapshot(
                config=config,
                organization_id=organization_id,
                db_path=db_path,
                logger=logger,
            )
            backup_snapshot_id = backup_snapshot.id
            if logger:
                logger.info(f"Backup snapshot created: {backup_snapshot_id}")

        # Push snapshot data to sheet
        if logger:
            logger.info(f"Restoring {len(snapshot_rows)} rows to sheet")

        from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier

        gc = gspread.service_account(filename=config.service_account_file)  # type: ignore[attr-defined]
        spreadsheet = gc.open_by_key(config.google_sheet_id)

        # Resolve worksheet name from GID URL if needed
        try:
            worksheet_name = parse_worksheet_identifier(
                config.google_worksheet_name,
                spreadsheet=spreadsheet,
            )
        except ValueError as e:
            return RollbackResult(
                success=False,
                snapshot_id=snapshot_id,
                backup_snapshot_id=backup_snapshot_id,
                error=str(e),
                message="Rollback failed: worksheet GID resolution failed",
            )

        worksheet = spreadsheet.worksheet(worksheet_name)

        # Overwrite from A1 with snapshot data (avoids clearing first)
        if snapshot_rows or snapshot_headers:
            all_data = [snapshot_headers] + snapshot_rows
            worksheet.update(
                values=all_data,
                range_name="A1",
                value_input_option="USER_ENTERED",  # type: ignore[arg-type]
            )

            # Get current sheet dimensions
            current_row_count = worksheet.row_count
            current_col_count = worksheet.col_count
            snapshot_row_count = len(all_data)
            snapshot_col_count = len(snapshot_headers) if snapshot_headers else 0

            # Build list of ranges to clear
            ranges_to_clear = []

            # Clear extra rows (full width of current sheet)
            if current_row_count > snapshot_row_count:
                ranges_to_clear.append(
                    f"A{snapshot_row_count + 1}:{_col_letter(current_col_count)}{current_row_count}"
                )

            # Clear extra columns (only for rows within snapshot range)
            if snapshot_col_count > 0 and current_col_count > snapshot_col_count:
                ranges_to_clear.append(
                    f"{_col_letter(snapshot_col_count + 1)}1:"
                    f"{_col_letter(current_col_count)}{snapshot_row_count}"
                )

            if ranges_to_clear:
                worksheet.batch_clear(ranges_to_clear)
                if logger:
                    logger.debug(f"Cleared ranges: {ranges_to_clear}")
        else:
            # Empty snapshot: clear entire sheet
            worksheet.clear()

        if logger:
            logger.info(
                f"Rollback complete: restored {len(snapshot_rows)} rows, "
                f"{len(snapshot_headers)} columns"
            )

        return RollbackResult(
            success=True,
            snapshot_id=snapshot_id,
            rows_restored=len(snapshot_rows),
            columns_restored=len(snapshot_headers),
            backup_snapshot_id=backup_snapshot_id,
            message=f"Successfully restored sheet from snapshot {snapshot_id}",
        )

    except gspread.exceptions.SpreadsheetNotFound:
        error_msg = "Spreadsheet not found. Ensure the Service Account has access."
        if logger:
            logger.error(error_msg)
        return RollbackResult(
            success=False,
            snapshot_id=snapshot_id,
            backup_snapshot_id=backup_snapshot_id,
            error=error_msg,
            message="Rollback failed: spreadsheet not found",
        )

    except gspread.exceptions.WorksheetNotFound:
        error_msg = f"Worksheet '{config.google_worksheet_name}' not found"
        if logger:
            logger.error(error_msg)
        return RollbackResult(
            success=False,
            snapshot_id=snapshot_id,
            backup_snapshot_id=backup_snapshot_id,
            error=error_msg,
            message="Rollback failed: worksheet not found",
        )

    except gspread.exceptions.APIError as e:
        error_msg = f"Google Sheets API error: {e}"
        if logger:
            logger.error(error_msg)
        return RollbackResult(
            success=False,
            snapshot_id=snapshot_id,
            backup_snapshot_id=backup_snapshot_id,
            error=error_msg,
            message="Rollback failed: API error",
        )

    except (OSError, RuntimeError, ValueError, KeyError) as e:
        error_msg = f"Unexpected error during rollback: {e}"
        if logger:
            logger.error(error_msg)
        return RollbackResult(
            success=False,
            snapshot_id=snapshot_id,
            backup_snapshot_id=backup_snapshot_id,
            error=error_msg,
            message="Rollback failed: unexpected error",
        )


def can_rollback(
    snapshot_id: int,
    organization_id: int,
    config: Config,
    db_path: str | None = None,
    logger: logging.Logger | None = None,
) -> tuple[bool, str]:
    """Check if a rollback can be performed.

    Verifies that:
    1. The snapshot exists
    2. The snapshot belongs to the correct organization
    3. The snapshot data is not corrupted
    4. The target sheet and worksheet exist
    5. Schema compatibility (warns if snapshot has fewer columns)

    Args:
        snapshot_id: ID of the snapshot to check.
        organization_id: Organization ID for access control.
        config: Configuration with Google Sheets settings.
        db_path: Path to snapshot database.
        logger: Optional logger instance.

    Returns:
        Tuple of (can_rollback, reason_message).
        The message may include warnings about schema compatibility.
    """
    db_path = db_path or config.tenant_db_path

    # Check snapshot exists
    snapshot = get_snapshot(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        db_path=db_path,
        include_data=True,
        logger=logger,
    )

    if snapshot is None:
        return False, f"Snapshot {snapshot_id} not found"

    # Verify checksum
    if not snapshot.verify_checksum():
        return False, f"Snapshot {snapshot_id} data is corrupted"

    # Check sheet matches
    if snapshot.sheet_id != config.google_sheet_id:
        return False, (
            f"Snapshot is for sheet {snapshot.sheet_id}, "
            f"but config specifies {config.google_sheet_id}"
        )

    if snapshot.worksheet_name != config.google_worksheet_name:
        return False, (
            f"Snapshot is for worksheet '{snapshot.worksheet_name}', "
            f"but config specifies '{config.google_worksheet_name}'"
        )

    # Check sheet accessibility and schema compatibility
    from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier

    warnings: list[str] = []
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
            return False, str(e)

        worksheet = spreadsheet.worksheet(worksheet_name)

        # Check schema compatibility: compare actual column headers
        current_data = worksheet.get_all_values()
        current_headers = current_data[0] if current_data else []
        current_col_count = len(current_headers)

        # Get actual snapshot headers (not just metadata column count)
        snapshot_data = snapshot.get_data()
        if snapshot_data:
            snapshot_headers, _ = snapshot_data
            snapshot_col_count = len(snapshot_headers)
        else:
            # Fall back to metadata if data retrieval fails
            snapshot_headers = []
            snapshot_col_count = snapshot.column_count

        # Column count mismatch warnings
        if snapshot_col_count < current_col_count:
            warnings.append(
                f"Warning: Snapshot has {snapshot_col_count} columns but sheet "
                f"currently has {current_col_count} columns. Extra columns will be cleared."
            )
            if logger:
                logger.warning(warnings[-1])
        elif snapshot_col_count > current_col_count:
            warnings.append(
                f"Warning: Snapshot has {snapshot_col_count} columns but sheet "
                f"currently has {current_col_count} columns. New columns will be added."
            )
            if logger:
                logger.warning(warnings[-1])

        # Column name mismatch warnings (if both have headers)
        if current_headers and snapshot_headers:
            # Check for header differences in overlapping columns
            min_cols = min(len(current_headers), len(snapshot_headers))
            mismatched_cols = []
            for i in range(min_cols):
                if current_headers[i] != snapshot_headers[i]:
                    mismatched_cols.append(
                        f"Column {i+1}: '{current_headers[i]}' → '{snapshot_headers[i]}'"
                    )

            if mismatched_cols:
                warnings.append(
                    f"Warning: Column header mismatch detected. "
                    f"The following columns will change: {'; '.join(mismatched_cols[:5])}"
                    + (" (and more)" if len(mismatched_cols) > 5 else "")
                )
                if logger:
                    logger.warning(warnings[-1])

    except gspread.exceptions.SpreadsheetNotFound:
        return False, "Target spreadsheet not found or not accessible"
    except gspread.exceptions.WorksheetNotFound:
        return False, f"Target worksheet '{config.google_worksheet_name}' not found"
    except (OSError, gspread.exceptions.GSpreadException) as e:
        return False, f"Cannot access target sheet: {e}"

    message = "Rollback can proceed"
    if warnings:
        message = f"{message}. {' '.join(warnings)}"

    return True, message
