"""Memory-efficient streaming for large dataset handling.

This module provides utilities for processing large datasets in chunks,
enabling sync operations that would otherwise run out of memory.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from mysql_to_sheets.core.exceptions import SyncError
from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)


@dataclass
class StreamingConfig:
    """Configuration for streaming sync mode.

    Attributes:
        chunk_size: Number of rows to process at a time.
        show_progress: Whether to log progress updates.
        progress_interval: Log progress every N chunks.
        chunk_delay: Seconds to sleep between chunk pushes (rate limit protection).
        abort_on_failure: Stop processing on first failed chunk.
        max_row_size_bytes: Maximum size of a single row in bytes (default 1MB).
        max_cell_size_bytes: Maximum size of a single cell in bytes (default 50KB).
        validate_row_size: Whether to validate row sizes (default True).
    """

    chunk_size: int = 1000
    show_progress: bool = True
    progress_interval: int = 10
    chunk_delay: float = 1.0
    abort_on_failure: bool = True
    max_row_size_bytes: int = 1_000_000  # 1MB per row
    max_cell_size_bytes: int = 50_000  # 50KB per cell (Sheets limit)
    validate_row_size: bool = True

    def __post_init__(self) -> None:
        """Validate configuration bounds."""
        if self.chunk_size < 100:
            self.chunk_size = 100
        elif self.chunk_size > 10000:
            self.chunk_size = 10000
        if self.chunk_delay < 0:
            self.chunk_delay = 0
        if self.max_row_size_bytes < 1000:
            self.max_row_size_bytes = 1000
        if self.max_cell_size_bytes < 1000:
            self.max_cell_size_bytes = 1000


def validate_row_size(
    row: list[Any],
    row_index: int,
    config: StreamingConfig,
    logger_instance: logging.Logger | None = None,
) -> None:
    """Validate a row doesn't exceed size limits.

    Checks both total row size and individual cell sizes to prevent
    OOM errors and Google Sheets API failures.

    Args:
        row: The data row to validate.
        row_index: Row index (for error messages).
        config: Streaming configuration with size limits.
        logger_instance: Optional logger.

    Raises:
        SyncError: If row or any cell exceeds configured limits.
    """
    import sys

    log = logger_instance or logger

    # Check individual cell sizes
    for col_idx, cell in enumerate(row):
        cell_str = str(cell) if cell is not None else ""
        cell_size = len(cell_str.encode("utf-8"))
        if cell_size > config.max_cell_size_bytes:
            msg = (
                f"Cell at row {row_index}, column {col_idx} exceeds size limit: "
                f"{cell_size:,} bytes > {config.max_cell_size_bytes:,} bytes. "
                f"Consider truncating large text fields or excluding BLOB columns."
            )
            log.error(msg)
            raise SyncError(
                message=msg,
                code="STREAMING_001",
            )

    # Check total row size (using sys.getsizeof for Python object size)
    row_size = sum(sys.getsizeof(cell) for cell in row)
    if row_size > config.max_row_size_bytes:
        msg = (
            f"Row {row_index} exceeds size limit: {row_size:,} bytes > "
            f"{config.max_row_size_bytes:,} bytes. "
            f"Consider excluding large columns or reducing row count."
        )
        log.error(msg)
        raise SyncError(
            message=msg,
            code="STREAMING_002",
        )


@dataclass
class ChunkResult:
    """Result of processing a single chunk.

    Attributes:
        chunk_number: Zero-indexed chunk number.
        rows_processed: Number of rows in this chunk.
        success: Whether the chunk was processed successfully.
        error: Error message if failed.
    """

    chunk_number: int
    rows_processed: int
    success: bool = True
    error: str | None = None


@dataclass
class StreamingResult:
    """Result of a streaming sync operation.

    Attributes:
        total_rows: Total rows processed across all chunks.
        total_chunks: Number of chunks processed.
        successful_chunks: Number of successful chunks.
        failed_chunks: Number of failed chunks.
        chunk_results: Individual results for each chunk.
    """

    total_rows: int = 0
    total_chunks: int = 0
    successful_chunks: int = 0
    failed_chunks: int = 0
    chunk_results: list[ChunkResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if all chunks were successful."""
        return self.failed_chunks == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "total_rows": self.total_rows,
            "total_chunks": self.total_chunks,
            "successful_chunks": self.successful_chunks,
            "failed_chunks": self.failed_chunks,
            "success": self.success,
        }


def chunk_iterator(
    rows: list[list[Any]],
    chunk_size: int,
) -> Generator[list[list[Any]], None, None]:
    """Iterate over rows in chunks.

    Args:
        rows: All rows to process.
        chunk_size: Size of each chunk.

    Yields:
        Lists of rows, each up to chunk_size.
    """
    for i in range(0, len(rows), chunk_size):
        yield rows[i : i + chunk_size]


@contextmanager
def streaming_mysql_connection(
    config: Any,
    logger_instance: logging.Logger | None = None,
) -> Generator[tuple[Any, Any], None, None]:
    """Context manager for MySQL streaming connections.

    Ensures connection and cursor are properly closed when context exits,
    even if the generator is abandoned early.

    Args:
        config: Configuration with database credentials.
        logger_instance: Optional logger.

    Yields:
        Tuple of (connection, cursor).

    Raises:
        DatabaseError: If connection fails.
    """
    import mysql.connector
    from mysql.connector import Error as MySQLError

    from mysql_to_sheets.core.exceptions import DatabaseError

    log = logger_instance or logger
    connection = None
    cursor = None

    try:
        log.debug("Opening MySQL connection for streaming")
        connection = mysql.connector.connect(
            host=config.db_host,
            port=config.db_port,
            user=config.db_user,
            password=config.db_password,
            database=config.db_name,
            buffered=False,
        )
        cursor = connection.cursor()
        yield connection, cursor
    except MySQLError as e:
        log.error(f"MySQL connection error: {e}")
        raise DatabaseError(
            message=f"Failed to connect to database: {e}",
            host=config.db_host,
            database=config.db_name,
            original_error=e,
        ) from e
    finally:
        if cursor:
            try:
                cursor.close()
                log.debug("MySQL cursor closed")
            except Exception:
                pass
        if connection:
            try:
                if connection.is_connected():
                    connection.close()
                    log.debug("MySQL connection closed")
            except Exception:
                pass


def fetch_data_streaming(
    config: Any,  # Config type
    chunk_size: int = 1000,
    logger_instance: logging.Logger | None = None,
    offset: int = 0,
) -> Generator[tuple[list[str], list[list[Any]]], None, None]:
    """Fetch data from MySQL in a streaming fashion.

    Uses server-side cursors to avoid loading all data into memory.

    Args:
        config: Configuration with database credentials.
        chunk_size: Number of rows to fetch at a time.
        logger_instance: Optional logger.
        offset: Number of rows to skip (for resume operations). Uses
            cursor.fetchmany() to consume and discard rows efficiently.

    Yields:
        Tuples of (headers, chunk_rows).
    """
    import mysql.connector
    from mysql.connector import Error as MySQLError

    from mysql_to_sheets.core.exceptions import DatabaseError

    log = logger_instance or logger

    connection = None
    cursor = None

    try:
        log.info(f"Connecting to MySQL (streaming mode, chunk_size={chunk_size}, offset={offset})")

        connection = mysql.connector.connect(
            host=config.db_host,
            port=config.db_port,
            user=config.db_user,
            password=config.db_password,
            database=config.db_name,
            # Enable buffered cursor for fetchmany
            buffered=False,
        )

        # Use a server-side cursor for large result sets
        cursor = connection.cursor()
        cursor.execute(config.sql_query)

        # Get headers from cursor description
        if cursor.description is None:
            headers = []
        else:
            headers = [desc[0] for desc in cursor.description]

        # Skip offset rows for resume operations
        if offset > 0:
            rows_skipped = 0
            while rows_skipped < offset:
                skip_chunk = cursor.fetchmany(min(chunk_size, offset - rows_skipped))
                if not skip_chunk:
                    log.warning(
                        f"Reached end of result set while skipping. "
                        f"Skipped {rows_skipped} of {offset} requested rows."
                    )
                    break
                rows_skipped += len(skip_chunk)
            log.info(f"Resumed from offset: skipped {rows_skipped} rows")

        chunk_num = 0
        while True:
            chunk = cursor.fetchmany(chunk_size)
            if not chunk:
                break

            rows = [list(row) for row in chunk]
            chunk_num += 1

            log.debug(f"Fetched chunk {chunk_num} with {len(rows)} rows")
            yield headers, rows

        log.info(f"Streaming fetch complete: {chunk_num} chunks")

    except MySQLError as e:
        log.error(f"MySQL error during streaming fetch: {e}")
        raise DatabaseError(
            message=f"Failed to fetch data: {e}",
            host=config.db_host,
            database=config.db_name,
            original_error=e,
        ) from e
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection:
            try:
                if connection.is_connected():
                    connection.close()
            except Exception:
                pass


def push_chunk_to_sheets(
    config: Any,  # Config type
    headers: list[str],
    rows: list[list[Any]],
    chunk_number: int,
    is_first_chunk: bool,
    logger_instance: logging.Logger | None = None,
) -> None:
    """Push a chunk of data to Google Sheets.

    For the first chunk, clears the sheet and writes headers.
    For subsequent chunks, appends to existing data.

    Args:
        config: Configuration with Sheets settings.
        headers: Column headers.
        rows: Data rows for this chunk.
        chunk_number: The chunk number (for logging).
        is_first_chunk: Whether this is the first chunk.
        logger_instance: Optional logger.
    """
    import gspread

    from mysql_to_sheets.core.exceptions import SheetsError
    from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier

    log = logger_instance or logger

    try:
        from mysql_to_sheets.core.sheets_client import get_sheets_client

        gc = get_sheets_client(
            service_account_file=config.service_account_file,
            timeout=config.sheets_timeout,
        )
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

        if is_first_chunk:
            log.info("Clearing sheet and writing headers (first chunk)")
            worksheet.clear()

            # Write headers and first chunk
            all_data = [headers] + rows
            worksheet.update(
                values=all_data,
                range_name="A1",
                value_input_option="USER_ENTERED",  # type: ignore[arg-type]
            )
        else:
            # Append to existing data
            log.debug(f"Appending chunk {chunk_number} ({len(rows)} rows)")
            worksheet.append_rows(
                values=rows,
                value_input_option="USER_ENTERED",  # type: ignore[arg-type]
            )

    except gspread.exceptions.APIError as e:
        log.error(f"Sheets API error for chunk {chunk_number}: {e}")
        raise SheetsError(
            message=f"Failed to push chunk {chunk_number}: {e}",
            sheet_id=config.google_sheet_id,
            worksheet_name=config.google_worksheet_name,
            original_error=e,
        ) from e


def run_streaming_sync(
    config: Any,  # Config type
    streaming_config: StreamingConfig | None = None,
    logger_instance: logging.Logger | None = None,
    dry_run: bool = False,
    atomic: bool = True,
    preserve_gid: bool = False,
    schema_policy: str | None = None,
    expected_headers: list[str] | None = None,
    resumable: bool = False,
    job_id: int | None = None,
    config_id: int | None = None,
) -> StreamingResult:
    """Execute a streaming sync operation.

    Fetches and pushes data in chunks to handle large datasets
    without running out of memory.

    By default, uses atomic mode which streams to a staging worksheet first,
    then atomically swaps it to the live worksheet after completion. This
    prevents partial data from appearing in the live sheet during streaming.

    Args:
        config: Configuration object.
        streaming_config: Streaming configuration.
        logger_instance: Optional logger.
        dry_run: If True, fetch but don't push to Sheets.
        atomic: If True (default), use atomic staging mode for transactional
            consistency. Set to False for legacy direct-write behavior.
        preserve_gid: If True, use copy mode to preserve worksheet GID during
            atomic swap. Only applies when atomic=True.
        schema_policy: Schema evolution policy ('strict', 'additive', 'flexible',
            'notify_only'). If provided with expected_headers, validates schema
            on first chunk.
        expected_headers: Expected column headers from previous sync. Used with
            schema_policy for schema change detection.
        resumable: If True, enable checkpoint/resume for streaming syncs.
            Preserves staging worksheet on failure for later resume.
        job_id: Optional job ID for checkpoint tracking (resumable streaming).
        config_id: Optional config ID for checkpoint tracking (resumable streaming).

    Returns:
        StreamingResult with operation statistics.
    """
    # Use atomic streaming for transactional consistency (default behavior)
    if atomic and not dry_run:
        from mysql_to_sheets.core.atomic_streaming import (
            AtomicStreamingConfig,
            run_atomic_streaming_sync,
        )

        log = logger_instance or logger
        log.info("Using atomic streaming mode for transactional consistency")

        # Build atomic config from streaming config
        sc = streaming_config or StreamingConfig()
        atomic_config = AtomicStreamingConfig(
            chunk_size=sc.chunk_size,
            show_progress=sc.show_progress,
            progress_interval=sc.progress_interval,
            chunk_delay=sc.chunk_delay,
            abort_on_failure=sc.abort_on_failure,
            max_row_size_bytes=sc.max_row_size_bytes,
            max_cell_size_bytes=sc.max_cell_size_bytes,
            validate_row_size=sc.validate_row_size,
            preserve_gid=preserve_gid,
            resumable=resumable,
        )

        return run_atomic_streaming_sync(
            config,
            atomic_config=atomic_config,
            logger_instance=logger_instance,
            dry_run=dry_run,
            schema_policy=schema_policy,
            expected_headers=expected_headers,
            job_id=job_id,
            config_id=config_id,
        )

    # Legacy direct-write mode (atomic=False)
    from mysql_to_sheets.core.sync import clean_data

    log = logger_instance or logger
    sc = streaming_config or StreamingConfig()

    result = StreamingResult()
    headers: list[str] | None = None

    log.info(f"Starting streaming sync (chunk_size={sc.chunk_size}, dry_run={dry_run})")

    try:
        for chunk_num, (chunk_headers, chunk_rows) in enumerate(
            fetch_data_streaming(config, sc.chunk_size, log)
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
                        log.info(f"Schema change detected in streaming mode: {schema_change.summary()}")

                        try:
                            # Apply policy - may raise SchemaChangeError for strict/additive
                            # Note: We don't filter columns in streaming mode (too complex)
                            # Just validate that the policy allows the changes
                            _, _, _ = apply_schema_policy(
                                schema_change,
                                SchemaPolicy.from_string(policy),
                                headers,
                                [],  # Empty rows for validation only
                            )
                            log.info(f"Schema policy '{policy}' allows the detected changes")
                        except SchemaChangeError:
                            # Re-raise to abort streaming before any data is pushed
                            raise

            # Clean data for Sheets compatibility
            cleaned_rows = clean_data(chunk_rows, log)

            # Validate chunk data before pushing to catch issues early
            # Import here to avoid circular imports
            from mysql_to_sheets.core.sync import validate_batch_size

            try:
                validate_batch_size(headers, cleaned_rows, logger=log)
            except (SyncError, OSError, ValueError) as e:
                log.error(f"Validation failed for chunk {chunk_num}: {e}")
                # On validation failure, abort early before any data is pushed
                # This prevents partial data from being written to the sheet
                raise

            result.total_rows += len(cleaned_rows)
            result.total_chunks += 1

            chunk_result = ChunkResult(
                chunk_number=chunk_num,
                rows_processed=len(cleaned_rows),
            )

            if not dry_run:
                try:
                    push_chunk_to_sheets(
                        config,
                        headers,
                        cleaned_rows,
                        chunk_num,
                        is_first_chunk=(chunk_num == 0),
                        logger_instance=log,
                    )
                    result.successful_chunks += 1
                except (OSError, RuntimeError, ValueError) as e:
                    chunk_result.success = False
                    chunk_result.error = str(e)
                    result.failed_chunks += 1
                    log.error(f"Failed to push chunk {chunk_num}: {e}")
                    if sc.abort_on_failure:
                        log.error(
                            "Aborting streaming sync due to chunk failure "
                            f"(successful_chunks={result.successful_chunks}, "
                            f"failed_chunks={result.failed_chunks}). "
                            "Sheet may contain partial data."
                        )
                        result.chunk_results.append(chunk_result)
                        return result
            else:
                result.successful_chunks += 1

            result.chunk_results.append(chunk_result)

            # Rate limit protection: delay between chunk pushes
            if not dry_run and sc.chunk_delay > 0 and chunk_result.success:
                import time

                time.sleep(sc.chunk_delay)

            # Log progress
            if sc.show_progress and chunk_num % sc.progress_interval == 0:
                log.info(
                    f"Progress: {result.total_rows} rows processed ({result.total_chunks} chunks)"
                )

        log.info(
            f"Streaming sync complete: {result.total_rows} rows in {result.total_chunks} chunks"
        )

    except (SyncError, OSError, ValueError) as e:
        log.error(f"Streaming sync failed: {e}")
        raise

    return result


class RowBuffer:
    """Buffer for accumulating rows before batch operations.

    Useful for append mode where we want to batch appends.
    """

    def __init__(self, max_size: int = 1000) -> None:
        """Initialize row buffer.

        Args:
            max_size: Maximum rows before flush.
        """
        self.max_size = max_size
        self._rows: list[list[Any]] = []

    def add(self, row: list[Any]) -> bool:
        """Add a row to the buffer.

        Args:
            row: Row to add.

        Returns:
            True if buffer is now full and should be flushed.
        """
        self._rows.append(row)
        return len(self._rows) >= self.max_size

    def add_many(self, rows: list[list[Any]]) -> bool:
        """Add multiple rows to the buffer.

        Args:
            rows: Rows to add.

        Returns:
            True if buffer is now full.
        """
        self._rows.extend(rows)
        return len(self._rows) >= self.max_size

    def flush(self) -> list[list[Any]]:
        """Get and clear all buffered rows.

        Returns:
            All buffered rows.
        """
        rows = self._rows
        self._rows = []
        return rows

    @property
    def size(self) -> int:
        """Get current buffer size."""
        return len(self._rows)

    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self._rows) == 0
