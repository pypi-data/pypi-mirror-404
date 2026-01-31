"""Request override helpers for configuration.

This module provides centralized utilities for applying request-based overrides
to configuration objects. It eliminates the duplicated pattern of:
    reset_config()
    config = get_config()
    overrides = {}
    if request.sheet_id:
        overrides["google_sheet_id"] = request.sheet_id
    ...
    if overrides:
        config = config.with_overrides(**overrides)

Usage:
    from mysql_to_sheets.core.config import apply_request_overrides

    # From API/Web request dict
    config = apply_request_overrides(request_data)

    # From argparse Namespace
    config = apply_request_overrides(args)

    # With explicit base config
    config = apply_request_overrides(request_data, base_config=existing_config)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from argparse import Namespace

    from mysql_to_sheets.core.config.dataclass import Config


@runtime_checkable
class SyncRequestLike(Protocol):
    """Protocol for objects that can provide sync request overrides.

    Supports both Pydantic models (attribute access) and dicts.
    """

    def __getattr__(self, name: str) -> Any:
        ...


def _get_value(
    source: SyncRequestLike | dict[str, Any] | Namespace | None,
    key: str,
    default: Any = None,
) -> Any:
    """Extract a value from a request-like object.

    Handles dicts, Pydantic models, argparse Namespace, and other objects
    with attribute access.

    Args:
        source: The source object (dict, model, Namespace, etc.).
        key: The key/attribute to extract.
        default: Default value if key is missing or None.

    Returns:
        The extracted value or default.
    """
    if source is None:
        return default

    if isinstance(source, dict):
        value = source.get(key, default)
    else:
        value = getattr(source, key, default)

    return value if value is not None else default


def _parse_sheet_id_if_url(value: str) -> str:
    """Parse sheet ID from URL if needed.

    Args:
        value: Either a sheet ID or full Google Sheets URL.

    Returns:
        The extracted sheet ID.

    Raises:
        ValueError: If URL format is invalid.
    """
    from mysql_to_sheets.core.sheets_utils import parse_sheet_id

    return parse_sheet_id(value)


def _parse_column_map(value: str | dict[str, str] | None) -> str | None:
    """Parse column mapping to JSON string.

    Supports:
    - JSON string: '{"old": "new"}'
    - Dict: {"old": "new"}
    - Simple format: "old=new,old2=new2"

    Args:
        value: Column mapping in any supported format.

    Returns:
        JSON string or None.
    """
    if value is None:
        return None

    if isinstance(value, dict):
        return json.dumps(value)

    if isinstance(value, str):
        # Already JSON
        if value.startswith("{"):
            return value

        # Simple old=new,old2=new2 format
        mapping = {}
        for pair in value.split(","):
            if "=" in pair:
                old, new = pair.split("=", 1)
                mapping[old.strip()] = new.strip()
        return json.dumps(mapping) if mapping else None

    return None


def _parse_column_order(value: str | list[str] | None) -> str | None:
    """Parse column order to comma-separated string.

    Args:
        value: Column list or comma-separated string.

    Returns:
        Comma-separated string or None.
    """
    if value is None:
        return None

    if isinstance(value, list):
        return ",".join(value)

    return value


def apply_request_overrides(
    request: SyncRequestLike | dict[str, Any] | Namespace | None = None,
    *,
    base_config: Config | None = None,
    reset_before: bool = True,
    # Explicit overrides (take precedence over request)
    sheet_id: str | None = None,
    worksheet_name: str | None = None,
    sql_query: str | None = None,
    db_type: str | None = None,
    column_map: str | dict[str, str] | None = None,
    columns: str | list[str] | None = None,
    column_case: str | None = None,
    mode: str | None = None,
    chunk_size: int | None = None,
    notify: bool | None = None,
) -> Config:
    """Apply request overrides and return configured Config.

    This is the centralized helper for applying overrides from API requests,
    web forms, CLI arguments, or programmatic calls.

    Args:
        request: Source of overrides (dict, Pydantic model, argparse Namespace).
        base_config: Optional base config to use (skips get_config() if provided).
        reset_before: Whether to call reset_config() before get_config().
            Ignored if base_config is provided.

        # Explicit overrides (take precedence over request values)
        sheet_id: Google Sheet ID or URL.
        worksheet_name: Target worksheet name.
        sql_query: SQL query to execute.
        db_type: Database type (mysql, postgres, sqlite, mssql).
        column_map: Column rename mapping (JSON, dict, or simple format).
        columns: Column order/filter (list or comma-separated).
        column_case: Case transformation (none, upper, lower, title).
        mode: Sync mode (replace, append, streaming).
        chunk_size: Chunk size for streaming mode.
        notify: Whether to send notifications.

    Returns:
        Config instance with all overrides applied.

    Raises:
        ValueError: If sheet_id URL is malformed.

    Example:
        # API endpoint
        @router.post("/sync")
        async def execute_sync(request: SyncRequest):
            config = apply_request_overrides(request)
            result = run_sync(config)

        # CLI command
        def cmd_sync(args):
            config = apply_request_overrides(args)
            result = run_sync(config)

        # With explicit overrides
        config = apply_request_overrides(
            request_data,
            sheet_id="override_this",
            mode="streaming",
        )
    """
    from mysql_to_sheets.core.config.singleton import get_config, reset_config

    # Get base config
    if base_config is not None:
        config = base_config
    else:
        if reset_before:
            reset_config()
        config = get_config()

    # Build overrides dict
    overrides: dict[str, Any] = {}

    # === Sheet/Worksheet overrides ===
    # Priority: explicit args > request values
    _sheet_id = sheet_id or _get_value(request, "sheet_id") or _get_value(
        request, "google_sheet_id"
    )
    if _sheet_id:
        overrides["google_sheet_id"] = _parse_sheet_id_if_url(_sheet_id)

    _worksheet = worksheet_name or _get_value(
        request, "worksheet_name"
    ) or _get_value(request, "worksheet") or _get_value(
        request, "google_worksheet_name"
    )
    if _worksheet:
        overrides["google_worksheet_name"] = _worksheet

    # === Query override ===
    _query = sql_query or _get_value(request, "sql_query") or _get_value(
        request, "query"
    )
    if _query:
        overrides["sql_query"] = _query

    # === Database type override ===
    _db_type = db_type or _get_value(request, "db_type")
    if _db_type:
        overrides["db_type"] = _db_type

    # === Column mapping overrides ===
    _column_map = column_map or _get_value(request, "column_map")
    _columns = columns or _get_value(request, "columns") or _get_value(
        request, "column_order"
    )
    _column_case = column_case or _get_value(request, "column_case")

    if _column_map:
        parsed_map = _parse_column_map(_column_map)
        if parsed_map:
            overrides["column_mapping_enabled"] = True
            overrides["column_mapping"] = parsed_map

    if _columns:
        parsed_order = _parse_column_order(_columns)
        if parsed_order:
            overrides["column_mapping_enabled"] = True
            overrides["column_order"] = parsed_order

    if _column_case:
        overrides["column_mapping_enabled"] = True
        overrides["column_case"] = _column_case

    # === Sync mode overrides ===
    _mode = mode or _get_value(request, "mode") or _get_value(request, "sync_mode")
    if _mode:
        overrides["sync_mode"] = _mode

    _chunk_size = chunk_size or _get_value(request, "chunk_size")
    if _chunk_size is not None:
        overrides["sync_chunk_size"] = _chunk_size

    # === Notification override ===
    _notify = notify if notify is not None else _get_value(request, "notify")
    if _notify is not None:
        overrides["notify_on_success"] = _notify
        overrides["notify_on_failure"] = _notify

    # Apply overrides if any
    if overrides:
        config = config.with_overrides(**overrides)

    return config


def extract_sync_options(
    request: SyncRequestLike | dict[str, Any] | Namespace | None = None,
    *,
    # Explicit overrides
    dry_run: bool | None = None,
    preview: bool | None = None,
    atomic: bool | None = None,
    preserve_gid: bool | None = None,
    resumable: bool | None = None,
    create_worksheet: bool | None = None,
    schema_policy: str | None = None,
    expected_headers: list[str] | None = None,
    detect_pii: bool | None = None,
    pii_acknowledged: bool | None = None,
) -> dict[str, Any]:
    """Extract sync execution options from a request.

    These are options that affect sync execution but don't modify the
    Config object. They are passed directly to run_sync().

    Args:
        request: Source of options (dict, Pydantic model, argparse Namespace).
        dry_run: Validate without pushing.
        preview: Show diff without pushing.
        atomic: Enable atomic streaming mode.
        preserve_gid: Preserve worksheet GID during atomic swap.
        resumable: Enable checkpoint/resume for streaming.
        create_worksheet: Create worksheet if missing.
        schema_policy: Schema evolution policy.
        expected_headers: Expected column headers for schema comparison.
        detect_pii: Override PII detection setting.
        pii_acknowledged: Whether PII has been acknowledged.

    Returns:
        Dict of sync options suitable for passing to run_sync().

    Example:
        config = apply_request_overrides(request)
        options = extract_sync_options(request)
        result = run_sync(config, **options)
    """
    options: dict[str, Any] = {}

    # Boolean options with explicit defaults
    _dry_run = dry_run if dry_run is not None else _get_value(request, "dry_run", False)
    options["dry_run"] = _dry_run

    _preview = preview if preview is not None else _get_value(request, "preview", False)
    options["preview"] = _preview

    _atomic = atomic if atomic is not None else _get_value(request, "atomic")
    if _atomic is not None:
        options["atomic"] = _atomic

    _preserve_gid = preserve_gid if preserve_gid is not None else _get_value(
        request, "preserve_gid"
    )
    if _preserve_gid is not None:
        options["preserve_gid"] = _preserve_gid

    _resumable = resumable if resumable is not None else _get_value(
        request, "resumable", False
    )
    if _resumable:
        options["resumable"] = _resumable

    _create_ws = create_worksheet if create_worksheet is not None else _get_value(
        request, "create_worksheet"
    )
    if _create_ws is not None:
        options["create_worksheet"] = _create_ws

    # Schema evolution
    _schema_policy = schema_policy or _get_value(request, "schema_policy")
    if _schema_policy:
        options["schema_policy"] = _schema_policy

    _expected_headers = expected_headers or _get_value(request, "expected_headers")
    if _expected_headers:
        options["expected_headers"] = _expected_headers

    # PII options
    _detect_pii = detect_pii if detect_pii is not None else _get_value(
        request, "detect_pii"
    )
    if _detect_pii is not None:
        options["detect_pii"] = _detect_pii

    _pii_ack = pii_acknowledged if pii_acknowledged is not None else _get_value(
        request, "pii_acknowledged", False
    )
    if _pii_ack:
        options["pii_acknowledged"] = _pii_ack

    return options


__all__ = [
    "apply_request_overrides",
    "extract_sync_options",
    "SyncRequestLike",
]
