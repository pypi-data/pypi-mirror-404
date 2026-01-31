"""Database to Google Sheets sync logic.

This module contains the core sync functionality extracted from the original
sync_db.py script. Functions raise exceptions instead of calling sys.exit()
to enable proper error handling in API and CLI contexts.

Supports multiple databases:
- MySQL (default)
- PostgreSQL

Supports multiple sync modes:
- replace: Clear sheet and push all data (default)
- append: Add rows without clearing existing data
- streaming: Process large datasets in chunks
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import gspread

if TYPE_CHECKING:
    from mysql_to_sheets.core.notifications.base import NotificationConfig
    from mysql_to_sheets.core.pii import PIITransformConfig

from mysql_to_sheets.core.column_mapping import (
    ColumnMappingConfig,
    apply_column_mapping,
    get_column_mapping_config,
)
from mysql_to_sheets.core.config import Config, get_config
from mysql_to_sheets.core.database import (
    DatabaseConfig,
    get_connection,
)
from mysql_to_sheets.core.database import (
    clean_value as db_clean_value,
)
from mysql_to_sheets.core.diff import DiffResult, run_preview
from mysql_to_sheets.core.exceptions import (
    ConfigError,
    DatabaseError,
    ErrorCode,
    SheetsError,
    SyncError,
)
from mysql_to_sheets.core.incremental import IncrementalConfig, build_incremental_query
from mysql_to_sheets.core.query_cache import get_query_cache, make_cache_key
from mysql_to_sheets.core.retry import (
    RetryConfig,
    parse_sheets_rate_limit,
    retry,
)


def detect_sheets_api_not_enabled(error: Exception) -> str | None:
    """Detect if a gspread error is caused by Google Sheets API not being enabled.

    EC-39: Users often create a service account but forget to enable the Sheets API
    in their GCP project, resulting in cryptic 403 errors.

    Args:
        error: The gspread exception to analyze.

    Returns:
        Helpful error message if API not enabled, None otherwise.
    """
    error_str = str(error).lower()

    # Common patterns for API-not-enabled errors
    api_not_enabled_patterns = [
        "accessnotconfigured",
        "api has not been used",
        "sheets api has not been enabled",
        "google sheets api has not been used",
        "is disabled",  # Matches "sheets.googleapis.com is disabled"
        "enable it by visiting",
        "project has not enabled the api",
    ]

    if any(pattern in error_str for pattern in api_not_enabled_patterns):
        return (
            f"The Google Sheets API is not enabled in your Google Cloud project.\n\n"
            f"To enable it:\n"
            f"  1. Go to: https://console.cloud.google.com/apis/library/sheets.googleapis.com\n"
            f"  2. Select your project from the dropdown\n"
            f"  3. Click \"Enable\"\n"
            f"  4. Wait 1-2 minutes, then re-run: mysql-to-sheets test-sheets\n\n"
            f"Error code: {ErrorCode.SHEETS_API_NOT_ENABLED}"
        )

    return None


# Google Sheets limits
# See: https://developers.google.com/sheets/api/limits
SHEETS_MAX_CELLS = 10_000_000  # Maximum cells per spreadsheet
SHEETS_MAX_COLUMNS = 18_278  # Column ZZZ (26 + 26*26 + 26*26*26)
SHEETS_MAX_ROWS_PER_SHEET = 10_000_000  # Maximum rows per worksheet
SHEETS_CELL_SIZE_LIMIT = 50_000  # Maximum characters per cell


def validate_batch_size(
    headers: list[str],
    rows: list[list[Any]],
    logger: logging.Logger | None = None,
) -> None:
    """Validate data fits within Google Sheets limits.

    Args:
        headers: Column headers.
        rows: Data rows.
        logger: Optional logger.

    Raises:
        SheetsError: If data exceeds Sheets limits.
    """
    num_columns = len(headers)
    num_rows = len(rows) + 1  # +1 for header row
    total_cells = num_columns * num_rows

    if num_columns > SHEETS_MAX_COLUMNS:
        msg = (
            f"Column count {num_columns:,} exceeds Google Sheets limit of "
            f"{SHEETS_MAX_COLUMNS:,}. Reduce columns in your SQL query."
        )
        if logger:
            logger.error(msg)
        raise SheetsError(
            message=msg,
            code="SHEETS_309",
        )

    if num_rows > SHEETS_MAX_ROWS_PER_SHEET:
        msg = (
            f"Row count {num_rows:,} exceeds Google Sheets limit of "
            f"{SHEETS_MAX_ROWS_PER_SHEET:,}. Use streaming mode with smaller chunks."
        )
        if logger:
            logger.error(msg)
        raise SheetsError(
            message=msg,
            code="SHEETS_310",
        )

    if total_cells > SHEETS_MAX_CELLS:
        msg = (
            f"Total cell count {total_cells:,} exceeds Google Sheets limit of "
            f"{SHEETS_MAX_CELLS:,}. Use streaming mode with smaller chunks or "
            f"reduce columns/rows in your query."
        )
        if logger:
            logger.error(msg)
        raise SheetsError(
            message=msg,
            code="SHEETS_311",
        )

    # Validate row column counts match header count (ragged row detection)
    expected_cols = len(headers)
    ragged_rows: list[tuple[int, int]] = []  # (row_idx, actual_col_count)
    for row_idx, row in enumerate(rows):
        actual_cols = len(row)
        if actual_cols != expected_cols:
            ragged_rows.append((row_idx, actual_cols))
            # Report up to 5 ragged rows
            if len(ragged_rows) >= 5:
                break

    if ragged_rows:
        examples = ", ".join(
            f"row {idx + 1} has {cols} columns" for idx, cols in ragged_rows[:3]
        )
        more = f" (and {len(ragged_rows) - 3} more)" if len(ragged_rows) > 3 else ""
        msg = (
            f"Data has inconsistent column counts. Expected {expected_cols} columns "
            f"(based on headers), but {examples}{more}. "
            f"Check your SQL query for NULL columns or use COALESCE() to ensure consistent row lengths."
        )
        if logger:
            logger.error(msg)
        raise ConfigError(
            message=msg,
            code="CONFIG_106",
        )

    # Validate individual cell sizes (50KB limit per cell)
    # Google Sheets API may use byte count for non-ASCII content, so we check both
    high_byte_ratio_warnings: list[str] = []
    for row_idx, row in enumerate(rows):
        for col_idx, cell in enumerate(row):
            cell_str = str(cell) if cell is not None else ""
            cell_size = len(cell_str)
            if cell_size > SHEETS_CELL_SIZE_LIMIT:
                col_name = headers[col_idx] if col_idx < len(headers) else f"column {col_idx}"
                msg = (
                    f"Cell at row {row_idx + 1}, column '{col_name}' contains "
                    f"{cell_size:,} characters, exceeding Google Sheets limit of "
                    f"{SHEETS_CELL_SIZE_LIMIT:,}. Truncate the data or exclude this column."
                )
                if logger:
                    logger.error(msg)
                raise SheetsError(
                    message=msg,
                    code="SHEETS_312",
                )

            # Check for high byte ratio (emoji/CJK content)
            # UTF-8 encoding can be 1-4 bytes per character
            # Warn if byte count is significantly higher than char count
            if cell_size > 1000:  # Only check cells with substantial content
                byte_size = len(cell_str.encode("utf-8"))
                byte_ratio = byte_size / cell_size if cell_size > 0 else 1.0

                # If bytes > 2x characters, likely emoji/CJK heavy content
                # This could cause API issues even if char count is under limit
                if byte_ratio > 2.0 and byte_size > SHEETS_CELL_SIZE_LIMIT:
                    col_name = headers[col_idx] if col_idx < len(headers) else f"column {col_idx}"
                    high_byte_ratio_warnings.append(
                        f"row {row_idx + 1}, column '{col_name}' "
                        f"({cell_size:,} chars, {byte_size:,} bytes)"
                    )

    # Log warning about high byte ratio content (potential API issues)
    if high_byte_ratio_warnings and logger:
        logger.warning(
            f"Cells with high Unicode content may exceed API byte limits: "
            f"{'; '.join(high_byte_ratio_warnings[:3])}"
            + (f" (and {len(high_byte_ratio_warnings) - 3} more)" if len(high_byte_ratio_warnings) > 3 else "")
        )

    if logger:
        logger.debug(
            f"Batch size validated: {num_columns} columns x {num_rows} rows = "
            f"{total_cells:,} cells (limit: {SHEETS_MAX_CELLS:,})"
        )


def validate_query_type(
    query: str,
    logger: logging.Logger | None = None,
    strict: bool = False,
) -> None:
    """Validate that the query is a SELECT statement.

    Non-SELECT queries (INSERT, UPDATE, DELETE, etc.) don't return data and
    would result in a "successful" sync with 0 rows, potentially clearing the
    sheet entirely if sync_empty_result_action=clear.

    Args:
        query: SQL query to validate.
        logger: Optional logger.
        strict: If True, raise ConfigError for non-SELECT. If False, log warning.

    Raises:
        ConfigError: If strict=True and query is not SELECT.
    """
    # Normalize query for analysis: strip whitespace, comments, and get first keyword
    normalized = query.strip()

    # Remove leading comments (single-line and multi-line)
    while normalized.startswith("--") or normalized.startswith("/*"):
        if normalized.startswith("--"):
            # Single-line comment: skip to end of line
            newline_pos = normalized.find("\n")
            if newline_pos == -1:
                normalized = ""
            else:
                normalized = normalized[newline_pos + 1:].strip()
        elif normalized.startswith("/*"):
            # Multi-line comment: skip to */
            end_pos = normalized.find("*/")
            if end_pos == -1:
                normalized = ""
            else:
                normalized = normalized[end_pos + 2:].strip()

    # EC-47: Strip leading parentheses for subquery validation
    # Valid queries like "(SELECT * FROM users) UNION ..." have first word "(SELECT"
    # which doesn't match "SELECT". Strip parens to get actual keyword.
    keyword_check = normalized
    while keyword_check.startswith("("):
        keyword_check = keyword_check[1:].lstrip()

    # Get first keyword (uppercase for comparison)
    first_word = keyword_check.split()[0].upper() if keyword_check.split() else ""

    # DML statements that modify data and don't return result sets
    dml_keywords = {"INSERT", "UPDATE", "DELETE", "TRUNCATE", "DROP", "ALTER", "CREATE"}

    # CTEs start with WITH but should be followed by SELECT
    if first_word == "WITH":
        # Check if it's a CTE (WITH ... AS ... SELECT)
        upper_query = normalized.upper()
        if "SELECT" not in upper_query:
            msg = (
                "Query appears to be a CTE (WITH clause) but doesn't contain SELECT. "
                "SQL_QUERY must return data to sync. "
                "If this is a data modification query, it won't return rows to push to Sheets."
            )
            if strict:
                if logger:
                    logger.error(msg)
                raise ConfigError(message=msg, code="CONFIG_107")
            elif logger:
                logger.warning(msg)
        return  # WITH ... SELECT is valid

    if first_word in dml_keywords:
        msg = (
            f"SQL_QUERY starts with '{first_word}' which modifies data instead of returning it. "
            f"Sync requires a SELECT query to fetch data. "
            f"This query would execute successfully but return 0 rows, "
            f"potentially clearing your Google Sheet."
        )
        if strict:
            if logger:
                logger.error(msg)
            raise ConfigError(message=msg, code="CONFIG_107")
        elif logger:
            logger.warning(msg)
        return

    # SELECT, SHOW, DESCRIBE, EXPLAIN are valid read queries
    valid_read_keywords = {"SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN", "TABLE"}
    if first_word not in valid_read_keywords and first_word:
        msg = (
            f"SQL_QUERY starts with '{first_word}' which may not return data. "
            f"Expected a SELECT query. If this is intentional, you can ignore this warning."
        )
        if logger:
            logger.warning(msg)


# Retry configuration for Sheets rate limits
# Uses longer delays since rate limits are per-minute quotas
_SHEETS_RATE_LIMIT_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=60.0,  # Start with 60s for rate limits
    max_delay=600.0,  # Cap at 10 minutes
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=(gspread.exceptions.APIError,),
)


def _sheets_api_call_with_retry(
    operation: str,
    api_call: Any,  # Callable
    logger: logging.Logger | None = None,
    max_attempts: int = 5,
) -> Any:
    """Execute a Sheets API call with rate limit retry.

    Implements exponential backoff when rate limited, respecting the
    retry_after value from the API response.

    Args:
        operation: Description of the operation (for logging).
        api_call: Callable that makes the API call.
        logger: Optional logger.
        max_attempts: Maximum retry attempts.

    Returns:
        Result of the API call.

    Raises:
        SheetsError: If all retries exhausted or non-retryable error.
    """
    import time

    last_error: Exception | None = None
    base_delay = 60.0  # Start with 60s for rate limits

    for attempt in range(max_attempts):
        try:
            return api_call()
        except gspread.exceptions.APIError as e:
            last_error = e
            rate_limit_info = parse_sheets_rate_limit(e)

            if not rate_limit_info.is_rate_limited:
                # Not a rate limit error, don't retry
                raise

            if attempt >= max_attempts - 1:
                # Last attempt, raise the error
                break

            # Calculate delay: use retry_after if provided, otherwise exponential backoff
            if rate_limit_info.retry_after and rate_limit_info.retry_after > 0:
                delay = rate_limit_info.retry_after
            else:
                delay = base_delay * (2**attempt)
                delay = min(delay, 600.0)  # Cap at 10 minutes

            if logger:
                logger.warning(
                    f"Sheets rate limit hit during {operation} "
                    f"(quota: {rate_limit_info.quota_type}). "
                    f"Retrying in {delay:.0f}s (attempt {attempt + 1}/{max_attempts})"
                )

            time.sleep(delay)

    # All retries exhausted
    if last_error:
        rate_limit_info = parse_sheets_rate_limit(last_error)
        raise SheetsError(
            message=(
                f"Rate limit exceeded after {max_attempts} retries "
                f"({rate_limit_info.quota_type})"
            ),
            code="SHEETS_304",
            rate_limited=True,
            retry_after=rate_limit_info.retry_after,
        ) from last_error

    raise RuntimeError("Unexpected state in _sheets_api_call_with_retry")


@dataclass
class SyncResult:
    """Result of a sync operation.

    Attributes:
        success: Whether the sync completed successfully.
        rows_synced: Number of data rows synced (excluding header).
        columns: Number of columns in the synced data.
        headers: List of column headers.
        message: Human-readable status message.
        error: Error details if sync failed.
        preview: Whether this was a preview-only run.
        diff: Diff result if preview mode was used.
        schema_changes: Schema change information if detected.
    """

    success: bool
    rows_synced: int = 0
    columns: int = 0
    headers: list[str] = field(default_factory=list)
    message: str = ""
    error: str | None = None
    preview: bool = False
    diff: DiffResult | None = None
    schema_changes: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for API responses.

        Returns:
            Dictionary representation of the result.
        """
        result = {
            "success": self.success,
            "rows_synced": self.rows_synced,
            "columns": self.columns,
            "headers": self.headers,
            "message": self.message,
            "error": self.error,
            "preview": self.preview,
        }
        if self.diff is not None:
            result["diff"] = self.diff.to_dict()
        if self.schema_changes is not None:
            result["schema_changes"] = self.schema_changes
        return result


def setup_logging(config: Config) -> logging.Logger:
    """Configure logging to file and console.

    Args:
        config: Configuration object with log settings.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("mysql_to_sheets")
    logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    log_path = Path(config.log_file)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Fall back to platform directory if current location is not writable
        from mysql_to_sheets.core.paths import get_default_log_path

        log_path = get_default_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler(
        log_path, maxBytes=config.log_max_bytes, backupCount=config.log_backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger


def _build_column_mapping_config(config: Config) -> ColumnMappingConfig:
    """Build ColumnMappingConfig from main Config.

    Args:
        config: Main configuration object.

    Returns:
        ColumnMappingConfig for column transformations.
    """
    return get_column_mapping_config(
        enabled=config.column_mapping_enabled,
        rename_map=config.column_mapping if config.column_mapping else None,
        column_order=config.column_order if config.column_order else None,
        case_transform=config.column_case if config.column_case != "none" else None,
        strip_prefix=config.column_strip_prefix if config.column_strip_prefix else None,
        strip_suffix=config.column_strip_suffix if config.column_strip_suffix else None,
    )


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


def fetch_data(
    config: Config,
    logger: logging.Logger | None = None,
    incremental_config: IncrementalConfig | None = None,
    use_pool: bool = False,
    batch_size: int | None = None,
) -> tuple[list[str], list[list[Any]]]:
    """Connect to database and execute the configured query.

    Supports both MySQL and PostgreSQL databases. The database type is
    determined by config.db_type ('mysql' or 'postgres').

    Args:
        config: Configuration with database credentials and query.
        logger: Optional logger instance.
        incremental_config: Optional incremental sync configuration.
        use_pool: If True, use connection pooling (MySQL only, requires db_pool_enabled).
        batch_size: If set, fetch rows in batches (memory-efficient).
            If None, uses fetchall() (current behavior).

    Returns:
        Tuple of (column_headers, data_rows).

    Raises:
        DatabaseError: On database connection or query errors.
    """
    db_type = config.db_type.lower()

    if logger:
        logger.info(
            f"Connecting to {db_type.upper()}: {config.db_host}:{config.db_port}/{config.db_name}"
        )

    # Build query (potentially with incremental filtering)
    query = config.sql_query

    # Validate query is a SELECT statement (warns by default, can be made strict)
    validate_query_type(query, logger, strict=config.sql_validation_enabled)

    if incremental_config and incremental_config.is_active():
        query = build_incremental_query(query, incremental_config)
        if logger:
            logger.info(
                f"Using incremental sync with filter on {incremental_config.timestamp_column}"
            )

    # Check query cache
    cache_key = ""
    if config.query_cache_enabled:
        cache_key = make_cache_key(query, db_type, config.db_host, config.db_name)
        cache = get_query_cache(config.query_cache_backend, config.redis_url)
        cached = cache.get(cache_key)
        if cached is not None:
            if logger:
                logger.info("Query cache hit — returning cached result")
            return cached

    # Use connection pooling if enabled and requested
    if use_pool and config.db_pool_enabled and db_type == "mysql":
        headers, rows = _fetch_data_pooled(config, query, logger, batch_size)
    elif use_pool and config.db_pool_enabled and db_type == "postgres":
        headers, rows = _fetch_data_pg_pooled(config, query, logger, batch_size)
    else:
        # Use database abstraction layer
        db_config = _build_database_config(config)

        try:
            with get_connection(db_config) as conn:
                if logger:
                    query_preview = query[:100]
                    logger.info(f"Executing query: {query_preview}...")

                result = conn.execute(query)

                if logger:
                    logger.info(
                        f"Fetched {result.row_count} rows with {len(result.headers)} columns"
                    )

                headers, rows = result.headers, result.rows

        except DatabaseError:
            raise
        except (OSError, RuntimeError, ValueError) as e:
            if logger:
                logger.error(f"Unexpected error fetching data: {e}")
            raise DatabaseError(
                message=f"Unexpected error fetching data: {e}",
                host=config.db_host,
                database=config.db_name,
                original_error=e,
            ) from e

    # Store in cache
    if config.query_cache_enabled and cache_key:
        cache = get_query_cache(config.query_cache_backend, config.redis_url)
        cache.set(cache_key, headers, rows, config.query_cache_ttl_seconds)
        if logger:
            logger.info("Query result cached")

    return headers, rows


def _fetch_data_pooled(
    config: Config,
    query: str,
    logger: logging.Logger | None = None,
    batch_size: int | None = None,
) -> tuple[list[str], list[list[Any]]]:
    """Fetch data using MySQL connection pool.

    This is a separate function to handle the MySQL-specific pooling logic.

    Args:
        config: Configuration with database credentials.
        query: SQL query to execute.
        logger: Optional logger instance.
        batch_size: If set, fetch rows in batches.

    Returns:
        Tuple of (column_headers, data_rows).
    """
    from mysql.connector import Error as MySQLError

    from mysql_to_sheets.core.connection_pool import PoolConfig, get_connection_pool

    connection = None
    cursor = None

    try:
        pool = get_connection_pool(
            config,
            PoolConfig(pool_size=config.db_pool_size),
        )
        connection = pool.get_connection()
        if logger:
            logger.debug("Using pooled MySQL connection")

        cursor = connection.cursor()
        if logger:
            query_preview = query[:100]
            logger.info(f"Executing query: {query_preview}...")
        cursor.execute(query)

        # Get column headers from cursor description
        headers = [desc[0] for desc in cursor.description]

        # Fetch data - either all at once or in batches
        if batch_size is not None and batch_size > 0:
            if logger:
                logger.debug(f"Using batch fetching with size {batch_size}")
            rows = []
            while True:
                batch = cursor.fetchmany(batch_size)
                if not batch:
                    break
                rows.extend([list(row) for row in batch])
        else:
            rows = [list(row) for row in cursor.fetchall()]

        if logger:
            logger.info(f"Fetched {len(rows)} rows with {len(headers)} columns")

        return headers, rows

    except MySQLError as e:
        if logger:
            logger.error(f"MySQL error: {e}")
        raise DatabaseError(
            message=f"Failed to fetch data from MySQL: {e}",
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


def _fetch_data_pg_pooled(
    config: Config,
    query: str,
    logger: logging.Logger | None = None,
    batch_size: int | None = None,
) -> tuple[list[str], list[list[Any]]]:
    """Fetch data using PostgreSQL connection pool.

    Args:
        config: Configuration with database credentials.
        query: SQL query to execute.
        logger: Optional logger instance.
        batch_size: If set, fetch rows in batches.

    Returns:
        Tuple of (column_headers, data_rows).
    """
    from mysql_to_sheets.core.database.postgres import pg_pooled_connection

    try:
        with pg_pooled_connection(config, pool_size=config.db_pool_size) as connection:
            if logger:
                logger.debug("Using pooled PostgreSQL connection")

            cursor = connection.cursor()
            try:
                if logger:
                    query_preview = query[:100]
                    logger.info(f"Executing query: {query_preview}...")
                cursor.execute(query)

                headers = [desc[0] for desc in cursor.description] if cursor.description else []

                if batch_size is not None and batch_size > 0:
                    if logger:
                        logger.debug(f"Using batch fetching with size {batch_size}")
                    rows: list[list[Any]] = []
                    while True:
                        batch = cursor.fetchmany(batch_size)
                        if not batch:
                            break
                        rows.extend([list(row) for row in batch])
                else:
                    rows = [list(row) for row in cursor.fetchall()]

                if logger:
                    logger.info(f"Fetched {len(rows)} rows with {len(headers)} columns")

                return headers, rows
            finally:
                cursor.close()

    except DatabaseError:
        raise
    except OSError as e:
        if logger:
            logger.error(f"PostgreSQL pool error: {e}")
        raise DatabaseError(
            message=f"Failed to fetch data from PostgreSQL pool: {e}",
            host=config.db_host,
            database=config.db_name,
            original_error=e,
        ) from e


def clean_value(value: Any, db_type: str = "mysql") -> Any:
    """Convert a single value to a Google Sheets compatible type.

    This function delegates to the database-aware type converter in the
    database module, which handles database-specific types like PostgreSQL
    arrays, UUIDs, and JSON.

    Args:
        value: Raw value from database.
        db_type: Database type for type-specific conversions.

    Returns:
        Cleaned value suitable for Google Sheets.
    """
    return db_clean_value(value, db_type)


def clean_data(
    rows: list[list[Any]],
    logger: logging.Logger | None = None,
    db_type: str = "mysql",
) -> list[list[Any]]:
    """Convert all values in rows to Google Sheets compatible types.

    Args:
        rows: Raw data rows from database.
        logger: Optional logger instance.
        db_type: Database type for type-specific conversions.

    Returns:
        Cleaned rows with converted types.
    """
    if logger:
        logger.debug("Cleaning data for Google Sheets compatibility")
    cleaned = []
    for row in rows:
        cleaned.append([clean_value(v, db_type) for v in row])
    return cleaned


def push_to_sheets(
    config: Config,
    headers: list[str],
    rows: list[list[Any]],
    logger: logging.Logger | None = None,
    mode: str = "replace",
    create_worksheet: bool | None = None,
) -> None:
    """Push data to Google Sheets.

    Args:
        config: Configuration with Google Sheets settings.
        headers: Column headers.
        rows: Data rows.
        logger: Optional logger instance.
        mode: Sync mode - 'replace' clears first, 'append' adds to existing.
        create_worksheet: If True, create the worksheet if it doesn't exist.
            If None, uses config.worksheet_auto_create.

    Raises:
        SheetsError: On Google Sheets API errors.
    """
    # Import here to avoid circular dependency
    from mysql_to_sheets.core.sheets_utils import (
        get_or_create_worksheet,
        parse_worksheet_identifier,
    )

    if logger:
        logger.info(f"Authenticating with Google Sheets via {config.service_account_file}")

    # Determine whether to auto-create worksheet
    should_create = (
        create_worksheet if create_worksheet is not None else config.worksheet_auto_create
    )

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

        # Get or create the worksheet
        worksheet = get_or_create_worksheet(
            spreadsheet,
            worksheet_name,
            create_if_missing=should_create,
            rows=config.worksheet_default_rows,
            cols=config.worksheet_default_cols,
            logger=logger,
        )

        if logger:
            logger.info(f"Connected to spreadsheet: {spreadsheet.title}")
            logger.info(f"Target worksheet: {worksheet_name}")
            logger.info(f"Sync mode: {mode}")

        # Validate batch size before pushing
        validate_batch_size(headers, rows, logger)

        if mode == "replace":
            # Clear existing content
            if logger:
                logger.info("Clearing existing sheet content")
            _sheets_api_call_with_retry(
                operation="clear sheet",
                api_call=worksheet.clear,
                logger=logger,
            )

            # Prepare data with headers as first row
            all_data = [headers] + rows

            # Batch update - single API call with rate limit retry
            if logger:
                logger.info(f"Pushing {len(rows)} rows to sheet")
            _sheets_api_call_with_retry(
                operation="update sheet",
                api_call=lambda: worksheet.update(
                    values=all_data,
                    range_name="A1",
                    value_input_option="USER_ENTERED",  # type: ignore[arg-type]
                ),
                logger=logger,
            )
        elif mode == "append":
            # Validate column alignment with existing sheet headers
            if logger:
                logger.info("Checking existing sheet headers for append mode")
            existing_data = _sheets_api_call_with_retry(
                operation="get existing headers",
                api_call=lambda: worksheet.row_values(1),
                logger=logger,
            )
            existing_headers = existing_data if existing_data else []

            # Only validate if sheet has existing headers
            if existing_headers:
                if existing_headers != headers:
                    # Provide detailed mismatch information
                    missing_in_sheet = set(headers) - set(existing_headers)
                    missing_in_data = set(existing_headers) - set(headers)
                    # Detect column order mismatch: same columns but different order
                    order_mismatch = (
                        set(headers) == set(existing_headers) and headers != existing_headers
                    )

                    details = []
                    if missing_in_sheet:
                        details.append(f"columns in data but not in sheet: {sorted(missing_in_sheet)}")
                    if missing_in_data:
                        details.append(f"columns in sheet but not in data: {sorted(missing_in_data)}")
                    if not missing_in_sheet and not missing_in_data and order_mismatch:
                        details.append("column order differs")

                    detail_str = "; ".join(details) if details else "headers differ"
                    msg = (
                        f"Append mode column mismatch: {detail_str}. "
                        f"Expected columns: {existing_headers[:5]}{'...' if len(existing_headers) > 5 else ''}, "
                        f"got: {headers[:5]}{'...' if len(headers) > 5 else ''}. "
                        f"Use --mode=replace to overwrite with new column structure."
                    )
                    if logger:
                        logger.error(msg)
                    raise SheetsError(
                        message=msg,
                        code="SHEETS_313",
                    )
            else:
                # Empty sheet - add headers first, then append rows
                if logger:
                    logger.info("Sheet is empty, adding headers before appending data")
                _sheets_api_call_with_retry(
                    operation="add headers",
                    api_call=lambda: worksheet.update(
                        values=[headers],
                        range_name="A1",
                        value_input_option="USER_ENTERED",  # type: ignore[arg-type]
                    ),
                    logger=logger,
                )

            # Append without clearing, with rate limit retry
            if logger:
                logger.info(f"Appending {len(rows)} rows to sheet")
            _sheets_api_call_with_retry(
                operation="append rows",
                api_call=lambda: worksheet.append_rows(
                    values=rows,
                    value_input_option="USER_ENTERED",  # type: ignore[arg-type]
                ),
                logger=logger,
            )
        else:
            raise ValueError(f"Unknown sync mode: {mode}")

        if logger:
            logger.info("Successfully pushed data to Google Sheets")

    except gspread.exceptions.SpreadsheetNotFound as e:
        if logger:
            logger.error(f"Spreadsheet not found: {config.google_sheet_id}")
            logger.error("Ensure the Service Account has access to this spreadsheet")
        raise SheetsError(
            message="Spreadsheet not found. Ensure the Service Account has access.",
            sheet_id=config.google_sheet_id,
            original_error=e,
        ) from e
    except gspread.exceptions.WorksheetNotFound as e:
        if logger:
            logger.error(f"Worksheet not found: {config.google_worksheet_name}")
        raise SheetsError(
            message=f"Worksheet '{config.google_worksheet_name}' not found",
            sheet_id=config.google_sheet_id,
            worksheet_name=config.google_worksheet_name,
            original_error=e,
        ) from e
    except gspread.exceptions.APIError as e:
        # EC-39: Check for API-not-enabled error
        api_not_enabled_msg = detect_sheets_api_not_enabled(e)
        if api_not_enabled_msg:
            if logger:
                logger.error(api_not_enabled_msg)
            raise SheetsError(
                message=api_not_enabled_msg,
                sheet_id=config.google_sheet_id,
                worksheet_name=config.google_worksheet_name,
                original_error=e,
                code=ErrorCode.SHEETS_API_NOT_ENABLED,
            ) from e

        # Parse rate limit information
        rate_limit_info = parse_sheets_rate_limit(e)

        if rate_limit_info.is_rate_limited:
            if logger:
                logger.warning(
                    f"Google Sheets rate limit hit (quota: {rate_limit_info.quota_type}). "
                    f"Retry after: {rate_limit_info.retry_after}s"
                )
            raise SheetsError(
                message=f"Rate limit exceeded ({rate_limit_info.quota_type})",
                sheet_id=config.google_sheet_id,
                worksheet_name=config.google_worksheet_name,
                original_error=e,
                rate_limited=True,
                retry_after=rate_limit_info.retry_after,
            ) from e
        else:
            if logger:
                logger.error(f"Google Sheets API error: {e}")
            raise SheetsError(
                message=f"Google Sheets API error: {e}",
                sheet_id=config.google_sheet_id,
                worksheet_name=config.google_worksheet_name,
                original_error=e,
            ) from e
    except (OSError, RuntimeError, ValueError) as e:
        if logger:
            logger.error(f"Unexpected error pushing to sheets: {e}")
        raise SheetsError(
            message=f"Unexpected error pushing to sheets: {e}",
            sheet_id=config.google_sheet_id,
            worksheet_name=config.google_worksheet_name,
            original_error=e,
        ) from e


def _get_notification_config(config: Config) -> "NotificationConfig":
    """Create NotificationConfig from main Config.

    Args:
        config: Main configuration object.

    Returns:
        NotificationConfig with notification settings.
    """
    from mysql_to_sheets.core.notifications.base import NotificationConfig

    return NotificationConfig(
        notify_on_success=config.notify_on_success,
        notify_on_failure=config.notify_on_failure,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_user=config.smtp_user,
        smtp_password=config.smtp_password,
        smtp_from=config.smtp_from,
        smtp_to=config.smtp_to,
        smtp_use_tls=config.smtp_use_tls,
        slack_webhook_url=config.slack_webhook_url,
        notification_webhook_url=config.notification_webhook_url,
    )


def _send_notification(
    result: SyncResult,
    config: Config,
    logger: logging.Logger,
    dry_run: bool = False,
    source: str = "sync",
    duration_ms: float = 0.0,
) -> None:
    """Send notification for sync result.

    This function handles notification sending gracefully - failures
    are logged but do not raise exceptions.

    Args:
        result: Sync result to notify about.
        config: Main configuration with notification settings.
        logger: Logger instance.
        dry_run: Whether this was a dry run.
        source: Source of the sync (cli, api, web, scheduler).
        duration_ms: Sync duration in milliseconds.
    """
    from mysql_to_sheets.core.notifications import (
        NotificationPayload,
        get_notification_manager,
    )

    notification_config = _get_notification_config(config)

    # Check if any notification is configured
    manager = get_notification_manager()
    configured_backends = manager.get_configured_backends(notification_config)
    if not configured_backends:
        logger.debug("No notification backends configured, skipping notification")
        return

    # Build notification payload
    payload = NotificationPayload(
        success=result.success,
        rows_synced=result.rows_synced,
        sheet_id=config.google_sheet_id,
        worksheet=config.google_worksheet_name,
        message=result.message,
        error=result.error,
        duration_ms=duration_ms,
        dry_run=dry_run,
        headers=result.headers,
        source=source,
    )

    # Send notification (failures are logged, not raised)
    try:
        results = manager.send_notification(payload, notification_config)
        if results["sent"]:
            logger.info(f"Notifications sent via: {', '.join(results['sent'])}")
        if results["failed"]:
            logger.warning(f"Notification failures: {results['errors']}")
    except (OSError, RuntimeError, KeyError) as e:
        logger.warning(f"Failed to send notifications: {e}")


def _send_schema_change_notification(
    schema_change: Any,
    policy: str,
    config: Config,
    logger: logging.Logger,
) -> None:
    """Send notification for schema change detection.

    This function handles notification sending gracefully - failures
    are logged but do not raise exceptions.

    Args:
        schema_change: SchemaChange object with change details.
        policy: The policy that was applied.
        config: Main configuration with notification settings.
        logger: Logger instance.
    """
    from mysql_to_sheets.core.notifications import (
        NotificationPayload,
        get_notification_manager,
    )

    notification_config = _get_notification_config(config)

    # Check if any notification is configured
    manager = get_notification_manager()
    configured_backends = manager.get_configured_backends(notification_config)
    if not configured_backends:
        logger.debug("No notification backends configured, skipping schema change notification")
        return

    # Build notification payload with schema change info
    message_parts = [f"Schema change detected (policy: {policy})"]
    if schema_change.added_columns:
        message_parts.append(f"Added columns: {schema_change.added_columns}")
    if schema_change.removed_columns:
        message_parts.append(f"Removed columns: {schema_change.removed_columns}")
    if schema_change.reordered:
        message_parts.append("Column order changed")

    payload = NotificationPayload(
        success=True,
        rows_synced=0,
        sheet_id=config.google_sheet_id,
        worksheet=config.google_worksheet_name,
        message=" | ".join(message_parts),
        error=None,
        duration_ms=0.0,
        dry_run=False,
        headers=[],
        source="schema_change",
        schema_change=schema_change.to_dict(),
    )

    # Send notification (failures are logged, not raised)
    try:
        results = manager.send_notification(payload, notification_config)
        if results["sent"]:
            logger.info(f"Schema change notifications sent via: {', '.join(results['sent'])}")
        if results["failed"]:
            logger.warning(f"Schema change notification failures: {results['errors']}")
    except (OSError, RuntimeError, KeyError) as e:
        logger.warning(f"Failed to send schema change notifications: {e}")


def _log_audit_event(
    event: str,
    organization_id: int,
    config: Config,
    logger: logging.Logger,
    sync_id: str | None = None,
    config_name: str | None = None,
    rows_synced: int | None = None,
    query: str | None = None,
    error: str | None = None,
    duration_seconds: float = 0.0,
    source: str = "sync",
) -> None:
    """Log an audit event for sync operations.

    This function handles audit logging gracefully - failures
    are logged but do not raise exceptions.

    Args:
        event: Audit event type (started, completed, failed).
        organization_id: Organization ID for scoping.
        config: Main configuration.
        logger: Logger instance.
        sync_id: Unique sync operation ID.
        config_name: Name of the sync configuration.
        rows_synced: Number of rows synced.
        query: SQL query that was executed.
        error: Error message if failed.
        duration_seconds: Sync duration in seconds.
        source: Source of the sync (cli, api, web, scheduler).
    """
    try:
        from mysql_to_sheets.core.audit import log_sync_event

        log_sync_event(
            event=event,
            organization_id=organization_id,
            db_path=config.tenant_db_path,
            sync_id=sync_id,
            config_name=config_name,
            rows_synced=rows_synced,
            query=query,
            error=error,
            duration_seconds=duration_seconds,
            source=source,
        )
    except (OSError, RuntimeError, ImportError) as e:
        logger.debug(f"Audit logging skipped or failed: {e}")


def _trigger_webhook(
    event: str,
    organization_id: int,
    config: Config,
    logger: logging.Logger,
    result: SyncResult | None = None,
    sync_id: str | None = None,
    config_name: str | None = None,
    duration_seconds: float = 0.0,
    source: str = "sync",
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    """Trigger a webhook for a sync event.

    This function handles webhook delivery gracefully - failures
    are logged but do not raise exceptions.

    Args:
        event: Webhook event type (sync.started, sync.completed, sync.failed).
        organization_id: Organization ID for scoping.
        config: Main configuration.
        logger: Logger instance.
        result: Optional sync result (for completed/failed events).
        sync_id: Unique sync operation ID.
        config_name: Name of the sync configuration.
        duration_seconds: Sync duration in seconds.
        source: Source of the sync (cli, api, web, scheduler).
        error_type: Type of error (for failed events).
        error_message: Error message (for failed events).
    """
    try:
        from mysql_to_sheets.core.webhooks.delivery import get_webhook_delivery_service
        from mysql_to_sheets.core.webhooks.payload import create_sync_payload

        rows_synced = result.rows_synced if result else 0
        sheet_url = (
            f"https://docs.google.com/spreadsheets/d/{config.google_sheet_id}"
            if config.google_sheet_id
            else None
        )

        payload = create_sync_payload(
            event=event,
            sync_id=sync_id,
            config_name=config_name,
            rows_synced=rows_synced,
            duration_seconds=duration_seconds,
            sheet_id=config.google_sheet_id,
            sheet_url=sheet_url,
            triggered_by=source,
            error_type=error_type,
            error_message=error_message,
        )

        delivery_service = get_webhook_delivery_service(config.tenant_db_path)
        results = delivery_service.deliver_to_all(event, organization_id, payload)

        if results:
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            if successful > 0:
                logger.debug(f"Webhook '{event}' delivered to {successful} subscriptions")
            if failed > 0:
                logger.warning(f"Webhook '{event}' failed for {failed} subscriptions")

    except (OSError, RuntimeError, ImportError) as e:
        logger.debug(f"Webhook delivery skipped or failed: {e}")


def _create_pre_sync_snapshot(
    config: Config,
    organization_id: int,
    sync_config_id: int | None,
    logger: logging.Logger,
) -> None:
    """Create a snapshot of the current sheet state before sync.

    This function handles snapshot creation gracefully - failures
    are logged but do not raise exceptions or block the sync.

    Args:
        config: Main configuration.
        organization_id: Organization ID for scoping.
        sync_config_id: Optional sync config ID.
        logger: Logger instance.
    """
    try:
        from mysql_to_sheets.core.snapshot_retention import (
            RetentionConfig,
            cleanup_old_snapshots,
            should_create_snapshot,
        )
        from mysql_to_sheets.core.snapshots import create_snapshot, estimate_sheet_size

        # Check size limit before creating snapshot
        retention_config = RetentionConfig(
            retention_count=config.snapshot_retention_count,
            retention_days=config.snapshot_retention_days,
            max_size_mb=config.snapshot_max_size_mb,
        )

        try:
            estimated_size = estimate_sheet_size(config, logger)
            should_create, reason = should_create_snapshot(estimated_size, retention_config, logger)
            if not should_create:
                logger.info(f"Skipping snapshot: {reason}")
                return
        except (OSError, ValueError) as size_error:
            # If we can't estimate size, try to create snapshot anyway
            logger.debug(f"Could not estimate sheet size: {size_error}")

        # Create the snapshot
        snapshot = create_snapshot(
            config=config,
            organization_id=organization_id,
            db_path=config.tenant_db_path,
            sync_config_id=sync_config_id,
            logger=logger,
        )
        logger.info(f"Pre-sync snapshot created: ID {snapshot.id}")

        # Run cleanup to enforce retention limits
        cleanup_old_snapshots(
            organization_id=organization_id,
            db_path=config.tenant_db_path,
            retention_config=retention_config,
            logger=logger,
        )

    except (OSError, RuntimeError, ImportError) as e:
        logger.warning(f"Failed to create pre-sync snapshot: {e}")


def run_sync(
    config: Config | None = None,
    logger: logging.Logger | None = None,
    dry_run: bool = False,
    preview: bool = False,
    mode: str | None = None,
    chunk_size: int | None = None,
    incremental_config: IncrementalConfig | None = None,
    column_mapping_config: ColumnMappingConfig | None = None,
    notify: bool | None = None,
    source: str = "sync",
    organization_id: int | None = None,
    config_name: str | None = None,
    sync_id: str | None = None,
    config_id: int | None = None,
    skip_snapshot: bool = False,
    create_worksheet: bool | None = None,
    atomic: bool = True,
    preserve_gid: bool = False,
    schema_policy: str | None = None,
    expected_headers: list[str] | None = None,
    pii_config: "PIITransformConfig | None" = None,
    pii_acknowledged: bool = False,
    detect_pii: bool | None = None,
    resumable: bool = False,
    job_id: int | None = None,
) -> SyncResult:
    """Execute the full sync operation.

    Args:
        config: Configuration object. If None, loads from environment.
        logger: Logger instance. If None, creates one from config.
        dry_run: If True, fetch and validate but don't push to Sheets.
        preview: If True, show diff with current sheet data without pushing.
        mode: Sync mode ('replace', 'append', 'streaming'). Defaults to config.
        chunk_size: Chunk size for streaming mode. Defaults to config.
        incremental_config: Optional incremental sync configuration.
        column_mapping_config: Optional column mapping configuration.
        notify: Whether to send notifications. If None, uses config settings.
        source: Source of the sync (cli, api, web, scheduler).
        organization_id: Optional organization ID for webhook delivery.
        config_name: Optional config name for webhook payloads.
        sync_id: Optional unique sync ID for webhook payloads.
        config_id: Optional sync config ID for freshness tracking.
        atomic: If True (default), streaming mode uses atomic staging for
            transactional consistency. Set to False for legacy direct-write.
        preserve_gid: If True, preserve worksheet GID during atomic swap.
            Only applies when atomic=True and mode='streaming'.
        skip_snapshot: If True, skip creating a pre-sync snapshot.
        create_worksheet: If True, create the worksheet if it doesn't exist.
            If None, uses config.worksheet_auto_create.
        schema_policy: Schema evolution policy ('strict', 'additive', 'flexible',
            'notify_only'). Defaults to 'strict' for FREE tier.
        expected_headers: Expected column headers from previous sync. If None,
            schema comparison is skipped (first sync).
        pii_config: Optional PII transform configuration. If None, uses config
            defaults or environment variables.
        pii_acknowledged: If True, acknowledges detected PII and proceeds without
            requiring transforms.
        detect_pii: Override PII detection setting. If None, uses config default.
        resumable: If True, enable checkpoint/resume for streaming syncs.
            Preserves staging worksheet on failure for later resume.
        job_id: Optional job ID for checkpoint tracking (resumable streaming).

    Returns:
        SyncResult with operation status and statistics.

    Raises:
        ConfigError: If configuration is invalid.
        DatabaseError: If database operations fail.
        SheetsError: If Google Sheets operations fail.
    """
    import secrets
    import time

    start_time = time.time()

    # Generate sync ID if not provided
    if sync_id is None:
        sync_id = f"sync_{secrets.token_hex(8)}"

    # Load config if not provided
    if config is None:
        config = get_config()

    # Setup logging if not provided
    if logger is None:
        logger = setup_logging(config)

    # Use config defaults if not overridden
    sync_mode = mode or config.sync_mode
    sync_chunk_size = chunk_size or config.sync_chunk_size

    # Use config defaults for atomic streaming settings
    # These can be overridden via function parameters
    if atomic is True:  # If using default True, check config
        atomic = getattr(config, "streaming_atomic_enabled", True)
    if preserve_gid is False:  # If using default False, check config
        preserve_gid = getattr(config, "streaming_preserve_gid", False)

    db_type = config.db_type.lower()
    logger.info(f"Starting {db_type.upper()} to Google Sheets sync (mode={sync_mode})")

    # Track result for notification
    result: SyncResult | None = None
    error_result: SyncResult | None = None

    try:
        # Validate configuration
        config.validate_or_raise()
        logger.debug(f"Configuration loaded: {config}")

        # Log sync.started audit event and trigger webhook (only for real syncs)
        if organization_id and not dry_run and not preview:
            _log_audit_event(
                event="started",
                organization_id=organization_id,
                config=config,
                logger=logger,
                sync_id=sync_id,
                config_name=config_name,
                query=config.sql_query,
                source=source,
            )
            _trigger_webhook(
                event="sync.started",
                organization_id=organization_id,
                config=config,
                logger=logger,
                sync_id=sync_id,
                config_name=config_name,
                source=source,
            )

        # Create pre-sync snapshot if enabled
        if (
            organization_id
            and not dry_run
            and not preview
            and not skip_snapshot
            and config.snapshot_enabled
        ):
            _create_pre_sync_snapshot(
                config=config,
                organization_id=organization_id,
                sync_config_id=config_id,
                logger=logger,
            )

        # Handle streaming mode separately
        if sync_mode == "streaming":
            # Warn if column mapping is configured but will be ignored
            col_mapping = column_mapping_config or _build_column_mapping_config(config)
            if col_mapping.is_active():
                logger.warning(
                    "Column mapping is configured but will be ignored in streaming mode. "
                    "Use 'replace' or 'append' mode to apply column transformations."
                )

            from mysql_to_sheets.core.streaming import StreamingConfig, run_streaming_sync

            streaming_config = StreamingConfig(chunk_size=sync_chunk_size)
            streaming_result = run_streaming_sync(
                config,
                streaming_config=streaming_config,
                logger_instance=logger,
                dry_run=dry_run,
                atomic=atomic,
                preserve_gid=preserve_gid,
                resumable=resumable,
                job_id=job_id,
                config_id=config_id,
            )

            result = SyncResult(
                success=streaming_result.success,
                rows_synced=streaming_result.total_rows,
                columns=0,  # Not tracked in streaming mode
                headers=[],  # Not returned in streaming mode
                message=f"Streamed {streaming_result.total_rows} rows in {streaming_result.total_chunks} chunks",
                error=None
                if streaming_result.success
                else f"{streaming_result.failed_chunks} chunks failed",
            )
            return result

        # Regular sync modes (replace, append)
        # Fetch data from database
        headers, rows = fetch_data(config, logger, incremental_config)

        if not rows:
            logger.warning("No data returned from query")
            empty_action = getattr(config, "sync_empty_result_action", "warn") or "warn"
            if empty_action == "error":
                raise SyncError(
                    message="Query returned no rows; aborting to protect sheet data",
                    code="CONFIG_106",
                )
            if empty_action == "clear" and not dry_run and sync_mode == "replace":
                # Explicitly requested: push headers to clear old data
                push_to_sheets(
                    config, headers, [], logger, mode=sync_mode, create_worksheet=create_worksheet
                )
            elif empty_action == "warn":
                logger.warning(
                    "Empty result set in replace mode — skipping sheet update "
                    "to prevent data loss. Set SYNC_EMPTY_RESULT_ACTION=clear to allow."
                )
            result = SyncResult(
                success=True,
                rows_synced=0,
                columns=len(headers),
                headers=headers,
                message="Sync completed (empty dataset)",
            )
            return result

        # Clean data for Google Sheets compatibility
        cleaned_rows = clean_data(rows, logger, db_type=db_type)

        # PII Detection and Transformation
        # Runs after clean_data() but before column mapping to ensure
        # transforms are applied to the original column names
        pii_detection_result = None
        should_detect_pii = detect_pii if detect_pii is not None else getattr(
            config, "pii_detect_enabled", False
        )

        if should_detect_pii or (pii_config and pii_config.is_active()):
            from mysql_to_sheets.core.exceptions import PIIAcknowledgmentRequired
            from mysql_to_sheets.core.pii import PIITransformConfig
            from mysql_to_sheets.core.pii_detection import detect_pii_in_columns
            from mysql_to_sheets.core.pii_transform import apply_pii_transforms

            # Build PII config from settings if not provided
            if pii_config is None:
                pii_config = PIITransformConfig(
                    enabled=True,
                    auto_detect=should_detect_pii,
                    confidence_threshold=getattr(config, "pii_confidence_threshold", 0.7),
                    sample_size=getattr(config, "pii_sample_size", 100),
                )

            # Detect PII in columns
            if pii_config.auto_detect:
                pii_detection_result = detect_pii_in_columns(
                    headers, cleaned_rows, pii_config, logger
                )

                if pii_detection_result.has_pii:
                    logger.info(pii_detection_result.summary())

                    # Check if acknowledgment is required
                    if pii_detection_result.requires_acknowledgment and not pii_acknowledged:
                        # Check for explicit transforms for all detected columns
                        unhandled_columns = [
                            col.column_name
                            for col in pii_detection_result.columns
                            if (
                                pii_config.get_transform_for_column(col.column_name) is None
                                and not pii_config.is_acknowledged(col.column_name)
                            )
                        ]

                        if unhandled_columns:
                            raise PIIAcknowledgmentRequired(pii_result=pii_detection_result)

            # Apply PII transforms
            if pii_config.is_active():
                headers, cleaned_rows = apply_pii_transforms(
                    headers, cleaned_rows, pii_config, pii_detection_result, logger
                )

        # Apply column mapping if configured
        col_mapping = column_mapping_config or _build_column_mapping_config(config)
        if col_mapping.is_active():
            logger.info("Applying column mapping transformations")
            headers, cleaned_rows = apply_column_mapping(headers, cleaned_rows, col_mapping)
            logger.debug(f"Column mapping result: {len(headers)} columns")

        # Check for schema changes if expected_headers is provided
        schema_change_info: dict[str, Any] | None = None
        if schema_policy is not None or expected_headers is not None:
            from mysql_to_sheets.core.schema_evolution import (
                SchemaChangeError,
                SchemaPolicy,
                apply_schema_policy,
                detect_schema_change,
                get_policy_tier_requirement,
            )
            from mysql_to_sheets.core.tier import Tier, check_feature_access, get_tier_from_license

            # Default to strict policy
            policy = schema_policy or "strict"
            policy_enum = SchemaPolicy.from_string(policy)

            # Check tier access for non-strict policies
            feature_key = get_policy_tier_requirement(policy_enum)
            if feature_key is not None:
                current_tier = get_tier_from_license()
                if not check_feature_access(current_tier, feature_key):
                    logger.warning(
                        f"Schema policy '{policy}' requires PRO tier or higher. "
                        f"Current tier: {current_tier.value}. Using 'strict' policy."
                    )
                    policy = "strict"
                    policy_enum = SchemaPolicy.STRICT

            # Detect schema changes
            schema_change = detect_schema_change(expected_headers, headers)

            if schema_change.has_changes:
                logger.info(f"Schema change detected: {schema_change.summary()}")

                try:
                    # Apply policy (may raise SchemaChangeError)
                    headers, cleaned_rows, should_notify = apply_schema_policy(
                        schema_change, policy_enum, headers, cleaned_rows
                    )

                    # Record schema change info for result
                    schema_change_info = schema_change.to_dict()
                    schema_change_info["policy_applied"] = policy

                    # Send schema change notification if appropriate
                    if should_notify and notify is not False:
                        _send_schema_change_notification(
                            schema_change=schema_change,
                            policy=policy,
                            config=config,
                            logger=logger,
                        )

                except SchemaChangeError:
                    # Re-raise to be handled by the main exception handler
                    raise

        # Preview mode - compute diff without pushing
        if preview:
            logger.info(f"Preview mode: comparing {len(cleaned_rows)} rows with current sheet")
            diff = run_preview(config, headers, cleaned_rows, logger)
            result = SyncResult(
                success=True,
                rows_synced=len(cleaned_rows),
                columns=len(headers),
                headers=headers,
                message=f"Preview: {diff.summary()}",
                preview=True,
                diff=diff,
            )
            return result

        # Dry run - validate without pushing or comparing
        if dry_run:
            logger.info(f"Dry run: would push {len(cleaned_rows)} rows to sheet (mode={sync_mode})")
            result = SyncResult(
                success=True,
                rows_synced=len(cleaned_rows),
                columns=len(headers),
                headers=headers,
                message=f"Dry run: validated {len(cleaned_rows)} rows",
            )
            return result

        # Push to Google Sheets
        push_to_sheets(
            config, headers, cleaned_rows, logger, mode=sync_mode, create_worksheet=create_worksheet
        )

        logger.info(
            f"Sync completed successfully: {len(cleaned_rows)} rows pushed (mode={sync_mode})"
        )

        result = SyncResult(
            success=True,
            rows_synced=len(cleaned_rows),
            columns=len(headers),
            headers=headers,
            message=f"Successfully synced {len(cleaned_rows)} rows",
            schema_changes=schema_change_info,
        )
        return result

    except SyncError as e:
        error_result = SyncResult(
            success=False,
            rows_synced=0,
            message=str(e),
            error=str(e),
        )
        raise
    except (OSError, ValueError, TypeError, RuntimeError, KeyError) as e:
        # Wrap non-SyncError exceptions to preserve the error code system
        error_result = SyncResult(
            success=False,
            rows_synced=0,
            message=str(e),
            error=str(e),
        )
        raise SyncError(
            message=f"Unexpected error during sync: {e}",
            details={"original_exception": type(e).__name__},
        ) from e

    finally:
        # Send notification if enabled
        duration_ms = (time.time() - start_time) * 1000
        duration_seconds = duration_ms / 1000
        final_result = result or error_result

        if final_result and notify is not False:
            # notify=None means use config, notify=True means force, notify=False means skip
            _send_notification(
                final_result,
                config,
                logger,
                dry_run=dry_run,
                source=source,
                duration_ms=duration_ms,
            )

        # Log audit event and trigger webhook (only for real syncs)
        if organization_id and final_result and not dry_run and not preview:
            if final_result.success:
                _log_audit_event(
                    event="completed",
                    organization_id=organization_id,
                    config=config,
                    logger=logger,
                    sync_id=sync_id,
                    config_name=config_name,
                    rows_synced=final_result.rows_synced,
                    query=config.sql_query,
                    duration_seconds=duration_seconds,
                    source=source,
                )
                _trigger_webhook(
                    event="sync.completed",
                    organization_id=organization_id,
                    config=config,
                    logger=logger,
                    result=final_result,
                    sync_id=sync_id,
                    config_name=config_name,
                    duration_seconds=duration_seconds,
                    source=source,
                )
            else:
                error_type = (
                    type(error_result.error).__name__
                    if error_result and error_result.error
                    else "SyncError"
                )
                _log_audit_event(
                    event="failed",
                    organization_id=organization_id,
                    config=config,
                    logger=logger,
                    sync_id=sync_id,
                    config_name=config_name,
                    query=config.sql_query,
                    error=final_result.error,
                    duration_seconds=duration_seconds,
                    source=source,
                )
                _trigger_webhook(
                    event="sync.failed",
                    organization_id=organization_id,
                    config=config,
                    logger=logger,
                    result=final_result,
                    sync_id=sync_id,
                    config_name=config_name,
                    duration_seconds=duration_seconds,
                    source=source,
                    error_type=error_type,
                    error_message=final_result.error,
                )

        # Update freshness tracking (only for real syncs with config_id)
        if config_id and organization_id and final_result and not dry_run and not preview:
            try:
                from mysql_to_sheets.core.freshness import update_freshness

                update_freshness(
                    config_id=config_id,
                    organization_id=organization_id,
                    success=final_result.success,
                    row_count=final_result.rows_synced if final_result.success else None,
                    db_path=config.tenant_db_path,
                )
            except (OSError, RuntimeError, ImportError) as freshness_error:
                logger.debug(f"Freshness update failed: {freshness_error}")

        # Record usage for billing (only for successful syncs with organization_id)
        if (
            organization_id
            and final_result
            and final_result.success
            and not dry_run
            and not preview
        ):
            try:
                from mysql_to_sheets.core.usage_tracking import record_sync_usage

                record_sync_usage(
                    organization_id=organization_id,
                    rows_synced=final_result.rows_synced,
                    db_path=config.tenant_db_path,
                )
            except (OSError, RuntimeError, ImportError) as usage_error:
                logger.debug(f"Usage tracking failed: {usage_error}")


class SyncService:
    """Service class for sync operations with reusable configuration.

    This class provides a stateful interface for sync operations,
    useful for API and web contexts where the same configuration
    may be used multiple times.

    Attributes:
        config: Configuration object.
        logger: Logger instance.
    """

    def __init__(
        self,
        config: Config | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize SyncService.

        Args:
            config: Configuration object. If None, loads from environment.
            logger: Logger instance. If None, creates one from config.
        """
        self.config = config or get_config()
        self.logger = logger or setup_logging(self.config)

    def sync(self, dry_run: bool = False) -> SyncResult:
        """Execute sync with current configuration.

        Args:
            dry_run: If True, validate without pushing to Sheets.

        Returns:
            SyncResult with operation status.
        """
        return run_sync(self.config, self.logger, dry_run=dry_run)

    def sync_with_overrides(
        self,
        dry_run: bool = False,
        **overrides: Any,
    ) -> SyncResult:
        """Execute sync with configuration overrides.

        Args:
            dry_run: If True, validate without pushing to Sheets.
            **overrides: Configuration fields to override.

        Returns:
            SyncResult with operation status.
        """
        config = self.config.with_overrides(**overrides)
        return run_sync(config, self.logger, dry_run=dry_run)

    def validate_config(self) -> list[str]:
        """Validate current configuration.

        Returns:
            List of validation errors (empty if valid).
        """
        return self.config.validate()

    def test_database_connection(self) -> bool:
        """Test database connectivity.

        Supports both MySQL and PostgreSQL databases based on config.db_type.

        Returns:
            True if connection successful.

        Raises:
            DatabaseError: If connection fails.
        """
        db_type = self.config.db_type.upper()
        self.logger.info(f"Testing {db_type} database connection...")

        db_config = _build_database_config(self.config)
        conn = get_connection(db_config)

        try:
            result = conn.test_connection()
            self.logger.info(f"{db_type} database connection successful")
            return result
        except DatabaseError:
            raise

    def test_sheets_connection(self) -> bool:
        """Test Google Sheets connectivity.

        Returns:
            True if connection successful.

        Raises:
            SheetsError: If connection fails.
        """
        from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier

        self.logger.info("Testing Google Sheets connection...")
        try:
            gc = gspread.service_account(filename=self.config.service_account_file)  # type: ignore[attr-defined]
            spreadsheet = gc.open_by_key(self.config.google_sheet_id)

            # Resolve worksheet name from GID URL if needed
            try:
                worksheet_name = parse_worksheet_identifier(
                    self.config.google_worksheet_name,
                    spreadsheet=spreadsheet,
                )
            except ValueError as e:
                raise SheetsError(
                    message=str(e),
                    sheet_id=self.config.google_sheet_id,
                    worksheet_name=self.config.google_worksheet_name,
                ) from e

            _ = spreadsheet.worksheet(worksheet_name)
            self.logger.info("Google Sheets connection successful")
            return True
        except gspread.exceptions.SpreadsheetNotFound as e:
            raise SheetsError(
                message="Spreadsheet not found",
                sheet_id=self.config.google_sheet_id,
                original_error=e,
            ) from e
        except gspread.exceptions.WorksheetNotFound as e:
            raise SheetsError(
                message=f"Worksheet '{self.config.google_worksheet_name}' not found",
                sheet_id=self.config.google_sheet_id,
                worksheet_name=self.config.google_worksheet_name,
                original_error=e,
            ) from e
        except gspread.exceptions.APIError as e:
            # EC-39: Check for API-not-enabled error
            api_not_enabled_msg = detect_sheets_api_not_enabled(e)
            if api_not_enabled_msg:
                self.logger.error(api_not_enabled_msg)
                raise SheetsError(
                    message=api_not_enabled_msg,
                    sheet_id=self.config.google_sheet_id,
                    original_error=e,
                    code=ErrorCode.SHEETS_API_NOT_ENABLED,
                ) from e
            raise SheetsError(
                message=f"Google Sheets API error: {e}",
                sheet_id=self.config.google_sheet_id,
                original_error=e,
            ) from e
        except (OSError, gspread.exceptions.GSpreadException) as e:
            raise SheetsError(
                message=f"Google Sheets connection failed: {e}",
                sheet_id=self.config.google_sheet_id,
                original_error=e,
            ) from e
