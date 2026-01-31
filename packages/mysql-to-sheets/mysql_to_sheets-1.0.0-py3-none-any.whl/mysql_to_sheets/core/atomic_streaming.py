"""Atomic streaming for transactional consistency in large dataset syncs.

This module provides atomic streaming capabilities where data is first written
to a staging worksheet, then atomically swapped to the live worksheet only after
100% completion and validation. This prevents partial data from appearing in
the live sheet during streaming operations.

Flow:
1. Create staging worksheet (_staging_<timestamp>)
2. Stream all chunks to staging worksheet
3. Validate staging data is complete
4. Atomically swap staging to live (delete live, rename staging)
5. Clean up staging on failure

Two swap modes are supported:
- Rename mode (default): Faster, but worksheet GID changes
- Copy mode (preserve_gid=True): Slower, preserves worksheet GID
"""

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

import gspread

from mysql_to_sheets.core.exceptions import ErrorCode, SheetsError, SyncError
from mysql_to_sheets.core.logging_utils import get_module_logger
from mysql_to_sheets.core.streaming import (
    ChunkResult,
    StreamingConfig,
    StreamingResult,
    fetch_data_streaming,
    validate_row_size,
)

if TYPE_CHECKING:
    from gspread import Spreadsheet, Worksheet

logger = get_module_logger(__name__)

# Pattern to parse staging worksheet timestamp from name
# Format: _staging_YYYYMMDD_HHMMSS
STAGING_NAME_PATTERN = re.compile(r"^_staging_(\d{8}_\d{6})$")


@dataclass
class AtomicStreamingConfig(StreamingConfig):
    """Extended configuration for atomic streaming mode.

    Inherits all settings from StreamingConfig and adds atomic-specific options.

    Attributes:
        staging_prefix: Prefix for staging worksheet names.
        cleanup_on_failure: Whether to delete staging worksheet on failure.
        preserve_gid: Use copy mode to preserve worksheet GID (slower).
        verification_enabled: Verify row count after swap.
        max_staging_age_minutes: Auto-cleanup threshold for stale staging sheets.
        resumable: Enable checkpoint/resume for large syncs.
        checkpoint_interval: Save checkpoint every N chunks.
        resume_from_checkpoint: Checkpoint to resume from (set by resume function).
    """

    staging_prefix: str = "_staging_"
    cleanup_on_failure: bool = True
    preserve_gid: bool = False
    verification_enabled: bool = True
    max_staging_age_minutes: int = 60
    # Resumable streaming fields
    resumable: bool = False
    checkpoint_interval: int = 1
    resume_from_checkpoint: Any | None = None  # StreamingCheckpoint type


@dataclass
class AtomicStreamingResult(StreamingResult):
    """Extended result for atomic streaming operations.

    Inherits statistics from StreamingResult and adds atomic operation details.

    Attributes:
        staging_worksheet_name: Name of the staging worksheet used.
        swap_successful: Whether the atomic swap completed successfully.
        verification_passed: Whether post-swap verification passed.
        staging_cleanup_done: Whether staging was cleaned up.
        swap_mode: Mode used for swap ('rename' or 'copy').
        resumable: Whether this sync can be resumed from checkpoint.
        checkpoint_chunk: Last checkpointed chunk number (for resume).
        staging_worksheet_gid: GID of the staging worksheet (for resume).
    """

    staging_worksheet_name: str | None = None
    swap_successful: bool = False
    verification_passed: bool = False
    staging_cleanup_done: bool = False
    swap_mode: str = "rename"
    # Resumable streaming fields
    resumable: bool = False
    checkpoint_chunk: int | None = None
    staging_worksheet_gid: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        base = super().to_dict()
        base.update(
            {
                "staging_worksheet_name": self.staging_worksheet_name,
                "swap_successful": self.swap_successful,
                "verification_passed": self.verification_passed,
                "staging_cleanup_done": self.staging_cleanup_done,
                "swap_mode": self.swap_mode,
                "resumable": self.resumable,
                "checkpoint_chunk": self.checkpoint_chunk,
                "staging_worksheet_gid": self.staging_worksheet_gid,
            }
        )
        return base


def _generate_staging_name(prefix: str = "_staging_") -> str:
    """Generate a unique staging worksheet name with timestamp.

    Args:
        prefix: Prefix for staging name (default: '_staging_').

    Returns:
        Staging worksheet name like '_staging_20240115_103045'.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{prefix}{timestamp}"


def _parse_staging_timestamp(name: str) -> datetime | None:
    """Parse timestamp from staging worksheet name.

    Args:
        name: Staging worksheet name like '_staging_20240115_103045'.

    Returns:
        Datetime if parseable, None otherwise.
    """
    match = STAGING_NAME_PATTERN.match(name)
    if not match:
        return None

    try:
        return datetime.strptime(match.group(1), "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def create_staging_worksheet(
    spreadsheet: "Spreadsheet",
    prefix: str = "_staging_",
    rows: int = 1000,
    cols: int = 26,
    logger_instance: logging.Logger | None = None,
) -> "Worksheet":
    """Create a new staging worksheet with timestamp-based name.

    Args:
        spreadsheet: Open gspread Spreadsheet object.
        prefix: Prefix for staging worksheet name.
        rows: Initial row count for the worksheet.
        cols: Initial column count for the worksheet.
        logger_instance: Optional logger.

    Returns:
        Newly created staging Worksheet.

    Raises:
        SheetsError: If worksheet creation fails.
    """
    log = logger_instance or logger
    staging_name = _generate_staging_name(prefix)

    log.info(f"Creating staging worksheet '{staging_name}'")

    try:
        worksheet = spreadsheet.add_worksheet(title=staging_name, rows=rows, cols=cols)
        log.debug(f"Successfully created staging worksheet '{staging_name}'")
        return worksheet
    except gspread.exceptions.APIError as e:
        raise SheetsError(
            message=f"Failed to create staging worksheet '{staging_name}': {e}",
            sheet_id=spreadsheet.id,
            worksheet_name=staging_name,
            original_error=e,
            code=ErrorCode.SHEETS_API_ERROR,
        ) from e


def cleanup_staging_worksheet(
    spreadsheet: "Spreadsheet",
    staging_name: str,
    logger_instance: logging.Logger | None = None,
) -> bool:
    """Delete a staging worksheet.

    Args:
        spreadsheet: Open gspread Spreadsheet object.
        staging_name: Name of the staging worksheet to delete.
        logger_instance: Optional logger.

    Returns:
        True if deleted successfully, False if not found.
    """
    log = logger_instance or logger

    try:
        worksheet = spreadsheet.worksheet(staging_name)
        spreadsheet.del_worksheet(worksheet)
        log.info(f"Cleaned up staging worksheet '{staging_name}'")
        return True
    except gspread.exceptions.WorksheetNotFound:
        log.debug(f"Staging worksheet '{staging_name}' not found (already cleaned)")
        return False
    except gspread.exceptions.APIError as e:
        log.warning(f"Failed to cleanup staging worksheet '{staging_name}': {e}")
        return False


def cleanup_stale_staging_sheets(
    spreadsheet: "Spreadsheet",
    max_age_minutes: int = 60,
    staging_prefix: str = "_staging_",
    logger_instance: logging.Logger | None = None,
) -> int:
    """Delete staging worksheets older than max_age_minutes.

    This function cleans up orphaned staging sheets that may have been
    left behind by crashed or interrupted streaming operations.

    Args:
        spreadsheet: Open gspread Spreadsheet object.
        max_age_minutes: Maximum age in minutes before cleanup.
        staging_prefix: Prefix used for staging worksheet names.
        logger_instance: Optional logger.

    Returns:
        Number of staging worksheets cleaned up.
    """
    log = logger_instance or logger
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
    cleaned = 0

    log.info(f"Cleaning stale staging sheets older than {max_age_minutes} minutes")

    for ws in spreadsheet.worksheets():
        if not ws.title.startswith(staging_prefix):
            continue

        created_at = _parse_staging_timestamp(ws.title)
        if created_at is None:
            # Can't parse timestamp - skip (may be manually created)
            log.debug(f"Skipping unparseable staging sheet: {ws.title}")
            continue

        if created_at < cutoff:
            try:
                spreadsheet.del_worksheet(ws)
                log.info(f"Cleaned up stale staging sheet: {ws.title}")
                cleaned += 1
            except gspread.exceptions.APIError as e:
                log.warning(f"Failed to clean up stale staging sheet '{ws.title}': {e}")

    log.info(f"Cleaned up {cleaned} stale staging sheet(s)")
    return cleaned


def push_chunk_to_staging(
    worksheet: "Worksheet",
    headers: list[str],
    rows: list[list[Any]],
    chunk_number: int,
    is_first_chunk: bool,
    logger_instance: logging.Logger | None = None,
) -> None:
    """Push a chunk of data to the staging worksheet.

    For the first chunk, writes headers and data.
    For subsequent chunks, appends rows.

    Args:
        worksheet: Staging worksheet to push to.
        headers: Column headers.
        rows: Data rows for this chunk.
        chunk_number: The chunk number (for logging).
        is_first_chunk: Whether this is the first chunk.
        logger_instance: Optional logger.

    Raises:
        SheetsError: If push fails.
    """
    log = logger_instance or logger

    try:
        if is_first_chunk:
            log.info(f"Writing headers and first chunk to staging ({len(rows)} rows)")
            all_data = [headers] + rows
            worksheet.update(
                values=all_data,
                range_name="A1",
                value_input_option="USER_ENTERED",  # type: ignore[arg-type]
            )
        else:
            log.debug(f"Appending chunk {chunk_number} to staging ({len(rows)} rows)")
            worksheet.append_rows(
                values=rows,
                value_input_option="USER_ENTERED",  # type: ignore[arg-type]
            )
    except gspread.exceptions.APIError as e:
        raise SheetsError(
            message=f"Failed to push chunk {chunk_number} to staging: {e}",
            sheet_id=worksheet.spreadsheet.id,
            worksheet_name=worksheet.title,
            original_error=e,
            code=ErrorCode.SHEETS_API_ERROR,
        ) from e


def validate_staging_complete(
    worksheet: "Worksheet",
    expected_rows: int,
    logger_instance: logging.Logger | None = None,
) -> bool:
    """Validate that staging worksheet contains expected row count.

    Args:
        worksheet: Staging worksheet to validate.
        expected_rows: Expected number of data rows (excluding header).
        logger_instance: Optional logger.

    Returns:
        True if validation passes.

    Raises:
        SyncError: If validation fails.
    """
    log = logger_instance or logger

    try:
        # Get actual row count (includes header row)
        values = worksheet.get_all_values()
        actual_rows = len(values) - 1  # Subtract header row

        if actual_rows != expected_rows:
            msg = (
                f"Staging validation failed: expected {expected_rows} rows, "
                f"found {actual_rows} rows"
            )
            log.error(msg)
            raise SyncError(
                message=msg,
                code="ATOMIC_001",
            )

        log.info(f"Staging validation passed: {actual_rows} rows verified")
        return True

    except gspread.exceptions.APIError as e:
        raise SheetsError(
            message=f"Failed to validate staging worksheet: {e}",
            sheet_id=worksheet.spreadsheet.id,
            worksheet_name=worksheet.title,
            original_error=e,
            code=ErrorCode.SHEETS_API_ERROR,
        ) from e


def atomic_swap_rename(
    spreadsheet: "Spreadsheet",
    staging_worksheet: "Worksheet",
    live_name: str,
    logger_instance: logging.Logger | None = None,
) -> None:
    """Swap staging to live using rename mode (GID changes).

    This is the faster swap mode but changes the worksheet GID.

    Steps:
    1. Delete existing live worksheet (if exists)
    2. Rename staging worksheet to live name

    Args:
        spreadsheet: Open gspread Spreadsheet object.
        staging_worksheet: Staging worksheet to swap in.
        live_name: Name for the live worksheet.
        logger_instance: Optional logger.

    Raises:
        SheetsError: If swap fails.
    """
    log = logger_instance or logger
    staging_name = staging_worksheet.title

    log.info(f"Atomic swap (rename mode): '{staging_name}' -> '{live_name}'")

    # Step 1: Delete existing live worksheet if it exists
    try:
        live_ws = spreadsheet.worksheet(live_name)
        spreadsheet.del_worksheet(live_ws)
        log.debug(f"Deleted existing live worksheet '{live_name}'")
    except gspread.exceptions.WorksheetNotFound:
        log.debug(f"No existing live worksheet '{live_name}' to delete")
    except gspread.exceptions.APIError as e:
        # If this fails, staging is intact, live is also intact
        raise SheetsError(
            message=f"Failed to delete live worksheet '{live_name}' during swap: {e}",
            sheet_id=spreadsheet.id,
            worksheet_name=live_name,
            original_error=e,
            code=ErrorCode.SHEETS_API_ERROR,
        ) from e

    # Step 2: Rename staging to live name
    try:
        staging_worksheet.update_title(live_name)
        log.info(f"Renamed staging '{staging_name}' to '{live_name}'")
    except gspread.exceptions.APIError as e:
        # Critical: live is deleted but staging rename failed
        # Staging still exists with original name - user can recover manually
        raise SheetsError(
            message=(
                f"Critical: Failed to rename staging '{staging_name}' to '{live_name}': {e}. "
                f"Live worksheet was deleted. Staging worksheet '{staging_name}' still exists - "
                f"rename it manually to recover."
            ),
            sheet_id=spreadsheet.id,
            worksheet_name=staging_name,
            original_error=e,
            code=ErrorCode.SHEETS_API_ERROR,
        ) from e


def atomic_swap_copy(
    spreadsheet: "Spreadsheet",
    staging_worksheet: "Worksheet",
    live_name: str,
    logger_instance: logging.Logger | None = None,
) -> None:
    """Swap staging to live using copy mode (preserves GID).

    This mode preserves the worksheet GID but is slower because it
    copies all data from staging to live.

    Steps:
    1. Get or create live worksheet
    2. Clear live worksheet
    3. Copy all data from staging to live
    4. Delete staging worksheet

    Args:
        spreadsheet: Open gspread Spreadsheet object.
        staging_worksheet: Staging worksheet to copy from.
        live_name: Name for the live worksheet.
        logger_instance: Optional logger.

    Raises:
        SheetsError: If swap fails.
    """
    log = logger_instance or logger
    staging_name = staging_worksheet.title

    log.info(f"Atomic swap (copy mode): '{staging_name}' -> '{live_name}'")

    # Step 1: Get or create live worksheet
    try:
        live_ws = spreadsheet.worksheet(live_name)
        log.debug(f"Found existing live worksheet '{live_name}'")
    except gspread.exceptions.WorksheetNotFound:
        log.info(f"Creating live worksheet '{live_name}'")
        live_ws = spreadsheet.add_worksheet(title=live_name, rows=1000, cols=26)

    # Step 2: Clear live worksheet
    try:
        live_ws.clear()
        log.debug(f"Cleared live worksheet '{live_name}'")
    except gspread.exceptions.APIError as e:
        raise SheetsError(
            message=f"Failed to clear live worksheet '{live_name}': {e}",
            sheet_id=spreadsheet.id,
            worksheet_name=live_name,
            original_error=e,
            code=ErrorCode.SHEETS_API_ERROR,
        ) from e

    # Step 3: Copy all data from staging to live
    try:
        staging_data = staging_worksheet.get_all_values()
        if staging_data:
            live_ws.update(
                values=staging_data,
                range_name="A1",
                value_input_option="USER_ENTERED",  # type: ignore[arg-type]
            )
        log.info(f"Copied {len(staging_data)} rows from staging to live")
    except gspread.exceptions.APIError as e:
        raise SheetsError(
            message=f"Failed to copy data from staging to live: {e}",
            sheet_id=spreadsheet.id,
            worksheet_name=live_name,
            original_error=e,
            code=ErrorCode.SHEETS_API_ERROR,
        ) from e

    # Step 4: Delete staging worksheet
    try:
        spreadsheet.del_worksheet(staging_worksheet)
        log.debug(f"Deleted staging worksheet '{staging_name}'")
    except gspread.exceptions.APIError as e:
        # Non-critical: data is in live, staging cleanup failed
        log.warning(f"Failed to delete staging worksheet '{staging_name}': {e}")


def atomic_swap_staging_to_live(
    spreadsheet: "Spreadsheet",
    staging_worksheet: "Worksheet",
    live_name: str,
    preserve_gid: bool = False,
    logger_instance: logging.Logger | None = None,
) -> str:
    """Atomically swap staging worksheet to live.

    Args:
        spreadsheet: Open gspread Spreadsheet object.
        staging_worksheet: Staging worksheet to swap in.
        live_name: Name for the live worksheet.
        preserve_gid: If True, use copy mode to preserve GID.
        logger_instance: Optional logger.

    Returns:
        Swap mode used ('rename' or 'copy').

    Raises:
        SheetsError: If swap fails.
    """
    log = logger_instance or logger

    if preserve_gid:
        atomic_swap_copy(spreadsheet, staging_worksheet, live_name, log)
        return "copy"
    else:
        atomic_swap_rename(spreadsheet, staging_worksheet, live_name, log)
        return "rename"


def run_atomic_streaming_sync(
    config: Any,  # Config type
    atomic_config: AtomicStreamingConfig | None = None,
    logger_instance: logging.Logger | None = None,
    dry_run: bool = False,
    schema_policy: str | None = None,
    expected_headers: list[str] | None = None,
    job_id: int | None = None,
    config_id: int | None = None,
) -> AtomicStreamingResult:
    """Execute an atomic streaming sync operation.

    Streams data to a staging worksheet, then atomically swaps it to the
    live worksheet only after 100% completion and validation.

    Args:
        config: Configuration object with database and sheets settings.
        atomic_config: Atomic streaming configuration.
        logger_instance: Optional logger.
        dry_run: If True, fetch and validate but don't push to Sheets.
        schema_policy: Schema evolution policy for validating schema changes.
        expected_headers: Expected column headers from previous sync.
        job_id: Optional job ID for checkpoint tracking (resumable sync).
        config_id: Optional config ID for checkpoint tracking (resumable sync).

    Returns:
        AtomicStreamingResult with operation statistics and atomic details.

    Raises:
        SyncError: If streaming fails.
        SheetsError: If Sheets operations fail.
    """
    from mysql_to_sheets.core.sheets_client import get_sheets_client
    from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier
    from mysql_to_sheets.core.sync import clean_data, validate_batch_size

    log = logger_instance or logger
    ac = atomic_config or AtomicStreamingConfig()

    result = AtomicStreamingResult()
    result.swap_mode = "copy" if ac.preserve_gid else "rename"

    headers: list[str] | None = None
    staging_worksheet: Worksheet | None = None
    spreadsheet: Spreadsheet | None = None
    live_name: str = ""

    log.info(
        f"Starting atomic streaming sync "
        f"(chunk_size={ac.chunk_size}, preserve_gid={ac.preserve_gid}, "
        f"dry_run={dry_run}, resumable={ac.resumable})"
    )

    try:
        # Step 1: Connect to Sheets and create staging worksheet (unless dry_run)
        if not dry_run:
            gc = get_sheets_client(
                service_account_file=config.service_account_file,
                timeout=config.sheets_timeout,
            )
            spreadsheet = gc.open_by_key(config.google_sheet_id)

            # Resolve live worksheet name
            try:
                live_name = parse_worksheet_identifier(
                    config.google_worksheet_name,
                    spreadsheet=spreadsheet,
                )
            except ValueError as e:
                raise SheetsError(
                    message=str(e),
                    sheet_id=config.google_sheet_id,
                    worksheet_name=config.google_worksheet_name,
                ) from e

            # Clean up any stale staging sheets first
            cleanup_stale_staging_sheets(
                spreadsheet,
                max_age_minutes=ac.max_staging_age_minutes,
                staging_prefix=ac.staging_prefix,
                logger_instance=log,
            )

            # Create staging worksheet
            staging_worksheet = create_staging_worksheet(
                spreadsheet,
                prefix=ac.staging_prefix,
                rows=config.worksheet_default_rows,
                cols=config.worksheet_default_cols,
                logger_instance=log,
            )
            result.staging_worksheet_name = staging_worksheet.title
            result.staging_worksheet_gid = staging_worksheet.id
            log.info(f"Created staging worksheet: {staging_worksheet.title} (gid={staging_worksheet.id})")

        # Step 2: Stream chunks to staging
        try:
            for chunk_num, (chunk_headers, chunk_rows) in enumerate(
                fetch_data_streaming(config, ac.chunk_size, log)
            ):
                # Store headers from first chunk and check schema policy
                if headers is None:
                    headers = chunk_headers

                    # Check schema policy on first chunk (before any data is pushed)
                    if schema_policy is not None or expected_headers is not None:
                        from mysql_to_sheets.core.schema_evolution import (
                            SchemaChangeError,
                            SchemaPolicy,
                            apply_schema_policy,
                            detect_schema_change,
                        )

                        policy = schema_policy or "strict"
                        schema_change = detect_schema_change(expected_headers, headers)

                        if schema_change.has_changes:
                            log.info(f"Schema change detected in atomic streaming: {schema_change.summary()}")

                            try:
                                # Apply policy - may raise SchemaChangeError
                                _, _, _ = apply_schema_policy(
                                    schema_change,
                                    SchemaPolicy.from_string(policy),
                                    headers,
                                    [],  # Empty rows for validation only
                                )
                                log.info(f"Schema policy '{policy}' allows the detected changes")
                            except SchemaChangeError:
                                # Re-raise to abort before any data is pushed to staging
                                raise

                # Clean data for Sheets compatibility
                cleaned_rows = clean_data(chunk_rows, log)

                # Validate row sizes
                if ac.validate_row_size:
                    for row_idx, row in enumerate(cleaned_rows):
                        validate_row_size(row, row_idx, ac, log)

                # Validate chunk data
                try:
                    validate_batch_size(headers, cleaned_rows, logger=log)
                except (SyncError, OSError, ValueError) as e:
                    log.error(f"Validation failed for chunk {chunk_num}: {e}")
                    raise

                result.total_rows += len(cleaned_rows)
                result.total_chunks += 1

                chunk_result = ChunkResult(
                    chunk_number=chunk_num,
                    rows_processed=len(cleaned_rows),
                )

                if not dry_run and staging_worksheet is not None:
                    try:
                        push_chunk_to_staging(
                            staging_worksheet,
                            headers,
                            cleaned_rows,
                            chunk_num,
                            is_first_chunk=(chunk_num == 0),
                            logger_instance=log,
                        )
                        result.successful_chunks += 1

                        # Save checkpoint after successful chunk push (if resumable)
                        if (
                            ac.resumable
                            and job_id is not None
                            and config_id is not None
                            and result.successful_chunks % ac.checkpoint_interval == 0
                        ):
                            from mysql_to_sheets.core.tenant import get_tenant_db_path
                            from mysql_to_sheets.models.checkpoints import (
                                StreamingCheckpoint,
                                get_checkpoint_repository,
                            )

                            checkpoint = StreamingCheckpoint(
                                job_id=job_id,
                                config_id=config_id,
                                staging_worksheet_name=result.staging_worksheet_name or "",
                                staging_worksheet_gid=result.staging_worksheet_gid or 0,
                                chunks_completed=result.successful_chunks,
                                rows_pushed=result.total_rows,
                                headers=headers,
                            )
                            try:
                                checkpoint_repo = get_checkpoint_repository(get_tenant_db_path())
                                checkpoint_repo.save_checkpoint(checkpoint)
                                log.debug(
                                    f"Checkpoint saved: chunk {result.successful_chunks}, "
                                    f"rows {result.total_rows}"
                                )
                            except Exception as cp_err:
                                log.warning(f"Failed to save checkpoint: {cp_err}")
                                # Continue - checkpoint failure shouldn't abort sync

                    except (SheetsError, OSError, RuntimeError, ValueError) as e:
                        chunk_result.success = False
                        chunk_result.error = str(e)
                        result.failed_chunks += 1
                        log.error(f"Failed to push chunk {chunk_num} to staging: {e}")

                        if ac.abort_on_failure:
                            log.error(
                                f"Aborting atomic streaming sync due to chunk failure. "
                                f"Staging worksheet '{result.staging_worksheet_name}' will be cleaned up."
                            )
                            result.chunk_results.append(chunk_result)
                            raise
                else:
                    result.successful_chunks += 1

                result.chunk_results.append(chunk_result)

                # Rate limit protection
                if not dry_run and ac.chunk_delay > 0 and chunk_result.success:
                    time.sleep(ac.chunk_delay)

                # Log progress
                if ac.show_progress and chunk_num % ac.progress_interval == 0:
                    log.info(
                        f"Progress: {result.total_rows} rows to staging "
                        f"({result.total_chunks} chunks)"
                    )

        except Exception:
            # Handle failure based on resumable mode
            if ac.resumable and result.successful_chunks > 0:
                # Don't cleanup - preserve staging for resume
                log.warning(
                    f"Streaming failed at chunk {result.successful_chunks}. "
                    f"Staging sheet '{result.staging_worksheet_name}' preserved for resume."
                )
                result.resumable = True
                result.checkpoint_chunk = result.successful_chunks
                # Checkpoint should already be saved by chunk loop
            elif ac.cleanup_on_failure and spreadsheet and result.staging_worksheet_name:
                # Non-resumable: cleanup staging
                cleanup_staging_worksheet(spreadsheet, result.staging_worksheet_name, log)
                result.staging_cleanup_done = True
            raise

        log.info(
            f"Streaming to staging complete: "
            f"{result.total_rows} rows in {result.total_chunks} chunks"
        )

        # Step 3: Validate staging (unless dry_run or no data)
        if not dry_run and staging_worksheet is not None and result.total_rows > 0:
            if ac.verification_enabled:
                try:
                    validate_staging_complete(staging_worksheet, result.total_rows, log)
                    result.verification_passed = True
                except SyncError:
                    if ac.cleanup_on_failure and spreadsheet:
                        cleanup_staging_worksheet(
                            spreadsheet, result.staging_worksheet_name or "", log
                        )
                        result.staging_cleanup_done = True
                    raise
            else:
                result.verification_passed = True  # Skip verification

            # Step 4: Atomic swap staging to live
            log.info(f"Swapping staging '{staging_worksheet.title}' to live '{live_name}'")
            result.swap_mode = atomic_swap_staging_to_live(
                spreadsheet,  # type: ignore[arg-type]
                staging_worksheet,
                live_name,
                preserve_gid=ac.preserve_gid,
                logger_instance=log,
            )
            result.swap_successful = True
            result.staging_cleanup_done = True  # Staging is now the live sheet (rename) or deleted (copy)

            # Clear checkpoint on success (if resumable mode was enabled)
            if ac.resumable and job_id is not None:
                try:
                    from mysql_to_sheets.core.tenant import get_tenant_db_path
                    from mysql_to_sheets.models.checkpoints import get_checkpoint_repository

                    checkpoint_repo = get_checkpoint_repository(get_tenant_db_path())
                    if checkpoint_repo.delete_checkpoint(job_id):
                        log.debug(f"Checkpoint cleared for job {job_id}")
                except Exception as cp_err:
                    log.warning(f"Failed to clear checkpoint: {cp_err}")

            log.info(
                f"Atomic streaming sync complete: "
                f"{result.total_rows} rows synced via {result.swap_mode} mode"
            )
        elif dry_run:
            log.info(f"Dry run complete: would sync {result.total_rows} rows")
            result.swap_successful = True  # Conceptually successful for dry run
            result.verification_passed = True

    except (SyncError, SheetsError) as e:
        log.error(f"Atomic streaming sync failed: {e}")
        raise

    return result


def resume_atomic_streaming_sync(
    config: Any,  # Config type
    checkpoint: Any,  # StreamingCheckpoint type
    atomic_config: AtomicStreamingConfig | None = None,
    job_id: int | None = None,
    logger_instance: logging.Logger | None = None,
) -> AtomicStreamingResult:
    """Resume a streaming sync from a checkpoint.

    Opens the existing staging worksheet, verifies it matches the checkpoint
    state, resumes fetching from the offset, and completes the atomic swap.

    Args:
        config: Configuration object with database and sheets settings.
        checkpoint: StreamingCheckpoint with saved state to resume from.
        atomic_config: Atomic streaming configuration.
        job_id: Job ID for checkpoint tracking.
        logger_instance: Optional logger.

    Returns:
        AtomicStreamingResult with operation statistics.

    Raises:
        SyncError: If resume fails due to state mismatch or other errors.
        SheetsError: If Sheets operations fail.
    """
    from mysql_to_sheets.core.sheets_client import get_sheets_client
    from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier
    from mysql_to_sheets.core.sync import clean_data, validate_batch_size
    from mysql_to_sheets.core.tenant import get_tenant_db_path
    from mysql_to_sheets.models.checkpoints import (
        StreamingCheckpoint,
        get_checkpoint_repository,
    )

    log = logger_instance or logger
    ac = atomic_config or AtomicStreamingConfig()

    # Initialize result with checkpoint state
    result = AtomicStreamingResult()
    result.swap_mode = "copy" if ac.preserve_gid else "rename"
    result.staging_worksheet_name = checkpoint.staging_worksheet_name
    result.staging_worksheet_gid = checkpoint.staging_worksheet_gid
    result.successful_chunks = checkpoint.chunks_completed
    result.total_rows = checkpoint.rows_pushed
    result.total_chunks = checkpoint.chunks_completed

    headers = checkpoint.headers
    offset = checkpoint.rows_pushed

    log.info(
        f"Resuming atomic streaming sync from checkpoint: "
        f"{checkpoint.chunks_completed} chunks, {checkpoint.rows_pushed} rows, "
        f"staging sheet '{checkpoint.staging_worksheet_name}'"
    )

    try:
        # Step 1: Connect to Sheets and find existing staging worksheet
        gc = get_sheets_client(
            service_account_file=config.service_account_file,
            timeout=config.sheets_timeout,
        )
        spreadsheet = gc.open_by_key(config.google_sheet_id)

        # Resolve live worksheet name
        try:
            live_name = parse_worksheet_identifier(
                config.google_worksheet_name,
                spreadsheet=spreadsheet,
            )
        except ValueError as e:
            raise SheetsError(
                message=str(e),
                sheet_id=config.google_sheet_id,
                worksheet_name=config.google_worksheet_name,
            ) from e

        # Find staging worksheet by GID
        staging_worksheet = None
        try:
            staging_worksheet = spreadsheet.get_worksheet_by_id(checkpoint.staging_worksheet_gid)
            log.info(f"Found staging worksheet by GID: {staging_worksheet.title}")
        except gspread.exceptions.WorksheetNotFound:
            raise SyncError(
                message=(
                    f"Staging worksheet with GID {checkpoint.staging_worksheet_gid} not found. "
                    f"The staging sheet may have been deleted. Cannot resume."
                ),
                code="RESUME_001",
            )

        # Verify staging sheet has expected rows
        try:
            values = staging_worksheet.get_all_values()
            current_rows = len(values) - 1  # Exclude header
        except gspread.exceptions.APIError as e:
            raise SheetsError(
                message=f"Failed to read staging worksheet: {e}",
                sheet_id=config.google_sheet_id,
                worksheet_name=staging_worksheet.title,
                original_error=e,
                code=ErrorCode.SHEETS_API_ERROR,
            ) from e

        if current_rows != checkpoint.rows_pushed:
            raise SyncError(
                message=(
                    f"Staging sheet state mismatch: expected {checkpoint.rows_pushed} rows, "
                    f"found {current_rows} rows. The staging sheet may have been modified. "
                    f"Cannot resume safely."
                ),
                code="RESUME_002",
            )

        log.info(f"Staging sheet verified: {current_rows} rows match checkpoint")

        # Step 2: Resume streaming from offset
        try:
            for chunk_num, (chunk_headers, chunk_rows) in enumerate(
                fetch_data_streaming(config, ac.chunk_size, log, offset=offset)
            ):
                # Verify headers match (should be same query)
                if chunk_num == 0 and chunk_headers != headers:
                    log.warning(
                        f"Headers changed since checkpoint. Expected {len(headers)} columns, "
                        f"got {len(chunk_headers)}. Proceeding with original headers."
                    )

                # Clean data for Sheets compatibility
                cleaned_rows = clean_data(chunk_rows, log)

                # Validate row sizes
                if ac.validate_row_size:
                    for row_idx, row in enumerate(cleaned_rows):
                        validate_row_size(row, row_idx, ac, log)

                # Validate chunk data
                try:
                    validate_batch_size(headers, cleaned_rows, logger=log)
                except (SyncError, OSError, ValueError) as e:
                    log.error(f"Validation failed for chunk {chunk_num}: {e}")
                    raise

                result.total_rows += len(cleaned_rows)
                result.total_chunks += 1

                chunk_result = ChunkResult(
                    chunk_number=checkpoint.chunks_completed + chunk_num,
                    rows_processed=len(cleaned_rows),
                )

                try:
                    push_chunk_to_staging(
                        staging_worksheet,
                        headers,
                        cleaned_rows,
                        checkpoint.chunks_completed + chunk_num,
                        is_first_chunk=False,  # Never first chunk in resume
                        logger_instance=log,
                    )
                    result.successful_chunks += 1

                    # Save checkpoint after successful chunk push
                    if (
                        ac.resumable
                        and job_id is not None
                        and result.successful_chunks % ac.checkpoint_interval == 0
                    ):
                        updated_checkpoint = StreamingCheckpoint(
                            job_id=job_id,
                            config_id=checkpoint.config_id,
                            staging_worksheet_name=checkpoint.staging_worksheet_name,
                            staging_worksheet_gid=checkpoint.staging_worksheet_gid,
                            chunks_completed=result.successful_chunks,
                            rows_pushed=result.total_rows,
                            headers=headers,
                        )
                        try:
                            checkpoint_repo = get_checkpoint_repository(get_tenant_db_path())
                            checkpoint_repo.save_checkpoint(updated_checkpoint)
                            log.debug(
                                f"Checkpoint updated: chunk {result.successful_chunks}, "
                                f"rows {result.total_rows}"
                            )
                        except Exception as cp_err:
                            log.warning(f"Failed to update checkpoint: {cp_err}")

                except (SheetsError, OSError, RuntimeError, ValueError) as e:
                    chunk_result.success = False
                    chunk_result.error = str(e)
                    result.failed_chunks += 1
                    log.error(f"Failed to push chunk during resume: {e}")

                    if ac.abort_on_failure:
                        result.chunk_results.append(chunk_result)
                        raise

                result.chunk_results.append(chunk_result)

                # Rate limit protection
                if ac.chunk_delay > 0 and chunk_result.success:
                    time.sleep(ac.chunk_delay)

                # Log progress
                if ac.show_progress and chunk_num % ac.progress_interval == 0:
                    log.info(
                        f"Resume progress: {result.total_rows} total rows "
                        f"({result.total_chunks} total chunks)"
                    )

        except Exception:
            # On failure during resume, preserve staging for another attempt
            log.warning(
                f"Resume failed at chunk {result.successful_chunks}. "
                f"Staging sheet preserved for retry."
            )
            result.resumable = True
            result.checkpoint_chunk = result.successful_chunks
            raise

        log.info(
            f"Resume streaming complete: "
            f"{result.total_rows} total rows in {result.total_chunks} total chunks"
        )

        # Step 3: Validate staging
        if ac.verification_enabled:
            try:
                validate_staging_complete(staging_worksheet, result.total_rows, log)
                result.verification_passed = True
            except SyncError:
                # Don't cleanup on verification failure during resume
                log.error("Verification failed during resume")
                raise
        else:
            result.verification_passed = True

        # Step 4: Atomic swap staging to live
        log.info(f"Swapping staging '{staging_worksheet.title}' to live '{live_name}'")
        result.swap_mode = atomic_swap_staging_to_live(
            spreadsheet,
            staging_worksheet,
            live_name,
            preserve_gid=ac.preserve_gid,
            logger_instance=log,
        )
        result.swap_successful = True
        result.staging_cleanup_done = True

        # Clear checkpoint on success
        if job_id is not None:
            try:
                checkpoint_repo = get_checkpoint_repository(get_tenant_db_path())
                if checkpoint_repo.delete_checkpoint(job_id):
                    log.debug(f"Checkpoint cleared for job {job_id}")
            except Exception as cp_err:
                log.warning(f"Failed to clear checkpoint: {cp_err}")

        log.info(
            f"Resume atomic streaming sync complete: "
            f"{result.total_rows} rows synced via {result.swap_mode} mode"
        )

    except (SyncError, SheetsError) as e:
        log.error(f"Resume atomic streaming sync failed: {e}")
        raise

    return result
