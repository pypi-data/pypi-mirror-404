"""Configuration dataclass definition.

This module contains the Config dataclass and SheetTarget dataclass
that define the configuration schema for the sync tool.
"""

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from mysql_to_sheets.core.config.parsing import (
    parse_bool,
    parse_env_sheet_id,
    safe_parse_float,
    safe_parse_int,
)
from mysql_to_sheets.core.config.validation import (
    check_placeholders,
    check_service_account_readable,
    detect_sql_file_path,
    strip_sql_comments,
    validate_service_account_json,
    validate_service_account_structure,
)
from mysql_to_sheets.core.exceptions import ConfigError
from mysql_to_sheets.core.paths import (
    get_default_api_keys_db_path,
    get_default_history_db_path,
    get_default_log_path,
    get_default_scheduler_db_path,
    get_default_service_account_path,
    get_default_tenant_db_path,
)


@dataclass
class SheetTarget:
    """Configuration for a multi-sheet sync target.

    Defines a target Google Sheet for multi-sheet sync operations,
    allowing one query result to be pushed to multiple sheets with
    optional column and row filtering.

    Attributes:
        sheet_id: Google Sheets spreadsheet ID.
        worksheet_name: Target worksheet tab name.
        column_filter: Optional list of columns to include (None = all columns).
        row_filter: Optional filter expression for rows (e.g., "status == 'active'").
        mode: Sync mode for this target ('replace' or 'append').
    """

    sheet_id: str
    worksheet_name: str = "Sheet1"
    column_filter: list[str] | None = None
    row_filter: str | None = None
    mode: str = "replace"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the target.
        """
        return {
            "sheet_id": self.sheet_id,
            "worksheet_name": self.worksheet_name,
            "column_filter": self.column_filter,
            "row_filter": self.row_filter,
            "mode": self.mode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SheetTarget":
        """Create SheetTarget from dictionary.

        Args:
            data: Dictionary with target data.

        Returns:
            SheetTarget instance.
        """
        return cls(
            sheet_id=data["sheet_id"],
            worksheet_name=data.get("worksheet_name", "Sheet1"),
            column_filter=data.get("column_filter"),
            row_filter=data.get("row_filter"),
            mode=data.get("mode", "replace"),
        )


@dataclass
class Config:
    """Configuration for the sync tool.

    Attributes:
        db_type: Database type ('mysql' or 'postgres').
        db_host: Database server hostname.
        db_port: Database server port (3306 for MySQL, 5432 for PostgreSQL).
        db_user: Database username.
        db_password: Database password.
        db_name: Database name.
        db_connect_timeout: Connection timeout in seconds.
        db_read_timeout: Read timeout in seconds.
        db_ssl_mode: SSL mode for PostgreSQL (disable, require, verify-ca, verify-full).
        db_ssl_ca: Path to SSL CA certificate file.
        google_sheet_id: Target Google Sheets spreadsheet ID.
        google_worksheet_name: Target worksheet tab name.
        service_account_file: Path to Google Service Account JSON.
        sheets_timeout: Google Sheets API timeout in seconds.
        sql_query: SQL query to execute.
        log_file: Path to log file.
        log_level: Logging verbosity level.
        log_format: Log format ('text' or 'json').
        retry_max_attempts: Maximum retry attempts for transient failures.
        retry_base_delay: Base delay between retries in seconds.
        circuit_breaker_enabled: Whether to enable circuit breaker pattern.
        history_backend: History storage backend ('memory' or 'sqlite').
        history_db_path: Path to SQLite history database.
        metrics_enabled: Whether to enable Prometheus metrics endpoint.
        api_auth_enabled: Whether to enable API key authentication.
        api_keys_db_path: Path to API keys SQLite database.
        rate_limit_enabled: Whether to enable rate limiting.
        rate_limit_rpm: Rate limit requests per minute.
        cors_allowed_origins: Comma-separated list of allowed CORS origins.
        sql_validation_enabled: Whether to validate SQL queries for safety.
        sync_mode: Default sync mode ('replace', 'append', 'streaming').
        sync_chunk_size: Chunk size for streaming sync mode.
        incremental_enabled: Whether to enable incremental sync.
        incremental_timestamp_column: Column name for incremental sync filtering.
    """

    # Database connection
    db_type: str = field(default_factory=lambda: os.getenv("DB_TYPE", "mysql"))
    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    db_port: int = field(
        default_factory=lambda: safe_parse_int("DB_PORT", 3306, min_value=1, max_value=65535)
    )
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", ""))
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", ""))
    db_connect_timeout: int = field(
        default_factory=lambda: safe_parse_int("DB_CONNECT_TIMEOUT", 10, min_value=1)
    )
    db_read_timeout: int = field(
        default_factory=lambda: safe_parse_int("DB_READ_TIMEOUT", 300, min_value=1)
    )
    db_pool_enabled: bool = field(default_factory=lambda: parse_bool("DB_POOL_ENABLED", False))
    db_pool_size: int = field(
        default_factory=lambda: safe_parse_int("DB_POOL_SIZE", 5, min_value=1)
    )
    db_ssl_mode: str = field(default_factory=lambda: os.getenv("DB_SSL_MODE", ""))
    db_ssl_ca: str = field(default_factory=lambda: os.getenv("DB_SSL_CA", ""))

    # Google Sheets
    google_sheet_id: str = field(
        default_factory=lambda: parse_env_sheet_id(os.getenv("GOOGLE_SHEET_ID", ""))
    )
    google_worksheet_name: str = field(
        default_factory=lambda: os.getenv("GOOGLE_WORKSHEET_NAME", "Sheet1")
    )
    service_account_file: str = field(
        default_factory=lambda: os.getenv(
            "SERVICE_ACCOUNT_FILE", str(get_default_service_account_path())
        )
    )
    sheets_timeout: int = field(
        default_factory=lambda: safe_parse_int("SHEETS_TIMEOUT", 60, min_value=1)
    )

    # Query
    sql_query: str = field(default_factory=lambda: os.getenv("SQL_QUERY", ""))

    # Logging
    log_file: str = field(
        default_factory=lambda: os.getenv("LOG_FILE", str(get_default_log_path()))
    )
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = field(default_factory=lambda: os.getenv("LOG_FORMAT", "text"))
    log_pii_masking: bool = field(default_factory=lambda: parse_bool("LOG_PII_MASKING", True))
    log_max_bytes: int = field(
        default_factory=lambda: safe_parse_int("LOG_MAX_BYTES", 10485760, min_value=1024)
    )
    log_backup_count: int = field(
        default_factory=lambda: safe_parse_int("LOG_BACKUP_COUNT", 5, min_value=0)
    )

    # Retry & Circuit Breaker (Phase 1)
    retry_max_attempts: int = field(
        default_factory=lambda: safe_parse_int("RETRY_MAX_ATTEMPTS", 3, min_value=1)
    )
    retry_base_delay: float = field(
        default_factory=lambda: safe_parse_float("RETRY_BASE_DELAY", 1.0)
    )
    circuit_breaker_enabled: bool = field(
        default_factory=lambda: parse_bool("CIRCUIT_BREAKER_ENABLED", False)
    )

    # History & Metrics (Phase 2)
    history_backend: str = field(default_factory=lambda: os.getenv("HISTORY_BACKEND", "memory"))
    history_db_path: str = field(
        default_factory=lambda: os.getenv("HISTORY_DB_PATH", str(get_default_history_db_path()))
    )
    metrics_enabled: bool = field(default_factory=lambda: parse_bool("METRICS_ENABLED", False))

    # Security (Phase 3)
    # API authentication is ENABLED by default for production security.
    # Set API_AUTH_ENABLED=false explicitly to disable (not recommended for production).
    api_auth_enabled: bool = field(default_factory=lambda: parse_bool("API_AUTH_ENABLED", True))
    api_keys_db_path: str = field(
        default_factory=lambda: os.getenv("API_KEYS_DB_PATH", str(get_default_api_keys_db_path()))
    )
    # Rate limiting is ENABLED by default for production security.
    # Set RATE_LIMIT_ENABLED=false explicitly to disable (not recommended for production).
    rate_limit_enabled: bool = field(default_factory=lambda: parse_bool("RATE_LIMIT_ENABLED", True))
    rate_limit_rpm: int = field(
        default_factory=lambda: safe_parse_int("RATE_LIMIT_RPM", 60, min_value=1)
    )
    cors_allowed_origins: str = field(default_factory=lambda: os.getenv("CORS_ALLOWED_ORIGINS", ""))
    sql_validation_enabled: bool = field(
        default_factory=lambda: parse_bool("SQL_VALIDATION_ENABLED", True)
    )

    # Sync Modes (Phase 4)
    sync_mode: str = field(default_factory=lambda: os.getenv("SYNC_MODE", "replace"))
    # EC-51: Validate chunk size with max bound (CLI validates <= 100000)
    sync_chunk_size: int = field(
        default_factory=lambda: safe_parse_int(
            "SYNC_CHUNK_SIZE", 1000, min_value=1, max_value=100000
        )
    )
    sync_empty_result_action: str = field(
        default_factory=lambda: os.getenv("SYNC_EMPTY_RESULT_ACTION", "warn")
    )
    incremental_enabled: bool = field(
        default_factory=lambda: parse_bool("INCREMENTAL_ENABLED", False)
    )
    incremental_timestamp_column: str = field(
        default_factory=lambda: os.getenv("INCREMENTAL_TIMESTAMP_COLUMN", "")
    )

    # Atomic Streaming (Transactional Consistency)
    # When enabled, streaming mode writes to a staging worksheet first,
    # then atomically swaps it to the live worksheet after completion.
    streaming_atomic_enabled: bool = field(
        default_factory=lambda: parse_bool("STREAMING_ATOMIC_ENABLED", True)
    )
    streaming_staging_prefix: str = field(
        default_factory=lambda: os.getenv("STREAMING_STAGING_PREFIX", "_staging_")
    )
    streaming_preserve_gid: bool = field(
        default_factory=lambda: parse_bool("STREAMING_PRESERVE_GID", False)
    )
    streaming_verification_enabled: bool = field(
        default_factory=lambda: parse_bool("STREAMING_VERIFICATION_ENABLED", True)
    )
    streaming_staging_max_age_minutes: int = field(
        default_factory=lambda: safe_parse_int(
            "STREAMING_STAGING_MAX_AGE_MINUTES", 60, min_value=1
        )
    )

    # Column Mapping (Phase 2 - Competitive Parity)
    column_mapping_enabled: bool = field(
        default_factory=lambda: parse_bool("COLUMN_MAPPING_ENABLED", False)
    )
    column_mapping: str = field(default_factory=lambda: os.getenv("COLUMN_MAPPING", ""))
    column_order: str = field(default_factory=lambda: os.getenv("COLUMN_ORDER", ""))
    column_case: str = field(default_factory=lambda: os.getenv("COLUMN_CASE", "none"))
    column_strip_prefix: str = field(default_factory=lambda: os.getenv("COLUMN_STRIP_PREFIX", ""))
    column_strip_suffix: str = field(default_factory=lambda: os.getenv("COLUMN_STRIP_SUFFIX", ""))

    # Notifications (MVP+)
    notify_on_success: bool = field(default_factory=lambda: parse_bool("NOTIFY_ON_SUCCESS", False))
    notify_on_failure: bool = field(default_factory=lambda: parse_bool("NOTIFY_ON_FAILURE", True))
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", ""))
    smtp_port: int = field(
        default_factory=lambda: safe_parse_int("SMTP_PORT", 587, min_value=1, max_value=65535)
    )
    smtp_user: str = field(default_factory=lambda: os.getenv("SMTP_USER", ""))
    smtp_password: str = field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    smtp_from: str = field(default_factory=lambda: os.getenv("SMTP_FROM", ""))
    smtp_to: str = field(default_factory=lambda: os.getenv("SMTP_TO", ""))
    smtp_use_tls: bool = field(default_factory=lambda: parse_bool("SMTP_USE_TLS", True))
    slack_webhook_url: str = field(default_factory=lambda: os.getenv("SLACK_WEBHOOK_URL", ""))
    notification_webhook_url: str = field(
        default_factory=lambda: os.getenv("NOTIFICATION_WEBHOOK_URL", "")
    )

    # Scheduler (MVP+)
    scheduler_enabled: bool = field(default_factory=lambda: parse_bool("SCHEDULER_ENABLED", False))
    scheduler_db_path: str = field(
        default_factory=lambda: os.getenv("SCHEDULER_DB_PATH", str(get_default_scheduler_db_path()))
    )
    scheduler_timezone: str = field(default_factory=lambda: os.getenv("SCHEDULER_TIMEZONE", "UTC"))
    scheduler_lock_ttl_seconds: int = field(
        default_factory=lambda: safe_parse_int("SCHEDULER_LOCK_TTL_SECONDS", 300, min_value=1)
    )
    scheduler_lock_heartbeat_interval: int = field(
        default_factory=lambda: safe_parse_int("SCHEDULER_LOCK_HEARTBEAT_INTERVAL", 30, min_value=1)
    )

    # JWT Authentication (Phase 3)
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", ""))
    jwt_access_token_expire_minutes: int = field(
        default_factory=lambda: safe_parse_int("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30, min_value=1)
    )
    jwt_refresh_token_expire_days: int = field(
        default_factory=lambda: safe_parse_int("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7, min_value=1)
    )

    # Session Configuration (Phase 3)
    session_secret_key: str = field(
        default_factory=lambda: os.getenv("SESSION_SECRET_KEY", "dev-secret-change-in-production")
    )
    session_lifetime_hours: int = field(
        default_factory=lambda: safe_parse_int("SESSION_LIFETIME_HOURS", 24, min_value=1)
    )

    # Password Configuration (Phase 3)
    password_min_length: int = field(
        default_factory=lambda: safe_parse_int("PASSWORD_MIN_LENGTH", 8, min_value=1)
    )

    # Lockout Configuration
    lockout_max_attempts: int = field(
        default_factory=lambda: safe_parse_int("LOCKOUT_MAX_ATTEMPTS", 5, min_value=1)
    )
    lockout_duration_minutes: int = field(
        default_factory=lambda: safe_parse_int("LOCKOUT_DURATION_MINUTES", 15, min_value=1)
    )
    lockout_window_minutes: int = field(
        default_factory=lambda: safe_parse_int("LOCKOUT_WINDOW_MINUTES", 30, min_value=1)
    )
    # SECURITY: Fail-closed by default. If lockout DB is unavailable, block login.
    # Set LOCKOUT_FAIL_OPEN=true only if availability is more important than security.
    lockout_fail_open: bool = field(default_factory=lambda: parse_bool("LOCKOUT_FAIL_OPEN", False))

    # RBAC Defaults (Phase 3)
    default_user_role: str = field(default_factory=lambda: os.getenv("DEFAULT_USER_ROLE", "viewer"))
    default_org_max_users: int = field(
        default_factory=lambda: safe_parse_int("DEFAULT_ORG_MAX_USERS", 5, min_value=1)
    )
    default_org_max_configs: int = field(
        default_factory=lambda: safe_parse_int("DEFAULT_ORG_MAX_CONFIGS", 10, min_value=1)
    )

    # Webhook Configuration (Phase 3)
    webhook_timeout_seconds: int = field(
        default_factory=lambda: safe_parse_int("WEBHOOK_TIMEOUT_SECONDS", 30, min_value=1)
    )
    webhook_max_retries: int = field(
        default_factory=lambda: safe_parse_int("WEBHOOK_MAX_RETRIES", 3, min_value=0)
    )
    webhook_disable_after_failures: int = field(
        default_factory=lambda: safe_parse_int("WEBHOOK_DISABLE_AFTER_FAILURES", 10, min_value=1)
    )

    # Multi-tenant Database (Phase 3)
    tenant_db_path: str = field(
        default_factory=lambda: os.getenv("TENANT_DB_PATH", str(get_default_tenant_db_path()))
    )

    # Audit Logging (Phase 4)
    audit_retention_days: int = field(
        default_factory=lambda: safe_parse_int("AUDIT_RETENTION_DAYS", 90, min_value=1)
    )

    # Job Queue (Phase 4)
    job_queue_concurrency: int = field(
        default_factory=lambda: safe_parse_int("JOB_QUEUE_CONCURRENCY", 1, min_value=1)
    )
    job_max_attempts: int = field(
        default_factory=lambda: safe_parse_int("JOB_MAX_ATTEMPTS", 3, min_value=1)
    )
    job_retry_delay_seconds: int = field(
        default_factory=lambda: safe_parse_int("JOB_RETRY_DELAY_SECONDS", 60, min_value=0)
    )
    job_timeout_seconds: int = field(
        default_factory=lambda: safe_parse_int("JOB_TIMEOUT_SECONDS", 300, min_value=1)
    )

    # Freshness/SLA Tracking (Phase 4)
    default_freshness_sla_minutes: int = field(
        default_factory=lambda: safe_parse_int("DEFAULT_FRESHNESS_SLA_MINUTES", 60, min_value=1)
    )
    freshness_warning_percent: int = field(
        default_factory=lambda: safe_parse_int(
            "FRESHNESS_WARNING_PERCENT", 80, min_value=1, max_value=100
        )
    )
    freshness_check_interval_minutes: int = field(
        default_factory=lambda: safe_parse_int("FRESHNESS_CHECK_INTERVAL_MINUTES", 5, min_value=1)
    )

    # Snapshot/Rollback (Phase 5)
    snapshot_retention_count: int = field(
        default_factory=lambda: safe_parse_int("SNAPSHOT_RETENTION_COUNT", 10, min_value=1)
    )
    snapshot_retention_days: int = field(
        default_factory=lambda: safe_parse_int("SNAPSHOT_RETENTION_DAYS", 30, min_value=1)
    )
    snapshot_max_size_mb: int = field(
        default_factory=lambda: safe_parse_int("SNAPSHOT_MAX_SIZE_MB", 50, min_value=1)
    )
    snapshot_enabled: bool = field(default_factory=lambda: parse_bool("SNAPSHOT_ENABLED", True))

    # Multi-Sheet Sync (Phase 6)
    multi_sheet_enabled: bool = field(
        default_factory=lambda: parse_bool("MULTI_SHEET_ENABLED", False)
    )
    multi_sheet_targets: list["SheetTarget"] = field(default_factory=list)
    multi_sheet_parallel: bool = field(
        default_factory=lambda: parse_bool("MULTI_SHEET_PARALLEL", False)
    )

    # Reverse Sync (Phase 6)
    reverse_sync_enabled: bool = field(
        default_factory=lambda: parse_bool("REVERSE_SYNC_ENABLED", False)
    )

    # Worksheet Management
    worksheet_auto_create: bool = field(
        default_factory=lambda: parse_bool("WORKSHEET_AUTO_CREATE", False)
    )
    worksheet_default_rows: int = field(
        default_factory=lambda: safe_parse_int("WORKSHEET_DEFAULT_ROWS", 1000, min_value=1)
    )
    worksheet_default_cols: int = field(
        default_factory=lambda: safe_parse_int("WORKSHEET_DEFAULT_COLS", 26, min_value=1)
    )

    # Metadata Database Backend (Phase 2B)
    metadata_db_type: str = field(default_factory=lambda: os.getenv("METADATA_DB_TYPE", "sqlite"))
    metadata_db_url: str = field(default_factory=lambda: os.getenv("METADATA_DB_URL", ""))

    # Job Queue Backend (Phase 2B)
    job_queue_backend: str = field(default_factory=lambda: os.getenv("JOB_QUEUE_BACKEND", "sqlite"))
    redis_url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    redis_job_ttl_seconds: int = field(
        default_factory=lambda: safe_parse_int("REDIS_JOB_TTL_SECONDS", 86400, min_value=1)
    )

    # Distributed Worker (Phase 2B)
    worker_id: str = field(default_factory=lambda: os.getenv("WORKER_ID", ""))
    worker_heartbeat_seconds: int = field(
        default_factory=lambda: safe_parse_int("WORKER_HEARTBEAT_SECONDS", 30, min_value=1)
    )
    worker_steal_timeout_seconds: int = field(
        default_factory=lambda: safe_parse_int("WORKER_STEAL_TIMEOUT_SECONDS", 300, min_value=1)
    )

    # Agent Cleanup (Hybrid Agent Observability)
    agent_cleanup_interval_seconds: int = field(
        default_factory=lambda: safe_parse_int("AGENT_CLEANUP_INTERVAL_SECONDS", 60, min_value=10)
    )
    agent_stale_timeout_seconds: int = field(
        default_factory=lambda: safe_parse_int("AGENT_STALE_TIMEOUT_SECONDS", 300, min_value=30)
    )
    crash_report_retention_days: int = field(
        default_factory=lambda: safe_parse_int("CRASH_REPORT_RETENTION_DAYS", 30, min_value=1)
    )
    crash_report_max_size_kb: int = field(
        default_factory=lambda: safe_parse_int("CRASH_REPORT_MAX_SIZE_KB", 100, min_value=1)
    )

    # Billing Readiness (Phase 6)
    billing_enabled: bool = field(default_factory=lambda: parse_bool("BILLING_ENABLED", False))
    billing_webhook_secret: str = field(
        default_factory=lambda: os.getenv("BILLING_WEBHOOK_SECRET", "")
    )
    billing_portal_url: str = field(default_factory=lambda: os.getenv("BILLING_PORTAL_URL", ""))
    trial_period_days: int = field(
        default_factory=lambda: safe_parse_int("TRIAL_PERIOD_DAYS", 14, min_value=0)
    )

    # License Key Configuration
    # License validation uses RS256 (asymmetric) algorithm.
    # Only the public key is needed to verify signatures.
    license_key: str = field(default_factory=lambda: os.getenv("LICENSE_KEY", ""))
    # Custom RSA public key for license verification.
    # If not set, uses the embedded default public key in license.py.
    license_public_key: str = field(default_factory=lambda: os.getenv("LICENSE_PUBLIC_KEY", ""))
    # Grace period (in days) for expired licenses before reverting to FREE tier.
    license_offline_grace_days: int = field(
        default_factory=lambda: safe_parse_int("LICENSE_OFFLINE_GRACE_DAYS", 3, min_value=0)
    )

    # Query Result Caching (Tier 4)
    query_cache_enabled: bool = field(
        default_factory=lambda: parse_bool("QUERY_CACHE_ENABLED", False)
    )
    query_cache_ttl_seconds: int = field(
        default_factory=lambda: safe_parse_int("QUERY_CACHE_TTL_SECONDS", 300, min_value=1)
    )
    query_cache_backend: str = field(
        default_factory=lambda: os.getenv("QUERY_CACHE_BACKEND", "memory")
    )

    def __post_init__(self) -> None:
        """Post-initialization processing.

        Handles:
        - Tilde (~) expansion for service account file path (EC-44)
        - Worksheet name whitespace stripping (EC-43)
        - Keychain fallback for desktop mode
        """
        # EC-44 & EC-52: Expand tilde and environment variables in service account path
        # Handles ~, $HOME, ${HOME}, and other env vars
        original_path = self.service_account_file
        expanded = os.path.expandvars(original_path)  # EC-52: $HOME, ${HOME}
        expanded = os.path.expanduser(expanded)  # EC-44: ~
        if expanded != original_path:
            object.__setattr__(self, "service_account_file", expanded)
            # EC-52: Warn if path still contains unexpanded variables
            if "$" in expanded:
                import logging

                logging.getLogger(__name__).warning(
                    "CONFIG_126: SERVICE_ACCOUNT_FILE contains unexpanded variable: %s",
                    expanded,
                )

        # EC-43: Strip whitespace from worksheet name
        stripped_name = self.google_worksheet_name.strip()
        if stripped_name != self.google_worksheet_name:
            object.__setattr__(self, "google_worksheet_name", stripped_name)

        # EC-48: Resolve relative SQLite paths to absolute paths
        # Relative paths work interactively but fail in scheduled jobs with different CWD
        if self.db_type == "sqlite" and self.db_name:
            db_path = Path(self.db_name)
            # Only normalize if it's a relative path (not absolute)
            if not db_path.is_absolute() and not self.db_name.startswith(":"):
                # :memory: and other special SQLite paths start with :
                original_path = self.db_name
                absolute_path = str(db_path.resolve())
                if absolute_path != original_path:
                    object.__setattr__(self, "db_name", absolute_path)
                    # Store original path for warning message (used in logging)
                    object.__setattr__(self, "_sqlite_original_path", original_path)

        # Desktop mode keychain fallback
        try:
            from mysql_to_sheets.desktop.credentials import (
                CredentialManager,
                is_desktop_mode,
            )

            if not is_desktop_mode() or not CredentialManager.is_available():
                return

            # Keychain fallback for database credentials
            if not self.db_user:
                keychain_user = CredentialManager.retrieve("db_user")
                if keychain_user:
                    object.__setattr__(self, "db_user", keychain_user)

            if not self.db_password:
                keychain_password = CredentialManager.retrieve("db_password")
                if keychain_password:
                    object.__setattr__(self, "db_password", keychain_password)

            if not self.db_name:
                keychain_db_name = CredentialManager.retrieve("db_name")
                if keychain_db_name:
                    object.__setattr__(self, "db_name", keychain_db_name)

            if self.db_host == "localhost":
                keychain_host = CredentialManager.retrieve("db_host")
                if keychain_host:
                    object.__setattr__(self, "db_host", keychain_host)

            # Keychain fallback for Google Sheets credentials
            if not self.google_sheet_id:
                keychain_sheet_id = CredentialManager.retrieve("google_sheet_id")
                if keychain_sheet_id:
                    object.__setattr__(self, "google_sheet_id", keychain_sheet_id)

        except ImportError:
            # Desktop module not available (e.g., minimal install)
            pass

    def validate(self) -> list[str]:
        """Validate required configuration values.

        Validates:
        - Required fields (DB_USER, DB_PASSWORD, DB_NAME, GOOGLE_SHEET_ID, SQL_QUERY)
        - Service account file existence, readability, and validity
        - Placeholder value detection
        - Google Sheet ID format (not a wrong service URL)
        - Bulk missing fields detection (EC-36: suggests .env file issue)

        Returns:
            List of error messages (empty if valid).
        """
        errors = []
        missing_required_count = 0

        # Database validation (skip for sqlite which doesn't need user/password)
        if self.db_type != "sqlite":
            if not self.db_user:
                errors.append("DB_USER is required")
                missing_required_count += 1
            if not self.db_password:
                errors.append("DB_PASSWORD is required")
                missing_required_count += 1
        if not self.db_name:
            errors.append("DB_NAME is required")
            missing_required_count += 1

        # Google Sheets validation
        if not self.google_sheet_id:
            errors.append("GOOGLE_SHEET_ID is required")
            missing_required_count += 1
        else:
            # Check for wrong Google service URLs (EC-33)
            from mysql_to_sheets.core.sheets_utils import validate_google_url

            url_valid, url_error = validate_google_url(self.google_sheet_id)
            if not url_valid and url_error:
                errors.append(url_error)

        # Service account file validation
        service_account_path = Path(self.service_account_file)
        if not service_account_path.exists():
            errors.append(f"SERVICE_ACCOUNT_FILE not found: {self.service_account_file}")
        else:
            # Check readability first (EC-40)
            readable, readable_error = check_service_account_readable(self.service_account_file)
            if not readable and readable_error:
                errors.append(readable_error)
            else:
                # Validate JSON format (EC-31)
                json_valid, json_error = validate_service_account_json(self.service_account_file)
                if not json_valid and json_error:
                    errors.append(json_error)
                else:
                    # Validate structure (EC-32) - only if JSON is valid
                    struct_valid, struct_error = validate_service_account_structure(
                        self.service_account_file
                    )
                    if not struct_valid and struct_error:
                        errors.append(struct_error)

        # Query validation
        if not self.sql_query:
            errors.append("SQL_QUERY is required")
            missing_required_count += 1
        else:
            # EC-42: Check if SQL query looks like a file path
            file_path_error = detect_sql_file_path(self.sql_query)
            if file_path_error:
                errors.append(file_path_error)

            # EC-45: Check if SQL query contains only comments
            stripped_query = strip_sql_comments(self.sql_query)
            if not stripped_query and self.sql_query.strip():
                errors.append(
                    "SQL_QUERY contains only comments with no executable SQL. "
                    "Add a SELECT statement after the comments, or remove the comment markers."
                )

        # EC-36: Detect bulk missing fields (likely .env file issue)
        # If 4+ required fields are missing, suggest .env file problem
        if missing_required_count >= 4:
            errors.insert(
                0,
                "Multiple required configuration fields are missing. "
                "This usually means the .env file is missing or empty.\n\n"
                "To fix:\n"
                "  1. Copy the example file: cp .env.example .env\n"
                "  2. Edit .env with your database and Google Sheets credentials\n\n"
                "Or run: mysql-to-sheets quickstart  — for interactive setup",
            )

        # Placeholder value detection (EC-34)
        placeholders = check_placeholders(
            self.db_user,
            self.db_password,
            self.db_name,
            self.google_sheet_id,
        )
        if placeholders:
            errors.append(
                f"Placeholder values detected in: {', '.join(placeholders)}. "
                "Please replace these with your actual values in the .env file."
            )

        # EC-50: SSL certificate file validation for PostgreSQL/MySQL
        # Validate before connection attempt to give clear error instead of cryptic timeout
        if self.db_ssl_ca:
            ssl_path = Path(os.path.expanduser(self.db_ssl_ca))
            if not ssl_path.exists():
                errors.append(
                    f"SSL certificate file not found: {self.db_ssl_ca}. "
                    "Verify the DB_SSL_CA path in your .env file points to an existing certificate file."
                )
            elif not ssl_path.is_file():
                errors.append(
                    f"SSL certificate path is a directory, not a file: {self.db_ssl_ca}. "
                    "DB_SSL_CA must point to a certificate file (e.g., ca-cert.pem)."
                )
            elif not os.access(ssl_path, os.R_OK):
                errors.append(
                    f"SSL certificate file exists but cannot be read: {self.db_ssl_ca}. "
                    "Check file permissions (chmod 644 on Linux/macOS)."
                )

        # Validate that verify-ca/verify-full SSL modes require a CA certificate
        if self.db_ssl_mode in ("verify-ca", "verify-full") and not self.db_ssl_ca:
            errors.append(
                f"DB_SSL_MODE='{self.db_ssl_mode}' requires DB_SSL_CA to be set. "
                "Provide the path to your CA certificate file."
            )

        return errors

    def validate_or_raise(self) -> None:
        """Validate configuration and raise ConfigError if invalid.

        Raises:
            ConfigError: If configuration is invalid.
        """
        errors = self.validate()
        if errors:
            raise ConfigError(
                message="Invalid configuration",
                missing_fields=errors,
            )

    def is_valid(self) -> bool:
        """Check if configuration is valid.

        Returns:
            True if configuration is valid.
        """
        return len(self.validate()) == 0

    def with_overrides(self, **kwargs: Any) -> "Config":
        """Create a new Config instance with overridden values.

        Args:
            **kwargs: Fields to override.

        Returns:
            New Config instance with overrides applied.

        Example:
            >>> config = get_config()
            >>> new_config = config.with_overrides(
            ...     google_sheet_id="abc123",
            ...     sql_query="SELECT * FROM users"
            ... )
        """
        return replace(self, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create a Config instance from a dictionary.

        Args:
            data: Dictionary with configuration values.

        Returns:
            Config instance populated from dictionary.

        Example:
            >>> config = Config.from_dict({
            ...     "db_host": "localhost",
            ...     "db_port": 3306,
            ...     "google_sheet_id": "abc123"
            ... })
        """
        # Filter to only known fields
        known_fields = {
            # Database connection
            "db_type",
            "db_host",
            "db_port",
            "db_user",
            "db_password",
            "db_name",
            "db_connect_timeout",
            "db_read_timeout",
            "db_pool_enabled",
            "db_pool_size",
            "db_ssl_mode",
            "db_ssl_ca",
            # Google Sheets
            "google_sheet_id",
            "google_worksheet_name",
            "service_account_file",
            "sheets_timeout",
            # Query
            "sql_query",
            # Logging
            "log_file",
            "log_level",
            "log_format",
            "log_pii_masking",
            "log_max_bytes",
            "log_backup_count",
            # Retry & Circuit Breaker
            "retry_max_attempts",
            "retry_base_delay",
            "circuit_breaker_enabled",
            # History & Metrics
            "history_backend",
            "history_db_path",
            "metrics_enabled",
            # Security
            "api_auth_enabled",
            "api_keys_db_path",
            "rate_limit_enabled",
            "rate_limit_rpm",
            "cors_allowed_origins",
            "sql_validation_enabled",
            # Sync Modes
            "sync_mode",
            "sync_chunk_size",
            "incremental_enabled",
            "incremental_timestamp_column",
            # Atomic Streaming
            "streaming_atomic_enabled",
            "streaming_staging_prefix",
            "streaming_preserve_gid",
            "streaming_verification_enabled",
            "streaming_staging_max_age_minutes",
            # Column Mapping
            "column_mapping_enabled",
            "column_mapping",
            "column_order",
            "column_case",
            "column_strip_prefix",
            "column_strip_suffix",
            # Notifications
            "notify_on_success",
            "notify_on_failure",
            "smtp_host",
            "smtp_port",
            "smtp_user",
            "smtp_password",
            "smtp_from",
            "smtp_to",
            "smtp_use_tls",
            "slack_webhook_url",
            "notification_webhook_url",
            # Scheduler
            "scheduler_enabled",
            "scheduler_db_path",
            "scheduler_timezone",
            # JWT Authentication (Phase 3)
            "jwt_secret_key",
            "jwt_access_token_expire_minutes",
            "jwt_refresh_token_expire_days",
            # Session Configuration (Phase 3)
            "session_secret_key",
            "session_lifetime_hours",
            # Password Configuration (Phase 3)
            "password_min_length",
            # Lockout Configuration
            "lockout_max_attempts",
            "lockout_duration_minutes",
            "lockout_window_minutes",
            "lockout_fail_open",
            # RBAC Defaults (Phase 3)
            "default_user_role",
            "default_org_max_users",
            "default_org_max_configs",
            # Webhook Configuration (Phase 3)
            "webhook_timeout_seconds",
            "webhook_max_retries",
            "webhook_disable_after_failures",
            # Multi-tenant Database (Phase 3)
            "tenant_db_path",
            # Audit Logging (Phase 4)
            "audit_retention_days",
            # Job Queue (Phase 4)
            "job_queue_concurrency",
            "job_max_attempts",
            "job_retry_delay_seconds",
            "job_timeout_seconds",
            # Freshness/SLA Tracking (Phase 4)
            "default_freshness_sla_minutes",
            "freshness_warning_percent",
            "freshness_check_interval_minutes",
            # Snapshot/Rollback (Phase 5)
            "snapshot_retention_count",
            "snapshot_retention_days",
            "snapshot_max_size_mb",
            "snapshot_enabled",
            # Worksheet Management
            "worksheet_auto_create",
            "worksheet_default_rows",
            "worksheet_default_cols",
            # Metadata Database Backend (Phase 2B)
            "metadata_db_type",
            "metadata_db_url",
            # Job Queue Backend (Phase 2B)
            "job_queue_backend",
            "redis_url",
            "redis_job_ttl_seconds",
            # Distributed Worker (Phase 2B)
            "worker_id",
            "worker_heartbeat_seconds",
            "worker_steal_timeout_seconds",
            # Agent Cleanup (Hybrid Agent Observability)
            "agent_cleanup_interval_seconds",
            "agent_stale_timeout_seconds",
            "crash_report_retention_days",
            "crash_report_max_size_kb",
            # Billing Readiness (Phase 6)
            "billing_enabled",
            "billing_webhook_secret",
            "billing_portal_url",
            "trial_period_days",
            # License Key Configuration
            "license_key",
            "license_public_key",
            "license_offline_grace_days",
        }
        filtered = {k: v for k, v in data.items() if k in known_fields}

        # Create base config (loads from env)
        config = cls()

        # Override with provided values
        if filtered:
            config = config.with_overrides(**filtered)

        return config

    def __repr__(self) -> str:
        """String representation with masked secrets."""
        return (
            f"Config(db_host={self.db_host!r}, db_port={self.db_port}, "
            f"db_user={self.db_user!r}, db_password='***', db_name={self.db_name!r}, "
            f"google_sheet_id={self.google_sheet_id!r}, "
            f"google_worksheet_name={self.google_worksheet_name!r})"
        )
