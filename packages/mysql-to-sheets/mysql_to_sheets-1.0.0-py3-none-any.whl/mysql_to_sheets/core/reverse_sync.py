"""Google Sheets to Database reverse sync logic.

This module contains the core functionality for reverse sync - pushing data
from Google Sheets back to a database. Supports multiple databases and
conflict resolution strategies.

Supports multiple databases:
- MySQL
- PostgreSQL
- SQLite
- SQL Server

Supports multiple conflict modes:
- overwrite: Replace existing rows (upsert)
- skip: Skip rows that already exist
- error: Fail if any row already exists
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

import gspread

from mysql_to_sheets.core.config import Config, get_config
from mysql_to_sheets.core.database import (
    DatabaseConfig,
    WriteResult,
    get_connection,
)
from mysql_to_sheets.core.exceptions import (
    ConfigError,
    DatabaseError,
    SheetsError,
)


class ConflictMode(str, Enum):
    """Conflict resolution strategy for reverse sync."""

    OVERWRITE = "overwrite"  # Update existing rows (upsert)
    SKIP = "skip"  # Skip rows that already exist
    ERROR = "error"  # Fail if any row exists


@dataclass
class ReverseSyncConfig:
    """Configuration for reverse sync operations.

    Attributes:
        table_name: Target database table name.
        key_columns: Columns that form the unique key (for conflict detection).
        conflict_mode: How to handle existing rows.
        update_columns: Columns to update on conflict (None = all non-key columns).
        batch_size: Number of rows to process at a time.
        column_mapping: Map sheet columns to DB columns (sheet_col -> db_col).
        skip_header: Whether to skip the first row (header) in the sheet.
        sheet_range: Specific range to read from (e.g., "A1:E100"). If None, reads all.
    """

    table_name: str
    key_columns: list[str] = field(default_factory=list)
    conflict_mode: ConflictMode = ConflictMode.OVERWRITE
    update_columns: list[str] | None = None
    batch_size: int = 1000
    column_mapping: dict[str, str] | None = None
    skip_header: bool = True
    sheet_range: str | None = None


@dataclass
class ReverseSyncResult:
    """Result of a reverse sync operation.

    Attributes:
        success: Whether the sync completed successfully.
        rows_processed: Total number of rows read from sheet.
        rows_inserted: Number of rows inserted.
        rows_updated: Number of rows updated.
        rows_skipped: Number of rows skipped (for skip mode).
        message: Human-readable status message.
        error: Error details if sync failed.
    """

    success: bool
    rows_processed: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_skipped: int = 0
    message: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for API responses.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "success": self.success,
            "rows_processed": self.rows_processed,
            "rows_inserted": self.rows_inserted,
            "rows_updated": self.rows_updated,
            "rows_skipped": self.rows_skipped,
            "message": self.message,
            "error": self.error,
        }


def fetch_sheet_data(
    config: Config,
    reverse_config: ReverseSyncConfig,
    logger: logging.Logger | None = None,
) -> tuple[list[str], list[list[Any]]]:
    """Fetch data from Google Sheets.

    Args:
        config: Main configuration with Google Sheets settings.
        reverse_config: Reverse sync configuration.
        logger: Optional logger instance.

    Returns:
        Tuple of (column_headers, data_rows).

    Raises:
        SheetsError: On Google Sheets API errors.
    """
    from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier

    if logger:
        logger.info(f"Fetching data from Google Sheets: {config.google_sheet_id}")

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

        if logger:
            logger.info(f"Connected to spreadsheet: {spreadsheet.title}")
            logger.info(f"Reading from worksheet: {worksheet_name}")

        # Get data from sheet
        if reverse_config.sheet_range:
            data = worksheet.get(reverse_config.sheet_range)
        else:
            data = worksheet.get_all_values()

        if not data:
            if logger:
                logger.warning("No data found in sheet")
            return [], []

        # Extract headers and rows
        if reverse_config.skip_header:
            headers = data[0]
            rows = data[1:]
        else:
            # If no header, generate column names
            headers = [f"col_{i}" for i in range(len(data[0]))]
            rows = data

        if logger:
            logger.info(f"Fetched {len(rows)} rows with {len(headers)} columns")

        return headers, rows

    except gspread.exceptions.SpreadsheetNotFound as e:
        raise SheetsError(
            message="Spreadsheet not found. Ensure the Service Account has access.",
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
            message=f"Failed to fetch data from Google Sheets: {e}",
            sheet_id=config.google_sheet_id,
            original_error=e,
        ) from e


def convert_value(
    value: Any,
    target_type: str | None = None,
    logger: logging.Logger | None = None,
) -> Any:
    """Convert a sheet value to a database-compatible type.

    Args:
        value: Raw value from sheet (usually string).
        target_type: Optional target type hint (int, float, date, datetime, bool, str).
            When specified, conversion is strict: if the value cannot be converted
            to the target type, returns None (allowing the database to reject it).
        logger: Optional logger for conversion warnings.

    Returns:
        Converted value suitable for database insertion.
        Returns None if target_type is specified and conversion fails.
    """
    # Handle empty values
    if value is None or value == "":
        return None

    # If already the right type, return as-is
    if isinstance(value, (int, float, bool, date, datetime, Decimal)):
        # But verify it matches target_type if specified
        if target_type:
            type_checks = {
                "int": (int,),
                "float": (int, float, Decimal),
                "bool": (bool,),
                "date": (date,),
                "datetime": (datetime,),
                "str": (str,),
            }
            expected_types = type_checks.get(target_type.lower())
            if expected_types and not isinstance(value, expected_types):
                if logger:
                    logger.warning(
                        f"Type mismatch: expected {target_type}, got {type(value).__name__} "
                        f"for value: {value!r}"
                    )
                return None
        return value

    # Convert string values
    if isinstance(value, str):
        value = value.strip()

        # If target_type is specified, only attempt that conversion
        if target_type:
            target_lower = target_type.lower()

            if target_lower == "str":
                return value

            if target_lower == "bool":
                if value.lower() in ("true", "yes", "1"):
                    return True
                if value.lower() in ("false", "no", "0"):
                    return False
                if logger:
                    logger.warning(f"Cannot convert '{value}' to bool")
                return None

            if target_lower == "int":
                try:
                    return int(value)
                except ValueError:
                    if logger:
                        logger.warning(f"Cannot convert '{value}' to int")
                    return None

            if target_lower == "float":
                try:
                    return float(value)
                except ValueError:
                    if logger:
                        logger.warning(f"Cannot convert '{value}' to float")
                    return None

            if target_lower == "date":
                try:
                    return datetime.strptime(value[:10], "%Y-%m-%d").date()
                except ValueError:
                    if logger:
                        logger.warning(f"Cannot convert '{value}' to date (expected YYYY-MM-DD)")
                    return None

            if target_lower == "datetime":
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        return datetime.strptime(value[:19], fmt)
                    except ValueError:
                        continue
                if logger:
                    logger.warning(
                        f"Cannot convert '{value}' to datetime "
                        "(expected YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD HH:MM:SS)"
                    )
                return None

            # Unknown target type - log and return None for strict mode
            if logger:
                logger.warning(f"Unknown target_type '{target_type}' for value: {value!r}")
            return None

        # No target_type specified - use auto-detection (original behavior)
        # Boolean detection
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # Number detection
        try:
            if "." in value or "e" in value.lower():
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Date/datetime detection (ISO format)
        if len(value) == 10 and "-" in value:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                pass

        if len(value) >= 19 and ("T" in value or " " in value):
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(value[:19], fmt)
                except ValueError:
                    pass

        # String value that didn't match any pattern in auto-detect mode
        return value

    # Non-string, non-typed value (e.g., bytes, bytearray, custom object)
    # In strict mode (target_type specified), reject these - we can't convert
    if target_type:
        if logger:
            logger.warning(
                f"Cannot convert {type(value).__name__} to {target_type}. "
                f"Value: {value!r}"
            )
        return None

    # Auto-detect mode: return as-is (original behavior)
    return value


def prepare_rows_for_db(
    headers: list[str],
    rows: list[list[Any]],
    reverse_config: ReverseSyncConfig,
    logger: logging.Logger | None = None,
) -> tuple[list[str], list[list[Any]]]:
    """Prepare sheet rows for database insertion.

    Applies column mapping and value conversion.

    Args:
        headers: Column headers from sheet.
        rows: Data rows from sheet.
        reverse_config: Reverse sync configuration.
        logger: Optional logger instance.

    Returns:
        Tuple of (db_columns, converted_rows).
    """
    # Apply column mapping if specified
    column_mapping = reverse_config.column_mapping or {}
    db_columns = [column_mapping.get(h, h) for h in headers]

    if logger and column_mapping:
        logger.debug(f"Applied column mapping: {column_mapping}")

    # Convert values
    converted_rows = []
    for row in rows:
        converted_row = []
        for value in row:
            converted_row.append(convert_value(value))
        converted_rows.append(converted_row)

    if logger:
        logger.debug(f"Converted {len(converted_rows)} rows for database insertion")

    return db_columns, converted_rows


def _build_database_config(config: Config) -> DatabaseConfig:
    """Build DatabaseConfig from main Config.

    Args:
        config: Main configuration object.

    Returns:
        DatabaseConfig for database connection.
    """
    return DatabaseConfig(
        db_type=config.db_type,
        host=config.db_host,
        port=config.db_port,
        user=config.db_user,
        password=config.db_password,
        database=config.db_name,
        connect_timeout=config.db_connect_timeout,
        read_timeout=config.db_read_timeout,
        ssl_mode=config.db_ssl_mode,
        ssl_ca=config.db_ssl_ca,
    )


def push_to_database(
    config: Config,
    columns: list[str],
    rows: list[list[Any]],
    reverse_config: ReverseSyncConfig,
    logger: logging.Logger | None = None,
) -> WriteResult:
    """Push data to the database.

    Args:
        config: Main configuration with database settings.
        columns: Column names.
        rows: Data rows to push.
        reverse_config: Reverse sync configuration.
        logger: Optional logger instance.

    Returns:
        WriteResult with affected row counts.

    Raises:
        DatabaseError: On database errors.
    """
    db_type = config.db_type.lower()

    if logger:
        logger.info(
            f"Connecting to {db_type.upper()}: {config.db_host}:{config.db_port}/{config.db_name}"
        )
        logger.info(f"Target table: {reverse_config.table_name}")
        logger.info(f"Conflict mode: {reverse_config.conflict_mode.value}")

    db_config = _build_database_config(config)

    try:
        with get_connection(db_config) as conn:
            total_result = WriteResult()

            # Process in batches
            batch_size = reverse_config.batch_size
            for i in range(0, len(rows), batch_size):
                batch = rows[i : i + batch_size]

                if logger:
                    batch_num = (i // batch_size) + 1
                    total_batches = (len(rows) + batch_size - 1) // batch_size
                    logger.debug(f"Processing batch {batch_num}/{total_batches}")

                if reverse_config.conflict_mode == ConflictMode.OVERWRITE:
                    if not reverse_config.key_columns:
                        raise ConfigError(
                            message="key_columns required for overwrite mode",
                            missing_fields=["key_columns"],
                        )
                    result = conn.upsert_rows(
                        table=reverse_config.table_name,
                        columns=columns,
                        rows=batch,
                        key_columns=reverse_config.key_columns,
                        update_columns=reverse_config.update_columns,
                    )
                elif reverse_config.conflict_mode == ConflictMode.SKIP:
                    # Use upsert but with empty update columns (DO NOTHING equivalent)
                    # For databases that support it, this will skip existing rows
                    if not reverse_config.key_columns:
                        raise ConfigError(
                            message="key_columns required for skip mode",
                            missing_fields=["key_columns"],
                        )
                    try:
                        result = conn.upsert_rows(
                            table=reverse_config.table_name,
                            columns=columns,
                            rows=batch,
                            key_columns=reverse_config.key_columns,
                            update_columns=[],  # Empty = skip on conflict
                        )
                    except DatabaseError as e:
                        # Only fall back if this looks like an "unsupported syntax" error
                        # for empty update_columns. Re-raise constraint violations
                        # (FK, CHECK, UNIQUE) and other errors immediately.
                        error_msg = str(e).lower()

                        # Check if this is a constraint violation - re-raise these
                        is_constraint_error = (
                            "foreign key" in error_msg
                            or "constraint" in error_msg
                            or "violates" in error_msg
                            or "duplicate" in error_msg
                            or "unique" in error_msg
                        )

                        # Check if this looks like syntax/unsupported feature error
                        is_syntax_error = (
                            "syntax" in error_msg
                            or "not supported" in error_msg
                            or "unknown" in error_msg
                        )

                        if is_constraint_error or not is_syntax_error:
                            # This is NOT the "empty update_columns unsupported" error
                            # Re-raise to avoid masking real issues
                            raise

                        # Likely the unsupported syntax error - fall back to individual inserts
                        if logger:
                            logger.debug(
                                f"Empty update_columns not supported on {config.db_type}, "
                                "falling back to individual row insertion"
                            )
                        result = _insert_skipping_duplicates(
                            conn,
                            reverse_config.table_name,
                            columns,
                            batch,
                            reverse_config.key_columns,
                            logger,
                        )
                else:  # ConflictMode.ERROR
                    result = conn.insert_rows(
                        table=reverse_config.table_name,
                        columns=columns,
                        rows=batch,
                    )

                # Accumulate results
                total_result.rows_affected += result.rows_affected
                total_result.rows_inserted += result.rows_inserted
                total_result.rows_updated += result.rows_updated
                total_result.rows_skipped += result.rows_skipped

            if logger:
                logger.info(f"Database write complete: {total_result.rows_affected} rows affected")

            return total_result

    except DatabaseError:
        raise
    except OSError as e:
        if logger:
            logger.error(f"Unexpected error pushing to database: {e}")
        raise DatabaseError(
            message=f"Unexpected error pushing to database: {e}",
            host=config.db_host,
            database=config.db_name,
            original_error=e,
        ) from e


def _is_duplicate_key_error(error: DatabaseError) -> bool:
    """Check if a DatabaseError is specifically a duplicate key violation.

    Uses database-specific error codes rather than string matching to avoid
    false positives from other constraint violations (FK, CHECK, etc.).

    Args:
        error: DatabaseError to check.

    Returns:
        True if the error is a duplicate key/unique constraint violation.
    """
    original = error.original_error
    if original is None:
        # Fallback to message check only for actual duplicate keywords
        # but be more specific than before
        msg = str(error).lower()
        return "duplicate entry" in msg or "unique constraint" in msg

    # MySQL: error code 1062 (ER_DUP_ENTRY)
    if hasattr(original, "errno") and original.errno == 1062:
        return True

    # PostgreSQL: SQLSTATE 23505 (unique_violation)
    if hasattr(original, "pgcode") and original.pgcode == "23505":
        return True

    # SQLite: SQLITE_CONSTRAINT_UNIQUE (typically shows in message)
    # SQLite errors have sqlite_errorcode attribute in newer versions
    if hasattr(original, "sqlite_errorcode"):
        # SQLITE_CONSTRAINT_UNIQUE = 2067
        if original.sqlite_errorcode == 2067:
            return True
    # Fallback for sqlite3.IntegrityError
    if "UNIQUE constraint failed" in str(original):
        return True

    # MSSQL: error 2627 (unique constraint) or 2601 (unique index)
    if hasattr(original, "number") and original.number in (2627, 2601):
        return True

    return False


def _insert_skipping_duplicates(
    conn: Any,
    table: str,
    columns: list[str],
    rows: list[list[Any]],
    key_columns: list[str],
    logger: logging.Logger | None = None,
) -> WriteResult:
    """Insert rows, skipping duplicates one at a time.

    Fallback for databases that don't support INSERT ... ON CONFLICT DO NOTHING.

    Args:
        conn: Database connection.
        table: Target table name.
        columns: Column names.
        rows: Data rows.
        key_columns: Key columns for duplicate detection.
        logger: Optional logger instance.

    Returns:
        WriteResult with affected row counts.

    Raises:
        DatabaseError: For non-duplicate constraint violations (FK, CHECK, etc.)
    """
    result = WriteResult()

    for row in rows:
        try:
            insert_result = conn.insert_rows(table, columns, [row])
            result.rows_inserted += insert_result.rows_inserted
            result.rows_affected += insert_result.rows_affected
        except DatabaseError as e:
            # Check if it's specifically a duplicate key error using error codes
            if _is_duplicate_key_error(e):
                result.rows_skipped += 1
                if logger:
                    logger.debug("Skipped duplicate row")
            else:
                # Re-raise other constraint violations (FK, CHECK, etc.)
                raise

    return result


def run_reverse_sync(
    config: Config | None = None,
    reverse_config: ReverseSyncConfig | None = None,
    logger: logging.Logger | None = None,
    dry_run: bool = False,
    preview: bool = False,
    table_name: str | None = None,
    key_columns: list[str] | None = None,
    conflict_mode: str | None = None,
) -> ReverseSyncResult:
    """Execute the full reverse sync operation.

    Args:
        config: Main configuration. If None, loads from environment.
        reverse_config: Reverse sync configuration. If None, builds from params.
        logger: Logger instance. If None, creates one.
        dry_run: If True, fetch data but don't write to database.
        preview: If True, show preview of data without writing.
        table_name: Target table name (used if reverse_config is None).
        key_columns: Key columns (used if reverse_config is None).
        conflict_mode: Conflict resolution mode (used if reverse_config is None).

    Returns:
        ReverseSyncResult with operation status and statistics.

    Raises:
        ConfigError: If configuration is invalid.
        SheetsError: If Google Sheets operations fail.
        DatabaseError: If database operations fail.
    """
    # Load config if not provided
    if config is None:
        config = get_config()

    # Setup logging if not provided
    if logger is None:
        from mysql_to_sheets.core.sync import setup_logging

        logger = setup_logging(config)

    # Build reverse_config if not provided
    if reverse_config is None:
        if not table_name:
            raise ConfigError(
                message="table_name is required for reverse sync",
                missing_fields=["table_name"],
            )
        reverse_config = ReverseSyncConfig(
            table_name=table_name,
            key_columns=key_columns or [],
            conflict_mode=ConflictMode(conflict_mode) if conflict_mode else ConflictMode.OVERWRITE,
        )

    db_type = config.db_type.lower()
    logger.info(f"Starting reverse sync: Google Sheets -> {db_type.upper()}")

    try:
        # Fetch data from Google Sheets
        headers, rows = fetch_sheet_data(config, reverse_config, logger)

        if not rows:
            logger.warning("No data to sync from sheet")
            return ReverseSyncResult(
                success=True,
                rows_processed=0,
                message="Reverse sync completed (empty dataset)",
            )

        # Prepare rows for database
        db_columns, prepared_rows = prepare_rows_for_db(headers, rows, reverse_config, logger)

        # Preview mode - just show data
        if preview:
            logger.info(f"Preview mode: would sync {len(prepared_rows)} rows")
            return ReverseSyncResult(
                success=True,
                rows_processed=len(prepared_rows),
                message=f"Preview: {len(prepared_rows)} rows would be synced",
            )

        # Dry run mode - validate without writing
        if dry_run:
            logger.info(f"Dry run: validated {len(prepared_rows)} rows")
            return ReverseSyncResult(
                success=True,
                rows_processed=len(prepared_rows),
                message=f"Dry run: validated {len(prepared_rows)} rows",
            )

        # Push to database
        result = push_to_database(config, db_columns, prepared_rows, reverse_config, logger)

        logger.info(
            f"Reverse sync completed: {result.rows_inserted} inserted, "
            f"{result.rows_updated} updated, {result.rows_skipped} skipped"
        )

        return ReverseSyncResult(
            success=True,
            rows_processed=len(prepared_rows),
            rows_inserted=result.rows_inserted,
            rows_updated=result.rows_updated,
            rows_skipped=result.rows_skipped,
            message=f"Successfully synced {result.rows_affected} rows",
        )

    except (SheetsError, DatabaseError, ConfigError, OSError, ValueError) as e:
        logger.error(f"Reverse sync failed: {e}")
        return ReverseSyncResult(
            success=False,
            message=str(e),
            error=str(e),
        )


class ReverseSyncService:
    """Service class for reverse sync operations with reusable configuration.

    Provides a stateful interface for reverse sync operations,
    useful for API and web contexts.

    Attributes:
        config: Main configuration object.
        logger: Logger instance.
    """

    def __init__(
        self,
        config: Config | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize ReverseSyncService.

        Args:
            config: Configuration object. If None, loads from environment.
            logger: Logger instance. If None, creates one from config.
        """
        self.config = config or get_config()
        if logger is None:
            from mysql_to_sheets.core.sync import setup_logging

            logger = setup_logging(self.config)
        self.logger = logger

    def sync(
        self,
        reverse_config: ReverseSyncConfig,
        dry_run: bool = False,
    ) -> ReverseSyncResult:
        """Execute reverse sync with the given configuration.

        Args:
            reverse_config: Reverse sync configuration.
            dry_run: If True, validate without writing to database.

        Returns:
            ReverseSyncResult with operation status.
        """
        return run_reverse_sync(self.config, reverse_config, self.logger, dry_run=dry_run)

    def sync_simple(
        self,
        table_name: str,
        key_columns: list[str] | None = None,
        conflict_mode: str = "overwrite",
        dry_run: bool = False,
    ) -> ReverseSyncResult:
        """Execute reverse sync with simple parameters.

        Args:
            table_name: Target database table.
            key_columns: Columns for duplicate detection.
            conflict_mode: How to handle duplicates (overwrite, skip, error).
            dry_run: If True, validate without writing.

        Returns:
            ReverseSyncResult with operation status.
        """
        return run_reverse_sync(
            self.config,
            reverse_config=None,
            logger=self.logger,
            dry_run=dry_run,
            table_name=table_name,
            key_columns=key_columns,
            conflict_mode=conflict_mode,
        )
