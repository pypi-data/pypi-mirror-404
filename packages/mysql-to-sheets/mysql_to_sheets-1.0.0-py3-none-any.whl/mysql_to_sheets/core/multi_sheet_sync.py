"""Multi-sheet sync logic.

This module provides functionality to sync data from a single database query
to multiple Google Sheets simultaneously. Supports:
- Multiple sheet targets from one query
- Per-target column filtering
- Per-target row filtering
- Parallel or sequential execution

Example:
    >>> from mysql_to_sheets.core.multi_sheet_sync import run_multi_sheet_sync
    >>> from mysql_to_sheets.core.config import SheetTarget
    >>>
    >>> targets = [
    ...     SheetTarget(sheet_id="abc123", worksheet_name="All Data"),
    ...     SheetTarget(
    ...         sheet_id="def456",
    ...         worksheet_name="Active Only",
    ...         column_filter=["name", "email"],
    ...         row_filter="status == 'active'",
    ...     ),
    ... ]
    >>> result = run_multi_sheet_sync(targets=targets)
"""

import ast
import contextvars
import logging
import operator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

import gspread

from mysql_to_sheets.core.column_mapping import apply_column_mapping
from mysql_to_sheets.core.config import Config, SheetTarget, get_config
from mysql_to_sheets.core.exceptions import ConfigError, SyncError
from mysql_to_sheets.core.sync import (
    _build_column_mapping_config,
    clean_data,
    fetch_data,
    setup_logging,
    validate_batch_size,
)


@dataclass
class TargetSyncResult:
    """Result of syncing to a single target sheet.

    Attributes:
        target: The SheetTarget that was synced.
        success: Whether the sync completed successfully.
        rows_synced: Number of rows synced to this target.
        message: Human-readable status message.
        error: Error details if sync failed.
    """

    target: SheetTarget
    success: bool
    rows_synced: int = 0
    message: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target": self.target.to_dict(),
            "success": self.success,
            "rows_synced": self.rows_synced,
            "message": self.message,
            "error": self.error,
        }


@dataclass
class MultiSheetSyncResult:
    """Result of a multi-sheet sync operation.

    Attributes:
        success: Whether all targets synced successfully.
        total_rows_fetched: Number of rows fetched from database.
        target_results: Results for each target sheet.
        message: Human-readable status message.
        error: Error details if sync failed.
    """

    success: bool
    total_rows_fetched: int = 0
    target_results: list[TargetSyncResult] = field(default_factory=list)
    message: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "total_rows_fetched": self.total_rows_fetched,
            "target_results": [r.to_dict() for r in self.target_results],
            "targets_succeeded": sum(1 for r in self.target_results if r.success),
            "targets_failed": sum(1 for r in self.target_results if not r.success),
            "message": self.message,
            "error": self.error,
        }


def validate_targets_unique(targets: list[SheetTarget]) -> None:
    """Validate that no two targets point to the same sheet + worksheet.

    When running in parallel mode, duplicate targets would race to write data,
    resulting in unpredictable final state and potential data corruption.

    Args:
        targets: List of SheetTarget configurations.

    Raises:
        ConfigError: If duplicate targets are detected.
    """
    if not targets:
        return

    seen: dict[tuple[str, str], int] = {}  # (sheet_id, worksheet_name) -> first index
    duplicates: list[str] = []

    for idx, target in enumerate(targets):
        key = (target.sheet_id, target.worksheet_name)
        if key in seen:
            first_idx = seen[key]
            duplicates.append(
                f"targets[{first_idx}] and targets[{idx}] both point to "
                f"sheet '{target.sheet_id}' / worksheet '{target.worksheet_name}'"
            )
        else:
            seen[key] = idx

    if duplicates:
        raise ConfigError(
            message=(
                f"Duplicate targets detected: {'; '.join(duplicates)}. "
                f"Each sheet/worksheet combination must be unique to avoid race conditions "
                f"in parallel execution mode."
            ),
            code="CONFIG_108",
        )


def filter_columns(
    headers: list[str],
    rows: list[list[Any]],
    column_filter: list[str],
) -> tuple[list[str], list[list[Any]]]:
    """Filter data to include only specified columns.

    Args:
        headers: Original column headers.
        rows: Original data rows.
        column_filter: List of column names to include.

    Returns:
        Tuple of (filtered_headers, filtered_rows).
    """
    # Find indices of columns to keep
    indices = []
    filtered_headers = []
    for col in column_filter:
        if col in headers:
            indices.append(headers.index(col))
            filtered_headers.append(col)

    # Filter rows
    filtered_rows = []
    for row in rows:
        filtered_row = [row[i] for i in indices if i < len(row)]
        filtered_rows.append(filtered_row)

    return filtered_headers, filtered_rows


# Allowed AST node types for safe expression evaluation
_SAFE_COMPARE_OPS: dict[type, Any] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

_SAFE_BOOL_OPS: dict[type, Any] = {
    ast.And: all,
    ast.Or: any,
}

_SAFE_UNARY_OPS: dict[type, Any] = {
    ast.Not: operator.not_,
    ast.USub: operator.neg,
}

_SAFE_BUILTINS: dict[str, Any] = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "None": None,
    "True": True,
    "False": False,
}


def _safe_eval(expr: str, context: dict[str, Any]) -> Any:
    """Evaluate a filter expression safely using AST walking.

    Only allows comparisons, boolean ops, literals, and name lookups
    against the provided context. No attribute access, calls (except
    whitelisted builtins), or arbitrary code execution.

    Args:
        expr: Filter expression string.
        context: Variable name to value mapping.

    Returns:
        Evaluation result.

    Raises:
        ValueError: If expression contains disallowed operations.
    """
    tree = ast.parse(expr, mode="eval")
    return _eval_node(tree.body, context)


def _eval_node(node: ast.expr, ctx: dict[str, Any]) -> Any:
    """Recursively evaluate an AST node against a context."""
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if node.id in _SAFE_BUILTINS:
            return _SAFE_BUILTINS[node.id]
        if node.id in ctx:
            return ctx[node.id]
        raise ValueError(f"Unknown name: {node.id!r}")

    if isinstance(node, ast.List):
        return [_eval_node(e, ctx) for e in node.elts]

    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(e, ctx) for e in node.elts)

    if isinstance(node, ast.Set):
        return {_eval_node(e, ctx) for e in node.elts}

    if isinstance(node, ast.UnaryOp):
        op_fn = _SAFE_UNARY_OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported unary op: {type(node.op).__name__}")
        return op_fn(_eval_node(node.operand, ctx))

    if isinstance(node, ast.BoolOp):
        fn = _SAFE_BOOL_OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"Unsupported bool op: {type(node.op).__name__}")
        values = [_eval_node(v, ctx) for v in node.values]
        return fn(values)

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, ctx)
        for op, comparator in zip(node.ops, node.comparators):
            op_fn = _SAFE_COMPARE_OPS.get(type(op))
            if op_fn is None:
                raise ValueError(f"Unsupported compare op: {type(op).__name__}")
            right = _eval_node(comparator, ctx)
            if not op_fn(left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.Call):
        func = _eval_node(node.func, ctx)
        if func not in (len, str, int, float):
            raise ValueError(f"Function calls not allowed: {ast.dump(node)}")
        args = [_eval_node(a, ctx) for a in node.args]
        return func(*args)

    raise ValueError(f"Unsupported expression: {type(node).__name__}")


def _extract_column_names(filter_expr: str) -> set[str]:
    """Extract all column name references from a filter expression.

    Args:
        filter_expr: Filter expression like "status == 'active' and age > 18".

    Returns:
        Set of column names referenced in the expression.

    Raises:
        ValueError: If expression cannot be parsed.
    """
    try:
        tree = ast.parse(filter_expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid filter syntax: {e}") from e

    names: set[str] = set()

    class NameVisitor(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:
            # Skip Python built-in constants
            if node.id not in ("True", "False", "None"):
                names.add(node.id)
            self.generic_visit(node)

    NameVisitor().visit(tree)
    return names


def validate_row_filter_columns(
    filter_expr: str,
    available_headers: list[str],
) -> list[str]:
    """Validate that all columns referenced in a filter exist in available headers.

    Args:
        filter_expr: Filter expression to validate.
        available_headers: List of available column names.

    Returns:
        List of missing column names (empty if all present).
    """
    if not filter_expr:
        return []

    try:
        referenced = _extract_column_names(filter_expr)
    except ValueError:
        # Can't parse expression - will fail at evaluation time
        return []

    available_set = set(available_headers)
    missing = [col for col in referenced if col not in available_set]
    return missing


def evaluate_row_filter(row: list[Any], headers: list[str], filter_expr: str) -> bool:
    """Evaluate a row filter expression.

    Supports simple expressions like:
    - "column_name == 'value'"
    - "column_name != 'value'"
    - "column_name > 100"
    - "column_name in ['a', 'b', 'c']"
    - "column_name is not None"

    Args:
        row: Data row to evaluate.
        headers: Column headers for name-to-index mapping.
        filter_expr: Filter expression.

    Returns:
        True if row passes filter, False otherwise.
    """
    if not filter_expr:
        return True

    # Build a context dict with column values
    context = dict(zip(headers, row))

    try:
        result = _safe_eval(filter_expr, context)
        return bool(result)
    except (ValueError, TypeError, KeyError, SyntaxError):
        # If evaluation fails, include the row by default
        return True


def filter_rows(
    headers: list[str],
    rows: list[list[Any]],
    row_filter: str,
    logger: logging.Logger | None = None,
    strict: bool = True,
) -> list[list[Any]]:
    """Filter rows based on an expression.

    Args:
        headers: Column headers.
        rows: Data rows.
        row_filter: Filter expression.
        logger: Optional logger for warnings.
        strict: If True, raise error for missing columns. If False, log warning.

    Returns:
        Filtered list of rows.

    Raises:
        ConfigError: If strict=True and filter references missing columns.
    """
    if not row_filter:
        return rows

    # Validate that all referenced columns exist
    missing_columns = validate_row_filter_columns(row_filter, headers)
    if missing_columns:
        from mysql_to_sheets.core.exceptions import ConfigError

        msg = (
            f"Row filter references missing columns: {sorted(missing_columns)}. "
            f"Available columns: {headers}. "
            f"This may occur if a column_filter removed the columns before row filtering."
        )
        if strict:
            raise ConfigError(message=msg, code="CONFIG_109")
        elif logger:
            logger.warning(f"{msg} Filter will be skipped.")
            return rows

    return [row for row in rows if evaluate_row_filter(row, headers, row_filter)]


def push_to_target(
    target: SheetTarget,
    headers: list[str],
    rows: list[list[Any]],
    service_account_file: str,
    logger: logging.Logger | None = None,
) -> TargetSyncResult:
    """Push data to a single target sheet.

    Args:
        target: Target sheet configuration.
        headers: Column headers.
        rows: Data rows.
        service_account_file: Path to service account JSON.
        logger: Optional logger instance.

    Returns:
        TargetSyncResult with operation status.
    """
    try:
        # Apply column filter if specified
        filtered_headers = headers
        filtered_rows = rows

        if target.column_filter:
            filtered_headers, filtered_rows = filter_columns(headers, rows, target.column_filter)
            if logger:
                logger.debug(
                    f"Filtered columns for target {target.sheet_id}: "
                    f"{len(headers)} -> {len(filtered_headers)}"
                )

        # Apply row filter if specified
        if target.row_filter:
            filtered_rows = filter_rows(
                filtered_headers, filtered_rows, target.row_filter, logger=logger
            )
            if logger:
                logger.debug(
                    f"Filtered rows for target {target.sheet_id}: "
                    f"{len(rows)} -> {len(filtered_rows)}"
                )

        # Connect to Google Sheets
        from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier

        gc = gspread.service_account(filename=service_account_file)  # type: ignore[attr-defined]
        spreadsheet = gc.open_by_key(target.sheet_id)

        # Resolve worksheet name from GID URL if needed
        try:
            worksheet_name = parse_worksheet_identifier(
                target.worksheet_name,
                spreadsheet=spreadsheet,
            )
        except ValueError as e:
            return TargetSyncResult(
                target=target,
                success=False,
                error=str(e),
            )

        worksheet = spreadsheet.worksheet(worksheet_name)

        if logger:
            logger.info(f"Pushing {len(filtered_rows)} rows to {target.sheet_id}/{worksheet_name}")

        # Push data based on mode
        if target.mode == "replace":
            worksheet.clear()
            all_data = [filtered_headers] + filtered_rows
            worksheet.update(
                values=all_data,
                range_name="A1",
                value_input_option="USER_ENTERED",  # type: ignore[arg-type]
            )
        elif target.mode == "append":
            # Check existing headers for validation (consistent with single-sheet sync)
            existing_headers = worksheet.row_values(1)

            if existing_headers:
                # Validate headers match (same as sync.py append mode)
                if existing_headers != filtered_headers:
                    # Provide detailed mismatch info
                    missing_in_sheet = set(filtered_headers) - set(existing_headers)
                    missing_in_data = set(existing_headers) - set(filtered_headers)
                    order_mismatch = (
                        set(filtered_headers) == set(existing_headers)
                        and filtered_headers != existing_headers
                    )

                    details = []
                    if missing_in_sheet:
                        details.append(f"columns missing in sheet: {sorted(missing_in_sheet)}")
                    if missing_in_data:
                        details.append(f"extra columns in sheet: {sorted(missing_in_data)}")
                    if order_mismatch:
                        details.append("column order differs")

                    return TargetSyncResult(
                        target=target,
                        success=False,
                        error=(
                            f"Append mode header mismatch for '{target.worksheet_name}'. "
                            f"Existing headers: {existing_headers}, "
                            f"new headers: {filtered_headers}. "
                            f"Details: {'; '.join(details) if details else 'headers differ'}. "
                            f"Use 'replace' mode to overwrite with new column structure."
                        ),
                    )

                # Headers match, just append the rows
                worksheet.append_rows(
                    values=filtered_rows,
                    value_input_option="USER_ENTERED",  # type: ignore[arg-type]
                )
            else:
                # Empty sheet - add headers first, then rows
                if logger:
                    logger.info(
                        f"Empty sheet detected for append mode, adding headers first: "
                        f"{target.sheet_id}/{worksheet_name}"
                    )
                # Write headers first
                worksheet.update(
                    values=[filtered_headers],
                    range_name="A1",
                    value_input_option="USER_ENTERED",  # type: ignore[arg-type]
                )
                # Then append rows
                if filtered_rows:
                    worksheet.append_rows(
                        values=filtered_rows,
                        value_input_option="USER_ENTERED",  # type: ignore[arg-type]
                    )
        else:
            raise ValueError(f"Unknown sync mode: {target.mode}")

        return TargetSyncResult(
            target=target,
            success=True,
            rows_synced=len(filtered_rows),
            message=f"Successfully synced {len(filtered_rows)} rows",
        )

    except gspread.exceptions.SpreadsheetNotFound:
        return TargetSyncResult(
            target=target,
            success=False,
            error=f"Spreadsheet not found: {target.sheet_id}",
        )
    except gspread.exceptions.WorksheetNotFound:
        return TargetSyncResult(
            target=target,
            success=False,
            error=f"Worksheet not found: {target.worksheet_name}",
        )
    except (OSError, gspread.exceptions.GSpreadException, SyncError, ValueError) as e:
        return TargetSyncResult(
            target=target,
            success=False,
            error=str(e),
        )


def run_multi_sheet_sync(
    config: Config | None = None,
    targets: list[SheetTarget] | None = None,
    logger: logging.Logger | None = None,
    dry_run: bool = False,
    parallel: bool = False,
    max_workers: int = 4,
) -> MultiSheetSyncResult:
    """Execute multi-sheet sync operation.

    Fetches data from the database once and pushes to multiple sheet targets.

    Args:
        config: Main configuration. If None, loads from environment.
        targets: List of SheetTarget configurations. If None, uses config.multi_sheet_targets.
        logger: Logger instance. If None, creates one.
        dry_run: If True, fetch data but don't push to sheets.
        parallel: If True, push to targets in parallel.
        max_workers: Maximum parallel workers (default 4).

    Returns:
        MultiSheetSyncResult with operation status and per-target results.

    Raises:
        ConfigError: If configuration is invalid.
        DatabaseError: If database operations fail.
    """
    # Load config if not provided
    if config is None:
        config = get_config()

    # Setup logging if not provided
    if logger is None:
        logger = setup_logging(config)

    # Get targets
    if targets is None:
        targets = config.multi_sheet_targets

    if not targets:
        raise ConfigError(
            message="No sheet targets specified for multi-sheet sync",
            missing_fields=["targets"],
        )

    # Validate no duplicate targets (would cause race condition in parallel mode)
    validate_targets_unique(targets)

    db_type = config.db_type.lower()
    logger.info(f"Starting multi-sheet sync: {db_type.upper()} -> {len(targets)} sheets")

    try:
        # Fetch data from database (once for all targets)
        headers, rows = fetch_data(config, logger)

        if not rows:
            logger.warning("No data returned from query")
            return MultiSheetSyncResult(
                success=True,
                total_rows_fetched=0,
                message="Multi-sheet sync completed (empty dataset)",
            )

        # Clean data for Google Sheets compatibility
        cleaned_rows = clean_data(rows, logger, db_type=db_type)

        # Apply column mapping if configured
        col_mapping_config = _build_column_mapping_config(config)
        if col_mapping_config.is_active():
            logger.info("Applying column mapping transformations")
            headers, cleaned_rows = apply_column_mapping(headers, cleaned_rows, col_mapping_config)

        logger.info(f"Fetched {len(cleaned_rows)} rows, pushing to {len(targets)} targets")

        # Validate batch size before pushing to any target (Edge Case 30)
        # This catches oversized cells and ragged rows before any partial writes
        validate_batch_size(headers, cleaned_rows, logger)

        # Dry run mode
        if dry_run:
            target_results = []
            for target in targets:
                # Calculate what would be synced
                filtered_headers = headers
                filtered_rows = cleaned_rows

                if target.column_filter:
                    filtered_headers, filtered_rows = filter_columns(
                        headers, cleaned_rows, target.column_filter
                    )
                if target.row_filter:
                    filtered_rows = filter_rows(filtered_headers, filtered_rows, target.row_filter)

                target_results.append(
                    TargetSyncResult(
                        target=target,
                        success=True,
                        rows_synced=len(filtered_rows),
                        message=f"Would sync {len(filtered_rows)} rows",
                    )
                )

            return MultiSheetSyncResult(
                success=True,
                total_rows_fetched=len(cleaned_rows),
                target_results=target_results,
                message=f"Dry run: would sync to {len(targets)} targets",
            )

        # Push to targets (parallel or sequential)
        target_results = []

        if parallel:
            logger.info(f"Pushing to targets in parallel (max {max_workers} workers)")

            # Copy context for worker threads to preserve TenantContext
            # This is Edge Case 26: ContextVar is NOT inherited by ThreadPoolExecutor
            # threads. We must explicitly copy the context to preserve tenant isolation.
            ctx = contextvars.copy_context()

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        ctx.run,  # Run within copied context
                        push_to_target,
                        target,
                        headers,
                        cleaned_rows,
                        config.service_account_file,
                        logger,
                    ): target
                    for target in targets
                }

                for future in as_completed(futures):
                    result = future.result()
                    target_results.append(result)
        else:
            logger.info("Pushing to targets sequentially")
            for target in targets:
                result = push_to_target(
                    target,
                    headers,
                    cleaned_rows,
                    config.service_account_file,
                    logger,
                )
                target_results.append(result)

        # Determine overall success
        all_success = all(r.success for r in target_results)
        succeeded = sum(1 for r in target_results if r.success)
        failed = len(target_results) - succeeded

        message = f"Multi-sheet sync completed: {succeeded}/{len(targets)} targets succeeded"
        if failed > 0:
            message += f", {failed} failed"

        return MultiSheetSyncResult(
            success=all_success,
            total_rows_fetched=len(cleaned_rows),
            target_results=target_results,
            message=message,
        )

    except (SyncError, OSError, ValueError) as e:
        logger.error(f"Multi-sheet sync failed: {e}")
        return MultiSheetSyncResult(
            success=False,
            message=str(e),
            error=str(e),
        )


class MultiSheetSyncService:
    """Service class for multi-sheet sync operations.

    Provides a stateful interface for multi-sheet sync operations,
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
        """Initialize MultiSheetSyncService.

        Args:
            config: Configuration object. If None, loads from environment.
            logger: Logger instance. If None, creates one from config.
        """
        self.config = config or get_config()
        if logger is None:
            logger = setup_logging(self.config)
        self.logger = logger

    def sync(
        self,
        targets: list[SheetTarget],
        dry_run: bool = False,
        parallel: bool = False,
    ) -> MultiSheetSyncResult:
        """Execute multi-sheet sync with the given targets.

        Args:
            targets: List of sheet targets.
            dry_run: If True, validate without pushing to sheets.
            parallel: If True, push to targets in parallel.

        Returns:
            MultiSheetSyncResult with operation status.
        """
        return run_multi_sheet_sync(
            self.config, targets, self.logger, dry_run=dry_run, parallel=parallel
        )

    def sync_from_config(
        self,
        dry_run: bool = False,
        parallel: bool | None = None,
    ) -> MultiSheetSyncResult:
        """Execute multi-sheet sync using targets from config.

        Args:
            dry_run: If True, validate without pushing to sheets.
            parallel: If True, push in parallel. None uses config setting.

        Returns:
            MultiSheetSyncResult with operation status.
        """
        use_parallel = parallel if parallel is not None else self.config.multi_sheet_parallel
        return run_multi_sheet_sync(
            self.config,
            targets=None,  # Use config.multi_sheet_targets
            logger=self.logger,
            dry_run=dry_run,
            parallel=use_parallel,
        )
