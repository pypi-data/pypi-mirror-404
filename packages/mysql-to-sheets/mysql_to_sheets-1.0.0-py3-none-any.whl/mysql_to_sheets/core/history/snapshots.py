"""Snapshot service for capturing sheet state before sync.

This module provides functions to create, retrieve, and manage
snapshots of Google Sheet data. Snapshots are compressed and
stored in SQLite for efficient storage.
"""

import hashlib
import json
import logging
import zlib
from typing import Any

import gspread

from mysql_to_sheets.core.config import Config
from mysql_to_sheets.core.exceptions import SheetsError
from mysql_to_sheets.models.snapshots import (
    Snapshot,
    get_snapshot_repository,
)


def _fetch_sheet_data(
    config: Config,
    logger: logging.Logger | None = None,
) -> tuple[list[str], list[list[Any]]]:
    """Fetch all data from a Google Sheet.

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
        logger.debug(f"Fetching sheet data from {config.google_sheet_id}")

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

        all_values = worksheet.get_all_values()

        if not all_values:
            if logger:
                logger.debug("Sheet is empty")
            return [], []

        headers = all_values[0]
        rows = all_values[1:]

        if logger:
            logger.debug(f"Fetched {len(rows)} rows and {len(headers)} columns")

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


def _compress_data(
    headers: list[str],
    rows: list[list[Any]],
) -> tuple[bytes, int, str]:
    """Compress sheet data and compute checksum.

    Args:
        headers: Column headers.
        rows: Data rows.

    Returns:
        Tuple of (compressed_data, original_size, checksum).
    """
    data = {"headers": headers, "rows": rows}
    json_str = json.dumps(data, default=str)
    json_bytes = json_str.encode("utf-8")
    original_size = len(json_bytes)

    # Compress using zlib (level 6 is good balance of speed/compression)
    compressed = zlib.compress(json_bytes, level=6)

    # Compute SHA256 checksum of compressed data
    checksum = hashlib.sha256(compressed).hexdigest()

    return compressed, original_size, checksum


def estimate_sheet_size(
    config: Config,
    logger: logging.Logger | None = None,
) -> int:
    """Estimate the size of a sheet in bytes without fetching all data.

    This is a rough estimate based on row/column counts and average cell size.

    Args:
        config: Configuration with Google Sheets settings.
        logger: Optional logger instance.

    Returns:
        Estimated size in bytes.

    Raises:
        SheetsError: On Google Sheets API errors.
    """
    from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier

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

        # Get row and column counts
        row_count = worksheet.row_count
        col_count = worksheet.col_count

        # Estimate ~50 bytes per cell on average (accounts for JSON overhead)
        estimated_size = row_count * col_count * 50

        if logger:
            logger.debug(
                f"Estimated sheet size: {estimated_size} bytes "
                f"({row_count} rows x {col_count} cols)"
            )

        return estimated_size

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
            message=f"Failed to estimate sheet size: {e}",
            sheet_id=config.google_sheet_id,
            original_error=e,
        ) from e


def create_snapshot(
    config: Config,
    organization_id: int,
    db_path: str | None = None,
    sync_config_id: int | None = None,
    logger: logging.Logger | None = None,
) -> Snapshot:
    """Create a snapshot of the current sheet state.

    Fetches all data from the Google Sheet, compresses it, and stores
    it in the database for later rollback.

    Args:
        config: Configuration with Google Sheets settings.
        organization_id: Organization ID for multi-tenant scoping.
        db_path: Path to snapshot database. Uses config.tenant_db_path if None.
        sync_config_id: Optional sync config ID to associate with snapshot.
        logger: Optional logger instance.

    Returns:
        Created Snapshot with ID and timestamp.

    Raises:
        SheetsError: On Google Sheets API errors.
    """
    if logger:
        logger.info(
            f"Creating snapshot for sheet {config.google_sheet_id} "
            f"worksheet '{config.google_worksheet_name}'"
        )

    # Fetch current sheet data
    headers, rows = _fetch_sheet_data(config, logger)

    # Compress data
    compressed, original_size, checksum = _compress_data(headers, rows)

    if logger:
        compression_ratio = len(compressed) / original_size if original_size > 0 else 0
        logger.debug(
            f"Compressed {original_size} bytes to {len(compressed)} bytes ({compression_ratio:.1%})"
        )

    # Create snapshot record
    snapshot = Snapshot(
        organization_id=organization_id,
        sync_config_id=sync_config_id,
        sheet_id=config.google_sheet_id,
        worksheet_name=config.google_worksheet_name,
        row_count=len(rows),
        column_count=len(headers),
        size_bytes=len(compressed),
        data_compressed=compressed,
        checksum=checksum,
        headers=headers,
    )

    # Store in database
    db_path = db_path or config.tenant_db_path
    repo = get_snapshot_repository(db_path)
    snapshot = repo.add(snapshot)

    if logger:
        logger.info(
            f"Created snapshot {snapshot.id}: {len(rows)} rows, "
            f"{len(headers)} columns, {len(compressed)} bytes"
        )

    return snapshot


def get_snapshot(
    snapshot_id: int,
    organization_id: int,
    db_path: str,
    include_data: bool = False,
    logger: logging.Logger | None = None,
) -> Snapshot | None:
    """Retrieve a snapshot by ID.

    Args:
        snapshot_id: Snapshot ID to retrieve.
        organization_id: Organization ID for access control.
        db_path: Path to snapshot database.
        include_data: Whether to include compressed data.
        logger: Optional logger instance.

    Returns:
        Snapshot if found, None otherwise.
    """
    repo = get_snapshot_repository(db_path)
    snapshot = repo.get(snapshot_id, organization_id, include_data=include_data)

    if logger:
        if snapshot:
            logger.debug(f"Retrieved snapshot {snapshot_id}")
        else:
            logger.debug(f"Snapshot {snapshot_id} not found")

    return snapshot


def list_snapshots(
    organization_id: int,
    db_path: str,
    sheet_id: str | None = None,
    worksheet_name: str | None = None,
    sync_config_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
    logger: logging.Logger | None = None,
) -> list[Snapshot]:
    """List snapshots with optional filters.

    Args:
        organization_id: Organization to query.
        db_path: Path to snapshot database.
        sheet_id: Filter by Google Sheet ID.
        worksheet_name: Filter by worksheet name.
        sync_config_id: Filter by sync config ID.
        limit: Maximum results (default 10).
        offset: Results to skip.
        logger: Optional logger instance.

    Returns:
        List of matching snapshots (without data).
    """
    repo = get_snapshot_repository(db_path)
    snapshots = repo.list(
        organization_id=organization_id,
        sheet_id=sheet_id,
        worksheet_name=worksheet_name,
        sync_config_id=sync_config_id,
        limit=limit,
        offset=offset,
    )

    if logger:
        logger.debug(f"Found {len(snapshots)} snapshots")

    return snapshots


def delete_snapshot(
    snapshot_id: int,
    organization_id: int,
    db_path: str,
    logger: logging.Logger | None = None,
) -> bool:
    """Delete a snapshot.

    Args:
        snapshot_id: Snapshot ID to delete.
        organization_id: Organization ID for access control.
        db_path: Path to snapshot database.
        logger: Optional logger instance.

    Returns:
        True if deleted, False if not found.
    """
    repo = get_snapshot_repository(db_path)
    deleted = repo.delete(snapshot_id, organization_id)

    if logger:
        if deleted:
            logger.info(f"Deleted snapshot {snapshot_id}")
        else:
            logger.debug(f"Snapshot {snapshot_id} not found for deletion")

    return deleted


def get_snapshot_data(
    snapshot_id: int,
    organization_id: int,
    db_path: str,
    logger: logging.Logger | None = None,
) -> tuple[list[str], list[list[Any]]] | None:
    """Retrieve and decompress snapshot data.

    Args:
        snapshot_id: Snapshot ID to retrieve.
        organization_id: Organization ID for access control.
        db_path: Path to snapshot database.
        logger: Optional logger instance.

    Returns:
        Tuple of (headers, rows) if found, None otherwise.

    Raises:
        ValueError: If data is corrupted.
    """
    snapshot = get_snapshot(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        db_path=db_path,
        include_data=True,
        logger=logger,
    )

    if snapshot is None:
        return None

    # Verify checksum before returning
    if not snapshot.verify_checksum():
        raise ValueError(f"Snapshot {snapshot_id} data is corrupted (checksum mismatch)")

    return snapshot.get_data()


def get_snapshot_stats(
    organization_id: int,
    db_path: str,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Get snapshot statistics for an organization.

    Args:
        organization_id: Organization to query.
        db_path: Path to snapshot database.
        logger: Optional logger instance.

    Returns:
        Dictionary with statistics including total count, size, and per-sheet breakdown.
    """
    repo = get_snapshot_repository(db_path)
    stats = repo.get_stats(organization_id)

    if logger:
        logger.debug(
            f"Snapshot stats: {stats['total_snapshots']} snapshots, "
            f"{stats['total_size_bytes']} bytes"
        )

    return stats
