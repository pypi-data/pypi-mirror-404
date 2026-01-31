"""Shared Pydantic request/response models for the API layer."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mysql_to_sheets import __version__


class SyncRequest(BaseModel):
    """Request body for sync endpoint."""

    sheet_id: str | None = Field(
        default=None,
        description="Google Sheets spreadsheet ID (overrides .env)",
    )
    worksheet_name: str | None = Field(
        default=None,
        description="Target worksheet name (overrides .env)",
    )
    sql_query: str | None = Field(
        default=None,
        description="SQL query to execute (overrides .env)",
    )
    db_type: str | None = Field(
        default=None,
        description="Database type: 'mysql' or 'postgres' (overrides .env)",
    )
    column_map: dict[str, str] | None = Field(
        default=None,
        description="Column rename mapping: {'old_name': 'New Name'}",
    )
    columns: list[str] | None = Field(
        default=None,
        description="List of columns to include and their order",
    )
    column_case: str | None = Field(
        default=None,
        description="Case transformation: 'none', 'upper', 'lower', 'title'",
    )
    dry_run: bool = Field(
        default=False,
        description="Validate and fetch data but don't push to Sheets",
    )
    preview: bool = Field(
        default=False,
        description="Show diff with current sheet data without pushing",
    )
    mode: str | None = Field(
        default=None,
        description="Sync mode: 'replace', 'append', or 'streaming' (overrides config)",
    )
    chunk_size: int | None = Field(
        default=None,
        description="Chunk size for streaming mode (overrides config)",
        ge=100,
        le=100000,
    )
    atomic: bool | None = Field(
        default=None,
        description="Enable atomic streaming (default: True). Writes to staging sheet first.",
    )
    preserve_gid: bool | None = Field(
        default=None,
        description="Preserve worksheet GID during atomic swap (default: False, slower)",
    )
    schema_policy: str | None = Field(
        default=None,
        description="Schema evolution policy: 'strict', 'additive', 'flexible', 'notify_only'",
    )
    expected_headers: list[str] | None = Field(
        default=None,
        description="Expected column headers from previous sync for schema comparison",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                "worksheet_name": "Sheet1",
                "sql_query": "SELECT * FROM users WHERE active = 1",
                "db_type": "mysql",
                "column_map": {"cust_id": "Customer ID", "txn_dt": "Transaction Date"},
                "columns": ["Customer ID", "Transaction Date", "Amount"],
                "dry_run": False,
            }
        }
    )


class ValidateRequest(BaseModel):
    """Request body for validate endpoint."""

    sheet_id: str | None = Field(
        default=None,
        description="Google Sheets spreadsheet ID to validate",
    )
    worksheet_name: str | None = Field(
        default=None,
        description="Worksheet name to validate",
    )
    sql_query: str | None = Field(
        default=None,
        description="SQL query to validate",
    )
    test_connections: bool = Field(
        default=False,
        description="Also test database and sheets connections",
    )


class DiffResponse(BaseModel):
    """Response body for diff/preview information."""

    has_changes: bool = False
    sheet_row_count: int = 0
    query_row_count: int = 0
    rows_to_add: int = 0
    rows_to_remove: int = 0
    rows_unchanged: int = 0
    header_changes: dict[str, Any] = {}
    summary: str = ""


class SchemaChangeResponse(BaseModel):
    """Response body for schema change information."""

    has_changes: bool = False
    added_columns: list[str] = Field(default_factory=list)
    removed_columns: list[str] = Field(default_factory=list)
    reordered: bool = False
    expected_headers: list[str] = Field(default_factory=list)
    actual_headers: list[str] = Field(default_factory=list)
    policy_applied: str | None = None


class SyncResponse(BaseModel):
    """Response body for sync endpoint."""

    success: bool
    rows_synced: int = 0
    columns: int = 0
    headers: list[str] = []
    message: str = ""
    error: str | None = None
    preview: bool = False
    diff: DiffResponse | None = None
    schema_changes: SchemaChangeResponse | None = None
    resumable: bool = False
    checkpoint_chunk: int | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class ResumeSyncResponse(BaseModel):
    """Response body for resume sync endpoint."""

    success: bool
    rows_synced: int = 0
    message: str = ""
    error: str | None = None
    resumed_from_chunk: int = 0
    resumed_from_rows: int = 0
    total_chunks: int = 0
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class CheckpointResponse(BaseModel):
    """Response body for checkpoint status endpoint."""

    job_id: int
    config_id: int
    staging_worksheet_name: str
    staging_worksheet_gid: int
    chunks_completed: int
    rows_pushed: int
    headers: list[str] = []
    created_at: str
    updated_at: str


class ValidateResponse(BaseModel):
    """Response body for validate endpoint."""

    valid: bool
    errors: list[str] = []
    database_ok: bool | None = None
    sheets_ok: bool | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class HealthResponse(BaseModel):
    """Response body for health endpoint."""

    status: str = "healthy"
    version: str = __version__
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str = ""
    code: str | None = None
    hint: str | None = None
    details: dict[str, Any] = {}


class HistoryEntryResponse(BaseModel):
    """Response model for a single history entry."""

    id: int | None = None
    timestamp: str
    success: bool
    rows_synced: int = 0
    columns: int = 0
    headers: list[str] = []
    message: str = ""
    error: str | None = None
    sheet_id: str | None = None
    worksheet: str | None = None
    duration_ms: float = 0.0
    request_id: str | None = None
    source: str | None = None


class HistoryResponse(BaseModel):
    """Response body for history endpoint."""

    entries: list[HistoryEntryResponse]
    total: int
    limit: int
    offset: int


class DeepHealthResponse(BaseModel):
    """Response body for deep health check endpoint."""

    status: str = "healthy"
    version: str = __version__
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    checks: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ErrorStatsResponse(BaseModel):
    """Response body for error statistics endpoint."""

    total_errors_24h: int = 0
    errors_by_category: dict[str, int] = Field(default_factory=dict)
    top_error_codes: list[dict[str, Any]] = Field(default_factory=list)
    retry_success_rate: float | None = None
    hours: int = 24


class ScheduleCreateRequest(BaseModel):
    """Request body for creating a scheduled job."""

    name: str = Field(..., min_length=1, max_length=100, description="Job name")
    cron_expression: str | None = Field(
        default=None,
        description="Cron expression (e.g., '0 6 * * *')",
    )
    interval_minutes: int | None = Field(
        default=None,
        ge=1,
        description="Interval in minutes (alternative to cron)",
    )
    sheet_id: str | None = Field(default=None, description="Override Google Sheet ID")
    worksheet_name: str | None = Field(default=None, description="Override worksheet name")
    sql_query: str | None = Field(default=None, description="Override SQL query")
    notify_on_success: bool | None = Field(
        default=None,
        description="Override success notification (None = use config)",
    )
    notify_on_failure: bool | None = Field(
        default=None,
        description="Override failure notification (None = use config)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "daily-sync",
                "cron_expression": "0 6 * * *",
                "sheet_id": None,
                "worksheet_name": None,
            }
        }
    )


class ScheduleUpdateRequest(BaseModel):
    """Request body for updating a scheduled job."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    cron_expression: str | None = Field(default=None)
    interval_minutes: int | None = Field(default=None, ge=1)
    sheet_id: str | None = Field(default=None)
    worksheet_name: str | None = Field(default=None)
    sql_query: str | None = Field(default=None)
    notify_on_success: bool | None = Field(default=None)
    notify_on_failure: bool | None = Field(default=None)
    enabled: bool | None = Field(default=None)


class ScheduleResponse(BaseModel):
    """Response body for a scheduled job."""

    id: int
    name: str
    cron_expression: str | None = None
    interval_minutes: int | None = None
    sheet_id: str | None = None
    worksheet_name: str | None = None
    sql_query: str | None = None
    notify_on_success: bool | None = None
    notify_on_failure: bool | None = None
    enabled: bool = True
    created_at: str | None = None
    updated_at: str | None = None
    last_run_at: str | None = None
    last_run_success: bool | None = None
    last_run_message: str | None = None
    last_run_rows: int | None = None
    last_run_duration_ms: float | None = None
    next_run_at: str | None = None
    status: str = "pending"
    schedule_display: str = ""


class ScheduleListResponse(BaseModel):
    """Response body for listing scheduled jobs."""

    schedules: list[ScheduleResponse]
    total: int


class NotificationStatusResponse(BaseModel):
    """Response body for notification status."""

    backends: dict[str, dict[str, Any]]


class NotificationTestRequest(BaseModel):
    """Request body for testing notifications."""

    backend: str = Field(
        default="all",
        description="Backend to test (email, slack, webhook, or all)",
    )


class NotificationTestResponse(BaseModel):
    """Response body for notification test."""

    success: bool
    results: dict[str, Any]


# PII Schemas


class PIIColumnResponse(BaseModel):
    """Response for a single PII column detection."""

    column_name: str
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_transform: str


class PIIDetectionResponse(BaseModel):
    """Response for PII detection results."""

    columns: list[PIIColumnResponse] = Field(default_factory=list)
    has_pii: bool = False
    requires_acknowledgment: bool = False
    detection_method: str = "combined"


class PIIDetectRequest(BaseModel):
    """Request for PII detection on a query."""

    query: str | None = Field(
        default=None,
        description="SQL query to analyze (uses .env SQL_QUERY if not provided)",
    )
    sample_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of rows to sample for content analysis",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence level for detection",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "SELECT id, email, phone, ssn FROM users LIMIT 100",
                "sample_size": 100,
                "confidence_threshold": 0.7,
            }
        }
    )


class PIITransformPreviewRequest(BaseModel):
    """Request for previewing PII transformations."""

    query: str | None = Field(
        default=None,
        description="SQL query to preview transforms on",
    )
    transform_map: dict[str, str] = Field(
        default_factory=dict,
        description="Column to transform mapping: {'email': 'hash', 'phone': 'redact'}",
    )
    sample_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of rows to show in preview",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "SELECT email, phone, ssn FROM users LIMIT 5",
                "transform_map": {"email": "hash", "phone": "redact", "ssn": "partial_mask"},
                "sample_size": 5,
            }
        }
    )


class PIITransformPreviewRow(BaseModel):
    """A single row of transform preview data."""

    original: dict[str, Any]
    transformed: dict[str, Any]


class PIITransformPreviewResponse(BaseModel):
    """Response for PII transform preview."""

    rows: list[PIITransformPreviewRow] = Field(default_factory=list)
    columns_transformed: list[str] = Field(default_factory=list)
    transform_map: dict[str, str] = Field(default_factory=dict)


class PIIPolicyResponse(BaseModel):
    """Response for a PII policy."""

    organization_id: int
    auto_detect_enabled: bool = True
    default_transforms: dict[str, str] = Field(default_factory=dict)
    require_acknowledgment: bool = True
    block_unacknowledged: bool = False
    created_at: str | None = None
    updated_at: str | None = None


class PIIPolicyUpdateRequest(BaseModel):
    """Request to update a PII policy."""

    auto_detect_enabled: bool | None = Field(
        default=None,
        description="Enable automatic PII detection",
    )
    default_transforms: dict[str, str] | None = Field(
        default=None,
        description="Default transforms by category: {'email': 'hash', 'phone': 'redact'}",
    )
    require_acknowledgment: bool | None = Field(
        default=None,
        description="Require acknowledgment before syncing detected PII",
    )
    block_unacknowledged: bool | None = Field(
        default=None,
        description="Block sync if PII not acknowledged (ENTERPRISE only)",
    )


class PIIAcknowledgmentRequest(BaseModel):
    """Request to acknowledge PII in a sync config."""

    config_id: int = Field(..., description="Sync configuration ID")
    column_name: str = Field(..., description="Column name to acknowledge")
    category: str = Field(..., description="PII category (email, phone, ssn, etc.)")
    transform: str = Field(
        ...,
        description="Transform to apply: 'none', 'hash', 'redact', 'partial_mask'",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "config_id": 1,
                "column_name": "email",
                "category": "email",
                "transform": "hash",
            }
        }
    )


class PIIAcknowledgmentResponse(BaseModel):
    """Response for a PII acknowledgment record."""

    id: int
    sync_config_id: int
    column_name: str
    category: str
    transform: str
    acknowledged_by_user_id: int
    acknowledged_at: str


# =============================================================================
# Common Response Base Classes
# =============================================================================


class MessageResponse(BaseModel):
    """Standard message response for simple confirmations."""

    message: str
    success: bool = True
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


class BasePaginatedResponse(BaseModel):
    """Base class for paginated list responses.

    Subclasses should add their specific `items` field with the appropriate type.
    """

    total: int = Field(..., description="Total count of items across all pages")
    limit: int = Field(50, ge=1, le=100, description="Page size limit")
    offset: int = Field(0, ge=0, description="Starting offset for pagination")


class BaseTimestampedResponse(BaseModel):
    """Base class for responses with timestamp field."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of response",
    )
