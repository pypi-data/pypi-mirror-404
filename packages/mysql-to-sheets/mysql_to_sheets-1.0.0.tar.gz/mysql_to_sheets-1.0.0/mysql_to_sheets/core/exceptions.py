"""Custom exceptions for MySQL to Google Sheets sync.

Extraction target: ``tla-errors`` standalone package.
This module has zero internal imports and depends only on the standard library.
See STANDALONE_PROJECTS.md for extraction details.
"""

from enum import Enum
from typing import Any


class ErrorCode:
    """Standardized error codes for troubleshooting and diagnostics.

    Error codes follow the format: CATEGORY_NNN where:
    - CATEGORY: Short identifier (CONFIG, DB, SHEETS, etc.)
    - NNN: Three-digit number within the category

    Error codes enable:
    - Quick identification of error types
    - Consistent error reporting across CLI, API, and Dashboard
    - Easy lookup of remediation steps
    """

    # Config errors (1xx)
    CONFIG_MISSING_FIELD = "CONFIG_101"
    CONFIG_INVALID_VALUE = "CONFIG_102"
    CONFIG_FILE_NOT_FOUND = "CONFIG_103"
    CONFIG_PARSE_ERROR = "CONFIG_104"
    CONFIG_UNSAFE_SQL = "CONFIG_105"
    CONFIG_RAGGED_ROWS = "CONFIG_106"
    CONFIG_NON_SELECT_QUERY = "CONFIG_107"
    CONFIG_DUPLICATE_TARGETS = "CONFIG_108"
    CONFIG_FILTER_MISSING_COLUMN = "CONFIG_109"
    CONFIG_SERVICE_ACCOUNT_INVALID_JSON = "CONFIG_110"
    CONFIG_SERVICE_ACCOUNT_MISSING_FIELDS = "CONFIG_111"
    CONFIG_WRONG_GOOGLE_SERVICE_URL = "CONFIG_112"
    CONFIG_PLACEHOLDER_VALUES = "CONFIG_113"
    CONFIG_ENV_FILE_ISSUE = "CONFIG_114"  # Multiple required fields missing
    CONFIG_QUERY_NO_RESULTS = "CONFIG_115"  # Query returned zero rows
    CONFIG_PORT_MISMATCH = "CONFIG_116"  # Database port doesn't match type
    CONFIG_SERVICE_ACCOUNT_NOT_READABLE = "CONFIG_117"  # File exists but not readable
    CONFIG_SERVICE_ACCOUNT_BOM = "CONFIG_118"  # UTF-8 BOM in JSON file
    CONFIG_SQL_FILE_PATH = "CONFIG_119"  # SQL query looks like file path
    CONFIG_WORKSHEET_WHITESPACE = "CONFIG_120"  # Worksheet name has whitespace (warning)
    CONFIG_PATH_TILDE = "CONFIG_121"  # Path uses tilde (~) expansion needed
    CONFIG_SQL_ONLY_COMMENTS = "CONFIG_122"  # SQL query contains only comments
    CONFIG_INVALID_BOOLEAN = "CONFIG_123"  # Invalid boolean env var value
    CONFIG_SQLITE_RELATIVE_PATH = "CONFIG_124"  # SQLite relative path (warning)
    CONFIG_SSL_CERT_NOT_FOUND = "CONFIG_125"  # SSL certificate file not found
    CONFIG_PATH_UNEXPANDED_VAR = "CONFIG_126"  # Path contains unexpanded $VAR
    CONFIG_DRIVER_MISSING = "CONFIG_127"  # Required database driver not installed

    # Database errors (2xx)
    DB_CONNECTION_REFUSED = "DB_201"
    DB_AUTH_FAILED = "DB_202"
    DB_QUERY_ERROR = "DB_203"
    DB_TIMEOUT = "DB_204"
    DB_NOT_FOUND = "DB_205"
    DB_UNSUPPORTED = "DB_206"
    DB_CONNECTION_LOST = "DB_207"

    # Sheets errors (3xx)
    SHEETS_AUTH_FAILED = "SHEETS_301"
    SHEETS_NOT_FOUND = "SHEETS_302"
    SHEETS_PERMISSION_DENIED = "SHEETS_303"
    SHEETS_RATE_LIMITED = "SHEETS_304"
    SHEETS_WORKSHEET_NOT_FOUND = "SHEETS_305"
    SHEETS_API_ERROR = "SHEETS_306"
    SHEETS_COLUMN_LIMIT_EXCEEDED = "SHEETS_309"
    SHEETS_ROW_LIMIT_EXCEEDED = "SHEETS_310"
    SHEETS_CELL_LIMIT_EXCEEDED = "SHEETS_311"
    SHEETS_CELL_SIZE_EXCEEDED = "SHEETS_312"
    SHEETS_APPEND_HEADER_MISMATCH = "SHEETS_313"
    SHEETS_API_NOT_ENABLED = "SHEETS_314"  # Google Sheets API not enabled in project

    # Scheduler errors (4xx)
    SCHEDULER_JOB_NOT_FOUND = "SCHEDULER_401"
    SCHEDULER_INVALID_CRON = "SCHEDULER_402"
    SCHEDULER_START_FAILED = "SCHEDULER_403"

    # Auth errors (5xx)
    AUTH_INVALID_CREDENTIALS = "AUTH_501"
    AUTH_TOKEN_EXPIRED = "AUTH_502"
    AUTH_TOKEN_INVALID = "AUTH_503"
    AUTH_PERMISSION_DENIED = "AUTH_504"
    AUTH_RATE_LIMITED = "AUTH_505"

    # Organization errors (6xx)
    ORG_NOT_FOUND = "ORG_601"
    ORG_INACTIVE = "ORG_602"
    ORG_QUOTA_EXCEEDED = "ORG_603"

    # Webhook errors (7xx)
    WEBHOOK_DELIVERY_FAILED = "WEBHOOK_701"
    WEBHOOK_NOT_FOUND = "WEBHOOK_702"
    WEBHOOK_INVALID_URL = "WEBHOOK_703"

    # Notification errors (8xx)
    NOTIFY_SMTP_FAILED = "NOTIFY_801"
    NOTIFY_SLACK_FAILED = "NOTIFY_802"
    NOTIFY_WEBHOOK_FAILED = "NOTIFY_803"

    # Tier/quota errors (9xx)
    TIER_UPGRADE_REQUIRED = "TIER_901"
    TIER_QUOTA_EXCEEDED = "TIER_902"
    TIER_FEATURE_DISABLED = "TIER_903"

    # Retry errors (10xx)
    RETRY_EXHAUSTED = "RETRY_1001"
    CIRCUIT_OPEN = "RETRY_1002"

    # License errors (11xx)
    LICENSE_MISSING = "LICENSE_001"
    LICENSE_INVALID = "LICENSE_002"
    LICENSE_EXPIRED = "LICENSE_003"
    LICENSE_TIER_REQUIRED = "LICENSE_004"

    # Schema evolution errors (12xx)
    SCHEMA_STRICT_VIOLATION = "SCHEMA_001"  # Strict policy with any schema change
    SCHEMA_ADDITIVE_VIOLATION = "SCHEMA_002"  # Additive policy with removed columns

    # PII errors (13xx)
    PII_DETECTED = "PII_001"  # PII detected, acknowledgment required
    PII_ACK_REQUIRED = "PII_002"  # Acknowledgment required but not provided
    PII_TRANSFORM_FAILED = "PII_003"  # Transformation failed
    PII_POLICY_BLOCKED = "PII_004"  # Org policy blocks operation
    PII_INVALID_TRANSFORM = "PII_005"  # Invalid transform type


class ErrorCategory(str, Enum):
    """Error categories for classification and handling.

    Categories help determine:
    - Whether retrying may help (transient)
    - What kind of fix is needed (config, permission, etc.)
    - Alert severity and escalation
    """

    TRANSIENT = "transient"  # Temporary issue, retry may help
    PERMANENT = "permanent"  # Requires code/config fix
    PERMISSION = "permission"  # Access/authorization issue
    QUOTA = "quota"  # Rate limit or quota exceeded
    CONFIG = "config"  # Configuration issue


# Mapping of error codes to their categories
ERROR_CATEGORIES: dict[str, ErrorCategory] = {
    # Config errors - permanent (need fix)
    ErrorCode.CONFIG_MISSING_FIELD: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_INVALID_VALUE: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_FILE_NOT_FOUND: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_PARSE_ERROR: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_UNSAFE_SQL: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_RAGGED_ROWS: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_NON_SELECT_QUERY: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_DUPLICATE_TARGETS: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_FILTER_MISSING_COLUMN: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_SERVICE_ACCOUNT_INVALID_JSON: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_SERVICE_ACCOUNT_MISSING_FIELDS: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_WRONG_GOOGLE_SERVICE_URL: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_PLACEHOLDER_VALUES: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_ENV_FILE_ISSUE: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_QUERY_NO_RESULTS: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_PORT_MISMATCH: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_SERVICE_ACCOUNT_NOT_READABLE: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_SERVICE_ACCOUNT_BOM: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_SQL_FILE_PATH: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_WORKSHEET_WHITESPACE: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_PATH_TILDE: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_SQL_ONLY_COMMENTS: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_INVALID_BOOLEAN: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_SQLITE_RELATIVE_PATH: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_SSL_CERT_NOT_FOUND: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_PATH_UNEXPANDED_VAR: ErrorCategory.CONFIG,
    ErrorCode.CONFIG_DRIVER_MISSING: ErrorCategory.CONFIG,
    # Database errors - mixed
    ErrorCode.DB_CONNECTION_REFUSED: ErrorCategory.TRANSIENT,
    ErrorCode.DB_AUTH_FAILED: ErrorCategory.PERMISSION,
    ErrorCode.DB_QUERY_ERROR: ErrorCategory.PERMANENT,
    ErrorCode.DB_TIMEOUT: ErrorCategory.TRANSIENT,
    ErrorCode.DB_NOT_FOUND: ErrorCategory.CONFIG,
    ErrorCode.DB_UNSUPPORTED: ErrorCategory.PERMANENT,
    ErrorCode.DB_CONNECTION_LOST: ErrorCategory.TRANSIENT,
    # Sheets errors - mixed
    ErrorCode.SHEETS_AUTH_FAILED: ErrorCategory.PERMISSION,
    ErrorCode.SHEETS_NOT_FOUND: ErrorCategory.CONFIG,
    ErrorCode.SHEETS_PERMISSION_DENIED: ErrorCategory.PERMISSION,
    ErrorCode.SHEETS_RATE_LIMITED: ErrorCategory.QUOTA,
    ErrorCode.SHEETS_WORKSHEET_NOT_FOUND: ErrorCategory.CONFIG,
    ErrorCode.SHEETS_API_ERROR: ErrorCategory.TRANSIENT,
    ErrorCode.SHEETS_COLUMN_LIMIT_EXCEEDED: ErrorCategory.QUOTA,
    ErrorCode.SHEETS_ROW_LIMIT_EXCEEDED: ErrorCategory.QUOTA,
    ErrorCode.SHEETS_CELL_LIMIT_EXCEEDED: ErrorCategory.QUOTA,
    ErrorCode.SHEETS_CELL_SIZE_EXCEEDED: ErrorCategory.QUOTA,
    ErrorCode.SHEETS_APPEND_HEADER_MISMATCH: ErrorCategory.CONFIG,
    ErrorCode.SHEETS_API_NOT_ENABLED: ErrorCategory.CONFIG,
    # Scheduler errors
    ErrorCode.SCHEDULER_JOB_NOT_FOUND: ErrorCategory.CONFIG,
    ErrorCode.SCHEDULER_INVALID_CRON: ErrorCategory.CONFIG,
    ErrorCode.SCHEDULER_START_FAILED: ErrorCategory.TRANSIENT,
    # Auth errors
    ErrorCode.AUTH_INVALID_CREDENTIALS: ErrorCategory.PERMISSION,
    ErrorCode.AUTH_TOKEN_EXPIRED: ErrorCategory.TRANSIENT,
    ErrorCode.AUTH_TOKEN_INVALID: ErrorCategory.PERMISSION,
    ErrorCode.AUTH_PERMISSION_DENIED: ErrorCategory.PERMISSION,
    ErrorCode.AUTH_RATE_LIMITED: ErrorCategory.QUOTA,
    # Organization errors
    ErrorCode.ORG_NOT_FOUND: ErrorCategory.CONFIG,
    ErrorCode.ORG_INACTIVE: ErrorCategory.PERMISSION,
    ErrorCode.ORG_QUOTA_EXCEEDED: ErrorCategory.QUOTA,
    # Webhook errors
    ErrorCode.WEBHOOK_DELIVERY_FAILED: ErrorCategory.TRANSIENT,
    ErrorCode.WEBHOOK_NOT_FOUND: ErrorCategory.CONFIG,
    ErrorCode.WEBHOOK_INVALID_URL: ErrorCategory.CONFIG,
    # Notification errors
    ErrorCode.NOTIFY_SMTP_FAILED: ErrorCategory.TRANSIENT,
    ErrorCode.NOTIFY_SLACK_FAILED: ErrorCategory.TRANSIENT,
    ErrorCode.NOTIFY_WEBHOOK_FAILED: ErrorCategory.TRANSIENT,
    # Tier errors
    ErrorCode.TIER_UPGRADE_REQUIRED: ErrorCategory.QUOTA,
    ErrorCode.TIER_QUOTA_EXCEEDED: ErrorCategory.QUOTA,
    ErrorCode.TIER_FEATURE_DISABLED: ErrorCategory.QUOTA,
    # Retry errors
    ErrorCode.RETRY_EXHAUSTED: ErrorCategory.TRANSIENT,
    ErrorCode.CIRCUIT_OPEN: ErrorCategory.TRANSIENT,
    # License errors
    ErrorCode.LICENSE_MISSING: ErrorCategory.PERMISSION,
    ErrorCode.LICENSE_INVALID: ErrorCategory.PERMISSION,
    ErrorCode.LICENSE_EXPIRED: ErrorCategory.PERMISSION,
    ErrorCode.LICENSE_TIER_REQUIRED: ErrorCategory.QUOTA,
    # Schema evolution errors
    ErrorCode.SCHEMA_STRICT_VIOLATION: ErrorCategory.CONFIG,
    ErrorCode.SCHEMA_ADDITIVE_VIOLATION: ErrorCategory.CONFIG,
    # PII errors
    ErrorCode.PII_DETECTED: ErrorCategory.PERMISSION,
    ErrorCode.PII_ACK_REQUIRED: ErrorCategory.PERMISSION,
    ErrorCode.PII_TRANSFORM_FAILED: ErrorCategory.PERMANENT,
    ErrorCode.PII_POLICY_BLOCKED: ErrorCategory.PERMISSION,
    ErrorCode.PII_INVALID_TRANSFORM: ErrorCategory.CONFIG,
}


# Remediation hints for each error code
REMEDIATION_HINTS: dict[str, str] = {
    # Config errors
    ErrorCode.CONFIG_MISSING_FIELD: "Run: mysql-to-sheets validate  — to see which fields are missing from .env",
    ErrorCode.CONFIG_INVALID_VALUE: "Run: mysql-to-sheets validate  — to identify the invalid value and expected format",
    ErrorCode.CONFIG_FILE_NOT_FOUND: "Run: cp .env.example .env  — then edit .env with your settings",
    ErrorCode.CONFIG_PARSE_ERROR: "Run: mysql-to-sheets validate  — to identify syntax errors in your config file",
    ErrorCode.CONFIG_UNSAFE_SQL: "Remove dangerous statements (DROP, DELETE, TRUNCATE, etc.) from your SQL_QUERY",
    ErrorCode.CONFIG_RAGGED_ROWS: (
        "Your SQL query returns rows with inconsistent column counts. "
        "Check for NULL columns or use COALESCE() to ensure consistent row lengths"
    ),
    ErrorCode.CONFIG_NON_SELECT_QUERY: (
        "SQL_QUERY must be a SELECT statement. "
        "INSERT/UPDATE/DELETE queries don't return data and would clear your sheet"
    ),
    ErrorCode.CONFIG_DUPLICATE_TARGETS: (
        "Each multi-sheet target must have a unique sheet_id + worksheet_name combination. "
        "Check your multi_sheet_targets configuration for duplicates."
    ),
    ErrorCode.CONFIG_FILTER_MISSING_COLUMN: (
        "Row filter references a column that doesn't exist after column filtering. "
        "Ensure row_filter only uses columns available in column_filter."
    ),
    ErrorCode.CONFIG_SERVICE_ACCOUNT_INVALID_JSON: (
        "The service account file contains invalid JSON. "
        "Re-download the JSON key from Google Cloud Console > IAM & Admin > Service Accounts. "
        "Ensure the file wasn't truncated or corrupted during download."
    ),
    ErrorCode.CONFIG_SERVICE_ACCOUNT_MISSING_FIELDS: (
        "The service account file is missing required fields. "
        "You may have downloaded OAuth2 credentials or an API key instead of a Service Account key. "
        "Go to Google Cloud Console > IAM & Admin > Service Accounts > Keys > Add Key > Create new key (JSON)."
    ),
    ErrorCode.CONFIG_WRONG_GOOGLE_SERVICE_URL: (
        "The URL is for a different Google service (Docs, Forms, or Slides), not Google Sheets. "
        "Open your spreadsheet at docs.google.com/spreadsheets and copy that URL instead."
    ),
    ErrorCode.CONFIG_PLACEHOLDER_VALUES: (
        "Your configuration contains placeholder values that need to be replaced with real values. "
        "Edit your .env file and replace values like 'your_password', '<your_database>', 'CHANGE_ME', etc."
    ),
    ErrorCode.CONFIG_ENV_FILE_ISSUE: (
        "Multiple required configuration fields are missing. This usually means "
        "the .env file is missing or empty.\n\n"
        "To fix:\n"
        "  1. Copy the example file: cp .env.example .env\n"
        "  2. Edit .env with your database and Google Sheets credentials\n\n"
        "Or run: mysql-to-sheets quickstart  — for interactive setup"
    ),
    ErrorCode.CONFIG_QUERY_NO_RESULTS: (
        "Your SQL query executed successfully but returned 0 rows. "
        "This usually means:\n"
        "  1. The WHERE clause filtered out all data\n"
        "  2. The table is empty\n"
        "  3. The table name has different capitalization\n\n"
        "Try: SELECT * FROM your_table LIMIT 10  (to verify data exists)"
    ),
    ErrorCode.CONFIG_PORT_MISMATCH: (
        "The database port doesn't match the expected default for your database type. "
        "Check DB_PORT in your .env file.\n\n"
        "Default ports: MySQL=3306, PostgreSQL=5432, SQL Server=1433"
    ),
    ErrorCode.CONFIG_SERVICE_ACCOUNT_NOT_READABLE: (
        "Service account file exists but cannot be read due to file permissions.\n\n"
        "To fix on Linux/macOS:\n"
        "  chmod 644 /path/to/service_account.json\n\n"
        "Or move to a user-writable location:\n"
        "  cp /path/to/service_account.json ./service_account.json"
    ),
    ErrorCode.CONFIG_SERVICE_ACCOUNT_BOM: (
        "Service account file has UTF-8 BOM (Byte Order Mark). "
        "This is common when editing with Windows Notepad. "
        "Open the file in a text editor and save as 'UTF-8' (without BOM), "
        "or re-download from Google Cloud Console."
    ),
    ErrorCode.CONFIG_SQL_FILE_PATH: (
        "SQL_QUERY appears to be a file path rather than SQL code.\n\n"
        "To load SQL from a file, read it first:\n"
        "  SQL_QUERY=$(cat /path/to/query.sql)\n\n"
        "Or in Python:\n"
        "  with open('query.sql') as f: query = f.read()"
    ),
    ErrorCode.CONFIG_WORKSHEET_WHITESPACE: (
        "Worksheet name contained leading or trailing whitespace. "
        "This is usually from copy-paste. "
        "The whitespace has been automatically removed."
    ),
    ErrorCode.CONFIG_PATH_TILDE: (
        "File path used tilde (~) which requires expansion. "
        "The path has been automatically expanded to your home directory."
    ),
    ErrorCode.CONFIG_SQL_ONLY_COMMENTS: (
        "SQL_QUERY contains only comments with no executable SQL. "
        "Add a SELECT statement after the comments, or remove the comment markers."
    ),
    ErrorCode.CONFIG_INVALID_BOOLEAN: (
        "Invalid boolean value for environment variable. "
        "Accepted truthy values: true, 1, yes, on, enabled. "
        "Accepted falsy values: false, 0, no, off, disabled, (empty string)."
    ),
    ErrorCode.CONFIG_SQLITE_RELATIVE_PATH: (
        "SQLite database path is relative (resolved to absolute). "
        "For scheduled syncs or cron jobs, use an absolute path to avoid "
        "failures when the working directory differs.\n\n"
        "Example: DB_NAME=/home/user/data/mydb.sqlite"
    ),
    ErrorCode.CONFIG_SSL_CERT_NOT_FOUND: (
        "SSL certificate file specified in DB_SSL_CA does not exist or is not readable.\n\n"
        "To fix:\n"
        "  1. Verify the file path: ls -la /path/to/cert.pem\n"
        "  2. Check file permissions: chmod 644 /path/to/cert.pem\n"
        "  3. Ensure DB_SSL_CA contains an absolute path"
    ),
    ErrorCode.CONFIG_PATH_UNEXPANDED_VAR: (
        "Path contains an environment variable that was not expanded. "
        "Ensure the variable is defined in your environment.\n\n"
        "Example: Instead of $HOME/db.sqlite, use ~/db.sqlite or /Users/you/db.sqlite"
    ),
    ErrorCode.CONFIG_DRIVER_MISSING: (
        "Required database driver is not installed.\n\n"
        "Install the appropriate driver for your database type:\n"
        "  PostgreSQL: pip install mysql-to-sheets[postgres]\n"
        "  SQL Server: pip install mysql-to-sheets[mssql]\n"
        "  Redis:      pip install mysql-to-sheets[redis]\n"
        "  All:        pip install mysql-to-sheets[all]"
    ),
    # Database errors
    ErrorCode.DB_CONNECTION_REFUSED: (
        "Run: mysql-to-sheets test-db --diagnose  — "
        "to check DB_HOST, DB_PORT, and server status"
    ),
    ErrorCode.DB_AUTH_FAILED: (
        "Run: mysql-to-sheets test-db --diagnose  — "
        "to verify DB_USER and DB_PASSWORD in .env"
    ),
    ErrorCode.DB_QUERY_ERROR: "Run: mysql-to-sheets sync --dry-run  — to validate SQL syntax without pushing data",
    ErrorCode.DB_TIMEOUT: (
        "Run: mysql-to-sheets test-db --diagnose  — "
        "try adding LIMIT to your query or increase DB_READ_TIMEOUT in .env"
    ),
    ErrorCode.DB_NOT_FOUND: "Run: mysql-to-sheets test-db --diagnose  — verify DB_NAME in .env matches an existing database",
    ErrorCode.DB_UNSUPPORTED: "Run: pip install mysql-to-sheets[postgres]  — or [mssql] for the required driver",
    ErrorCode.DB_CONNECTION_LOST: "Run: mysql-to-sheets test-db --diagnose  — transient network issue, retry may succeed",
    # Sheets errors
    ErrorCode.SHEETS_AUTH_FAILED: (
        "Run: mysql-to-sheets test-sheets --diagnose  — "
        "verify SERVICE_ACCOUNT_FILE path and re-download JSON from Google Cloud Console if needed"
    ),
    ErrorCode.SHEETS_NOT_FOUND: (
        "Run: mysql-to-sheets test-sheets --diagnose  — "
        "verify GOOGLE_SHEET_ID matches the spreadsheet URL"
    ),
    ErrorCode.SHEETS_PERMISSION_DENIED: (
        "Run: mysql-to-sheets test-sheets --diagnose  — "
        "share the Google Sheet with the service account email (client_email in service_account.json)"
    ),
    ErrorCode.SHEETS_RATE_LIMITED: "Wait 60 seconds and retry. Run: mysql-to-sheets sync  — to try again",
    ErrorCode.SHEETS_WORKSHEET_NOT_FOUND: (
        "Run: mysql-to-sheets sync --create-worksheet  — "
        "to auto-create the missing tab, or check GOOGLE_WORKSHEET_NAME in .env"
    ),
    ErrorCode.SHEETS_API_ERROR: "Run: mysql-to-sheets test-sheets --diagnose  — temporary Google API issue, retry may succeed",
    ErrorCode.SHEETS_COLUMN_LIMIT_EXCEEDED: "Reduce columns in your SQL query (max 18,278 columns)",
    ErrorCode.SHEETS_ROW_LIMIT_EXCEEDED: "Use streaming mode with smaller chunks (max 10M rows)",
    ErrorCode.SHEETS_CELL_LIMIT_EXCEEDED: "Use streaming mode or reduce columns/rows (max 10M cells total)",
    ErrorCode.SHEETS_CELL_SIZE_EXCEEDED: "Truncate large TEXT columns using SUBSTRING() in your query (max 50,000 chars per cell)",
    ErrorCode.SHEETS_APPEND_HEADER_MISMATCH: (
        "In append mode, columns must match existing sheet headers. "
        "Use replace mode or ensure your query columns match the sheet. "
        "Run: mysql-to-sheets sync --mode=replace  — to overwrite with new headers"
    ),
    ErrorCode.SHEETS_API_NOT_ENABLED: (
        "The Google Sheets API is not enabled in your Google Cloud project.\n\n"
        "To enable it:\n"
        "  1. Go to: https://console.cloud.google.com/apis/library/sheets.googleapis.com\n"
        "  2. Select your project from the dropdown\n"
        "  3. Click 'Enable'\n"
        "  4. Wait 1-2 minutes, then re-run: mysql-to-sheets test-sheets"
    ),
    # Scheduler errors
    ErrorCode.SCHEDULER_JOB_NOT_FOUND: "Run: mysql-to-sheets schedule list  — to see available schedule IDs",
    ErrorCode.SCHEDULER_INVALID_CRON: (
        "Use format: 'minute hour day month weekday'. "
        "Example: mysql-to-sheets schedule add --cron='0 6 * * *'"
    ),
    ErrorCode.SCHEDULER_START_FAILED: "Run: mysql-to-sheets diagnose  — to check scheduler configuration and logs",
    # Auth errors
    ErrorCode.AUTH_INVALID_CREDENTIALS: "Verify your email and password. Run: mysql-to-sheets user whoami  — to check current user",
    ErrorCode.AUTH_TOKEN_EXPIRED: "Re-authenticate: POST /api/v1/auth/login  — to get a new token",
    ErrorCode.AUTH_TOKEN_INVALID: "Re-authenticate: POST /api/v1/auth/login  — token is malformed or tampered",
    ErrorCode.AUTH_PERMISSION_DENIED: "Run: mysql-to-sheets user whoami  — to check your role and permissions",
    ErrorCode.AUTH_RATE_LIMITED: "Wait 15 minutes before retrying. Account is temporarily locked after too many failed attempts",
    # Organization errors
    ErrorCode.ORG_NOT_FOUND: "Run: mysql-to-sheets org list  — to see available organizations and their slugs",
    ErrorCode.ORG_INACTIVE: "Contact your organization administrator to reactivate the organization",
    ErrorCode.ORG_QUOTA_EXCEEDED: "Run: mysql-to-sheets tier usage  — to see current usage. Upgrade plan or remove unused items",
    # Webhook errors
    ErrorCode.WEBHOOK_DELIVERY_FAILED: "Run: mysql-to-sheets webhook test --id=ID  — to test the endpoint. Check URL accessibility",
    ErrorCode.WEBHOOK_NOT_FOUND: "Run: mysql-to-sheets webhook list  — to see available webhook subscriptions",
    ErrorCode.WEBHOOK_INVALID_URL: "Provide a valid HTTPS URL. Example: https://example.com/webhook",
    # Notification errors
    ErrorCode.NOTIFY_SMTP_FAILED: "Run: mysql-to-sheets diagnose  — check SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in .env",
    ErrorCode.NOTIFY_SLACK_FAILED: "Run: mysql-to-sheets diagnose  — verify SLACK_WEBHOOK_URL in .env is active",
    ErrorCode.NOTIFY_WEBHOOK_FAILED: "Run: mysql-to-sheets diagnose  — notification webhook endpoint returned an error",
    # Tier errors
    ErrorCode.TIER_UPGRADE_REQUIRED: "Run: mysql-to-sheets tier status  — this feature requires a higher tier",
    ErrorCode.TIER_QUOTA_EXCEEDED: "Run: mysql-to-sheets tier usage  — reached limit for your tier. Upgrade or remove unused items",
    ErrorCode.TIER_FEATURE_DISABLED: "Run: mysql-to-sheets tier features  — to see which tier enables this feature",
    # Retry errors
    ErrorCode.RETRY_EXHAUSTED: "Run: mysql-to-sheets diagnose  — all retries failed. Fix the underlying error and try again",
    ErrorCode.CIRCUIT_OPEN: "Wait 60 seconds for the circuit breaker to reset, then run: mysql-to-sheets sync",
    # License errors
    ErrorCode.LICENSE_MISSING: "Set LICENSE_KEY in .env with your subscription license key. Run: mysql-to-sheets license status",
    ErrorCode.LICENSE_INVALID: "Run: mysql-to-sheets license status  — verify LICENSE_KEY in .env is correct and unmodified",
    ErrorCode.LICENSE_EXPIRED: "Run: mysql-to-sheets license status  — renew your subscription to get a new license key",
    ErrorCode.LICENSE_TIER_REQUIRED: "Run: mysql-to-sheets tier features  — upgrade your subscription to access this feature",
    # Schema evolution errors
    ErrorCode.SCHEMA_STRICT_VIOLATION: (
        "Database schema has changed (columns added or removed). "
        "Use --schema-policy=additive to allow new columns, or --schema-policy=flexible to allow all changes. "
        "Update expected_headers in your sync config to match the new schema."
    ),
    ErrorCode.SCHEMA_ADDITIVE_VIOLATION: (
        "Columns have been removed from the database schema. "
        "Use --schema-policy=flexible to allow column removal, or update your sync config. "
        "Removed columns will need to be handled in your downstream processes."
    ),
    # PII errors
    ErrorCode.PII_DETECTED: (
        "PII detected in data. Acknowledge with --pii-acknowledged or apply transforms with "
        "--pii-transform='{\"column\": \"hash\"}'. Run: mysql-to-sheets pii detect"
    ),
    ErrorCode.PII_ACK_REQUIRED: (
        "PII columns require explicit acknowledgment before syncing. "
        "Use --pii-acknowledged to confirm or --pii-transform to apply transforms."
    ),
    ErrorCode.PII_TRANSFORM_FAILED: (
        "Failed to apply PII transformation. Check the transform type is valid "
        "(hash, redact, partial_mask) and the data is compatible."
    ),
    ErrorCode.PII_POLICY_BLOCKED: (
        "Organization policy requires PII handling. "
        "Contact your administrator or apply the required transforms."
    ),
    ErrorCode.PII_INVALID_TRANSFORM: (
        "Invalid PII transform type. Valid options: none, hash, redact, partial_mask. "
        "Run: mysql-to-sheets pii --help"
    ),
}


def get_error_category(code: str) -> ErrorCategory:
    """Get the category for an error code.

    Args:
        code: Error code string.

    Returns:
        ErrorCategory for the code, or PERMANENT if unknown.
    """
    return ERROR_CATEGORIES.get(code, ErrorCategory.PERMANENT)


def get_remediation_hint(code: str, db_type: str | None = None) -> str:
    """Get remediation hint for an error code, optionally specialized for database type.

    Args:
        code: Error code string.
        db_type: Optional database type for specialized hints (mysql, postgres, sqlite, mssql).

    Returns:
        Remediation hint or generic message if unknown.
    """
    # Check for database-type-specific hint first
    if db_type and code in DB_SPECIFIC_HINTS:
        specific_hints = DB_SPECIFIC_HINTS[code]
        if db_type.lower() in specific_hints:
            return specific_hints[db_type.lower()]

    return REMEDIATION_HINTS.get(code, "Check logs for more details")


# Database-type-specific remediation hints for common errors
DB_SPECIFIC_HINTS: dict[str, dict[str, str]] = {
    ErrorCode.DB_CONNECTION_REFUSED: {
        "mysql": (
            "Check that MySQL is running: sudo systemctl status mysql (or mysqld)\n"
            "Verify DB_HOST and DB_PORT (default: 3306) in your .env file\n"
            "Test manually: mysql -h localhost -P 3306 -u your_user -p"
        ),
        "postgres": (
            "Check that PostgreSQL is running: sudo systemctl status postgresql\n"
            "Verify DB_HOST and DB_PORT (default: 5432) in your .env file\n"
            "Test manually: psql -h localhost -p 5432 -U your_user -d your_db"
        ),
        "sqlite": (
            "Verify the database file path in DB_NAME exists and is readable\n"
            "Check file permissions: ls -la /path/to/database.db\n"
            "Ensure the directory exists: mkdir -p $(dirname /path/to/database.db)"
        ),
        "mssql": (
            "Check that SQL Server is running (Windows: SQL Server Configuration Manager)\n"
            "Verify DB_HOST and DB_PORT (default: 1433) in your .env file\n"
            "Ensure TCP/IP protocol is enabled in SQL Server Configuration"
        ),
    },
    ErrorCode.DB_AUTH_FAILED: {
        "mysql": (
            "Verify DB_USER and DB_PASSWORD in your .env file\n"
            "Check user has access from your host: SHOW GRANTS FOR 'user'@'host';\n"
            "Grant access: GRANT SELECT ON dbname.* TO 'user'@'%' IDENTIFIED BY 'password';"
        ),
        "postgres": (
            "Verify DB_USER and DB_PASSWORD in your .env file\n"
            "Check pg_hba.conf allows connections from your host\n"
            "Test: psql -h localhost -U your_user -d your_db"
        ),
        "sqlite": (
            "SQLite doesn't use authentication, but check file permissions\n"
            "Ensure read permission: chmod 644 /path/to/database.db\n"
            "If encrypted, ensure the encryption key is correct"
        ),
        "mssql": (
            "Verify DB_USER and DB_PASSWORD in your .env file\n"
            "For Windows Auth, try DB_USER=domain\\\\username\n"
            "For SQL Auth, ensure 'SQL Server and Windows Authentication mode' is enabled"
        ),
    },
    ErrorCode.DB_NOT_FOUND: {
        "mysql": (
            "Verify DB_NAME matches an existing database\n"
            "List databases: mysql -e 'SHOW DATABASES;'\n"
            "Create if needed: CREATE DATABASE your_db;"
        ),
        "postgres": (
            "Verify DB_NAME matches an existing database\n"
            "List databases: psql -l (or \\l in psql)\n"
            "Create if needed: CREATE DATABASE your_db;"
        ),
        "sqlite": (
            "Verify the file path in DB_NAME exists\n"
            "SQLite creates files automatically, but the directory must exist\n"
            "Check: ls -la /path/to/database.db"
        ),
        "mssql": (
            "Verify DB_NAME matches an existing database\n"
            "List databases: SELECT name FROM sys.databases;\n"
            "Create if needed: CREATE DATABASE your_db;"
        ),
    },
    ErrorCode.DB_TIMEOUT: {
        "mysql": (
            "Increase DB_READ_TIMEOUT in .env (default: 300 seconds)\n"
            "Optimize query with indexes or add LIMIT clause\n"
            "Check query plan: EXPLAIN SELECT ..."
        ),
        "postgres": (
            "Increase DB_READ_TIMEOUT in .env (default: 300 seconds)\n"
            "Set statement_timeout in PostgreSQL config\n"
            "Analyze query: EXPLAIN ANALYZE SELECT ..."
        ),
        "sqlite": (
            "SQLite timeouts are usually due to file locking\n"
            "Ensure no other process has an exclusive lock\n"
            "Consider WAL mode: PRAGMA journal_mode=WAL;"
        ),
        "mssql": (
            "Increase DB_READ_TIMEOUT in .env (default: 300 seconds)\n"
            "Check query plan: SET STATISTICS IO ON; SELECT ...\n"
            "Add indexes or optimize the query"
        ),
    },
    ErrorCode.DB_QUERY_ERROR: {
        "mysql": (
            "Check SQL syntax for MySQL-specific keywords\n"
            "Use backticks for reserved words: SELECT `order` FROM ...\n"
            "Validate: mysql-to-sheets sync --dry-run"
        ),
        "postgres": (
            "Check SQL syntax for PostgreSQL-specific features\n"
            "Use double quotes for identifiers: SELECT \"order\" FROM ...\n"
            "Note: PostgreSQL is case-sensitive for quoted identifiers"
        ),
        "sqlite": (
            "Check SQL syntax for SQLite limitations\n"
            "SQLite doesn't support: RIGHT/FULL OUTER JOIN, ALTER COLUMN\n"
            "Use SQLite-compatible date functions: date(), datetime()"
        ),
        "mssql": (
            "Check SQL syntax for SQL Server-specific keywords\n"
            "Use square brackets for reserved words: SELECT [order] FROM ...\n"
            "TOP instead of LIMIT: SELECT TOP 100 * FROM ..."
        ),
    },
}


class SyncError(Exception):
    """Base exception for all sync-related errors.

    Attributes:
        message: Human-readable error description.
        details: Optional dictionary with additional error context.
        code: Error code for troubleshooting (e.g., DB_201).
        category: Error category (transient, permanent, etc.).
    """

    # Default error code for this exception class (override in subclasses)
    default_code: str | None = None

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize SyncError.

        Args:
            message: Human-readable error description.
            details: Optional dictionary with additional error context.
            code: Error code for troubleshooting (uses default_code if not specified).
        """
        self.message = message
        self.details = details or {}
        self._code = code or self.default_code
        super().__init__(self.message)

    @property
    def code(self) -> str | None:
        """Get the error code."""
        return self._code

    @property
    def category(self) -> ErrorCategory | None:
        """Get the error category based on code."""
        if self._code:
            return get_error_category(self._code)
        return None

    @property
    def remediation(self) -> str | None:
        """Get the remediation hint for this error."""
        if self._code:
            return get_remediation_hint(self._code)
        return None

    @property
    def is_transient(self) -> bool:
        """Check if this error is transient (retry may help)."""
        return self.category == ErrorCategory.TRANSIENT

    def format_cli(self) -> str:
        """Format error for CLI output with code, category, and remediation.

        Returns:
            Multi-line string suitable for terminal display.
        """
        lines = [f"Error: {self.message}"]
        if self._code:
            lines.append(f"  Code: {self._code}")
        if self.category:
            lines.append(f"  Category: {self.category.value}")
        if self.remediation:
            lines.append(f"  Fix: {self.remediation}")
        return "\n".join(lines)

    def to_dict(self, request_id: str | None = None) -> dict[str, Any]:
        """Convert exception to dictionary for API responses.

        Args:
            request_id: Optional request ID for correlation.

        Returns:
            Dictionary with error type, message, code, category, and remediation.
        """
        result = {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }

        if self._code:
            result["code"] = self._code
            if self.category:
                result["category"] = self.category.value
            if self.remediation:
                result["remediation"] = self.remediation

        if request_id:
            result["request_id"] = request_id

        return result

class ConfigError(SyncError):
    """Raised when configuration is invalid or missing.

    Examples:
        - Missing required environment variables
        - Invalid port number
        - Service account file not found
    """

    default_code = ErrorCode.CONFIG_MISSING_FIELD

    def __init__(
        self,
        message: str,
        missing_fields: list[str] | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize ConfigError.

        Args:
            message: Human-readable error description.
            missing_fields: List of missing or invalid configuration fields.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if missing_fields:
            details["missing_fields"] = missing_fields
        super().__init__(message, details, code=code)
        self.missing_fields = missing_fields or []


class DatabaseError(SyncError):
    """Raised when database operations fail.

    Examples:
        - Connection refused
        - Authentication failed
        - Query syntax error
        - Query timeout
    """

    default_code = ErrorCode.DB_CONNECTION_REFUSED

    def __init__(
        self,
        message: str,
        host: str | None = None,
        database: str | None = None,
        original_error: Exception | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize DatabaseError.

        Args:
            message: Human-readable error description.
            host: Database host that failed.
            database: Database name that failed.
            original_error: The underlying exception that caused this error.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if host:
            details["host"] = host
        if database:
            details["database"] = database
        if original_error:
            details["original_error"] = str(original_error)

        # Auto-detect error code from original error if not specified
        if code is None and original_error:
            code = self._detect_error_code(original_error)

        super().__init__(message, details, code=code)
        self.host = host
        self.database = database
        self.original_error = original_error

    @staticmethod
    def _detect_error_code(error: Exception) -> str:
        """Detect error code from the original exception.

        Args:
            error: The original database exception.

        Returns:
            Detected error code.
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Connection errors
        if "refused" in error_str or "connection" in error_str:
            return ErrorCode.DB_CONNECTION_REFUSED
        if "access denied" in error_str or "authentication" in error_str:
            return ErrorCode.DB_AUTH_FAILED
        if "timeout" in error_str or "timed out" in error_str:
            return ErrorCode.DB_TIMEOUT
        if "unknown database" in error_str or "does not exist" in error_str:
            return ErrorCode.DB_NOT_FOUND
        if "syntax" in error_str or "error in your sql" in error_str:
            return ErrorCode.DB_QUERY_ERROR
        if "lost connection" in error_str or "gone away" in error_str:
            return ErrorCode.DB_CONNECTION_LOST

        return ErrorCode.DB_CONNECTION_REFUSED


class SheetsError(SyncError):
    """Raised when Google Sheets operations fail.

    Examples:
        - Spreadsheet not found
        - Worksheet not found
        - API rate limit exceeded
        - Authentication failed
    """

    default_code = ErrorCode.SHEETS_API_ERROR

    def __init__(
        self,
        message: str,
        sheet_id: str | None = None,
        worksheet_name: str | None = None,
        original_error: Exception | None = None,
        rate_limited: bool = False,
        retry_after: float | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize SheetsError.

        Args:
            message: Human-readable error description.
            sheet_id: Google Sheets spreadsheet ID that failed.
            worksheet_name: Worksheet name that failed.
            original_error: The underlying exception that caused this error.
            rate_limited: Whether this error is due to rate limiting.
            retry_after: Seconds to wait before retrying (if rate limited).
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if sheet_id:
            details["sheet_id"] = sheet_id
        if worksheet_name:
            details["worksheet_name"] = worksheet_name
        if original_error:
            details["original_error"] = str(original_error)
        if rate_limited:
            details["rate_limited"] = rate_limited
            code = code or ErrorCode.SHEETS_RATE_LIMITED
        if retry_after is not None:
            details["retry_after"] = retry_after

        # Auto-detect error code from original error if not specified
        if code is None and original_error:
            code = self._detect_error_code(original_error)

        super().__init__(message, details, code=code)
        self.sheet_id = sheet_id
        self.worksheet_name = worksheet_name
        self.original_error = original_error
        self.rate_limited = rate_limited
        self.retry_after = retry_after

    @staticmethod
    def _detect_error_code(error: Exception) -> str:
        """Detect error code from the original exception.

        Args:
            error: The original Sheets exception.

        Returns:
            Detected error code.
        """
        error_str = str(error).lower()

        if "spreadsheet not found" in error_str or "404" in error_str:
            return ErrorCode.SHEETS_NOT_FOUND
        if "permission" in error_str or "403" in error_str:
            return ErrorCode.SHEETS_PERMISSION_DENIED
        if "rate limit" in error_str or "quota" in error_str or "429" in error_str:
            return ErrorCode.SHEETS_RATE_LIMITED
        if "worksheet" in error_str and "not found" in error_str:
            return ErrorCode.SHEETS_WORKSHEET_NOT_FOUND
        if "invalid credentials" in error_str or "authentication" in error_str:
            return ErrorCode.SHEETS_AUTH_FAILED

        return ErrorCode.SHEETS_API_ERROR


class RetryExhaustedError(SyncError):
    """Raised when all retry attempts have been exhausted.

    Examples:
        - Database connection failed after 3 retries
        - Google Sheets API rate limited after backoff
    """

    default_code = ErrorCode.RETRY_EXHAUSTED

    def __init__(
        self,
        message: str,
        attempts: int,
        last_error: Exception | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize RetryExhaustedError.

        Args:
            message: Human-readable error description.
            attempts: Number of attempts made.
            last_error: The last exception that occurred.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {"attempts": attempts}
        if last_error:
            details["last_error"] = str(last_error)
            details["last_error_type"] = type(last_error).__name__
        super().__init__(message, details, code=code)
        self.attempts = attempts
        self.last_error = last_error


class TimeoutError(SyncError):
    """Raised when an operation times out.

    Examples:
        - Database query exceeded read timeout
        - Google Sheets API request timed out
    """

    default_code = ErrorCode.DB_TIMEOUT

    def __init__(
        self,
        message: str,
        timeout_seconds: int | float | None = None,
        operation: str | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize TimeoutError.

        Args:
            message: Human-readable error description.
            timeout_seconds: The timeout value that was exceeded.
            operation: Name of the operation that timed out.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        super().__init__(message, details, code=code)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class CircuitOpenError(SyncError):
    """Raised when a circuit breaker is open and rejecting requests.

    This indicates the circuit breaker has tripped due to too many
    failures, and requests are being rejected to prevent cascading
    failures.

    Examples:
        - MySQL circuit breaker open after 5 connection failures
        - Google Sheets circuit breaker open after rate limit hits
    """

    default_code = ErrorCode.CIRCUIT_OPEN

    def __init__(
        self,
        message: str,
        circuit_name: str | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize CircuitOpenError.

        Args:
            message: Human-readable error description.
            circuit_name: Name of the circuit breaker that is open.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if circuit_name:
            details["circuit_name"] = circuit_name
        super().__init__(message, details, code=code)
        self.circuit_name = circuit_name


class NotificationError(SyncError):
    """Raised when notification delivery fails.

    Examples:
        - SMTP connection refused
        - Slack webhook returned error
        - Invalid email configuration
    """

    default_code = ErrorCode.NOTIFY_WEBHOOK_FAILED

    def __init__(
        self,
        message: str,
        backend: str | None = None,
        original_error: Exception | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize NotificationError.

        Args:
            message: Human-readable error description.
            backend: Name of the notification backend that failed.
            original_error: The underlying exception that caused this error.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if backend:
            details["backend"] = backend

            # Auto-detect code based on backend
            if code is None:
                if backend.lower() == "smtp" or backend.lower() == "email":
                    code = ErrorCode.NOTIFY_SMTP_FAILED
                elif backend.lower() == "slack":
                    code = ErrorCode.NOTIFY_SLACK_FAILED

        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, details, code=code)
        self.backend = backend
        self.original_error = original_error


class SchedulerError(SyncError):
    """Raised when scheduler operations fail.

    Examples:
        - Failed to start scheduler
        - Invalid cron expression
        - Job not found
    """

    default_code = ErrorCode.SCHEDULER_JOB_NOT_FOUND

    def __init__(
        self,
        message: str,
        job_id: int | str | None = None,
        job_name: str | None = None,
        original_error: Exception | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize SchedulerError.

        Args:
            message: Human-readable error description.
            job_id: ID of the job that failed.
            job_name: Name of the job that failed.
            original_error: The underlying exception that caused this error.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if job_id is not None:
            details["job_id"] = job_id
        if job_name:
            details["job_name"] = job_name
        if original_error:
            details["original_error"] = str(original_error)

        # Auto-detect code from message if not specified
        if code is None:
            msg_lower = message.lower()
            if "cron" in msg_lower or "invalid" in msg_lower:
                code = ErrorCode.SCHEDULER_INVALID_CRON
            elif "not found" in msg_lower:
                code = ErrorCode.SCHEDULER_JOB_NOT_FOUND
            elif "start" in msg_lower or "failed" in msg_lower:
                code = ErrorCode.SCHEDULER_START_FAILED

        super().__init__(message, details, code=code)
        self.job_id = job_id
        self.job_name = job_name
        self.original_error = original_error


class UnsupportedDatabaseError(SyncError):
    """Raised when an unsupported database type is requested.

    Examples:
        - Requesting PostgreSQL without psycopg2 installed
        - Using an unknown database type identifier
    """

    default_code = ErrorCode.DB_UNSUPPORTED

    def __init__(
        self,
        message: str,
        db_type: str | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize UnsupportedDatabaseError.

        Args:
            message: Human-readable error description.
            db_type: The unsupported database type that was requested.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if db_type:
            details["db_type"] = db_type
        super().__init__(message, details, code=code)
        self.db_type = db_type


class AuthenticationError(SyncError):
    """Raised when authentication fails.

    Examples:
        - Invalid email or password
        - Expired or invalid JWT token
        - Missing authentication credentials
    """

    default_code = ErrorCode.AUTH_INVALID_CREDENTIALS

    def __init__(
        self,
        message: str,
        email: str | None = None,
        reason: str | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize AuthenticationError.

        Args:
            message: Human-readable error description.
            email: Email address that failed authentication (for logging).
            reason: Specific reason for authentication failure.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if email:
            details["email"] = email
        if reason:
            details["reason"] = reason

            # Auto-detect code from reason
            if code is None:
                reason_lower = reason.lower()
                if "expired" in reason_lower:
                    code = ErrorCode.AUTH_TOKEN_EXPIRED
                elif "invalid" in reason_lower and "token" in reason_lower:
                    code = ErrorCode.AUTH_TOKEN_INVALID
                elif "rate" in reason_lower or "limit" in reason_lower:
                    code = ErrorCode.AUTH_RATE_LIMITED

        super().__init__(message, details, code=code)
        self.email = email
        self.reason = reason


class AuthorizationError(SyncError):
    """Raised when authorization fails (user lacks required permission).

    Examples:
        - User tried to delete a config without permission
        - User tried to manage users without admin role
        - User tried to access another organization's data
    """

    default_code = ErrorCode.AUTH_PERMISSION_DENIED

    def __init__(
        self,
        message: str,
        required_permission: str | None = None,
        user_role: str | None = None,
        resource: str | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize AuthorizationError.

        Args:
            message: Human-readable error description.
            required_permission: Permission that was required.
            user_role: Role of the user who was denied.
            resource: Resource that was being accessed.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if required_permission:
            details["required_permission"] = required_permission
        if user_role:
            details["user_role"] = user_role
        if resource:
            details["resource"] = resource
        super().__init__(message, details, code=code)
        self.required_permission = required_permission
        self.user_role = user_role
        self.resource = resource


class OrganizationError(SyncError):
    """Raised when organization operations fail.

    Examples:
        - Organization not found
        - Organization inactive
        - Quota exceeded (max users, max configs)
    """

    default_code = ErrorCode.ORG_NOT_FOUND

    def __init__(
        self,
        message: str,
        organization_id: int | None = None,
        organization_slug: str | None = None,
        quota_type: str | None = None,
        quota_limit: int | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize OrganizationError.

        Args:
            message: Human-readable error description.
            organization_id: ID of the organization.
            organization_slug: Slug of the organization.
            quota_type: Type of quota exceeded (users, configs).
            quota_limit: The quota limit that was exceeded.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if organization_id is not None:
            details["organization_id"] = organization_id
        if organization_slug:
            details["organization_slug"] = organization_slug
        if quota_type:
            details["quota_type"] = quota_type
            if code is None:
                code = ErrorCode.ORG_QUOTA_EXCEEDED
        if quota_limit is not None:
            details["quota_limit"] = quota_limit

        # Auto-detect code from message
        if code is None:
            msg_lower = message.lower()
            if "inactive" in msg_lower or "deactivated" in msg_lower:
                code = ErrorCode.ORG_INACTIVE
            elif "not found" in msg_lower:
                code = ErrorCode.ORG_NOT_FOUND

        super().__init__(message, details, code=code)
        self.organization_id = organization_id
        self.organization_slug = organization_slug
        self.quota_type = quota_type
        self.quota_limit = quota_limit


class WebhookError(SyncError):
    """Raised when webhook operations fail.

    Examples:
        - Webhook delivery failed
        - Invalid webhook URL
        - Webhook subscription not found
    """

    default_code = ErrorCode.WEBHOOK_DELIVERY_FAILED

    def __init__(
        self,
        message: str,
        webhook_id: int | None = None,
        webhook_url: str | None = None,
        delivery_id: str | None = None,
        original_error: Exception | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize WebhookError.

        Args:
            message: Human-readable error description.
            webhook_id: ID of the webhook subscription.
            webhook_url: URL of the webhook endpoint.
            delivery_id: ID of the delivery attempt.
            original_error: The underlying exception that caused this error.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if webhook_id is not None:
            details["webhook_id"] = webhook_id
        if webhook_url:
            details["webhook_url"] = webhook_url
        if delivery_id:
            details["delivery_id"] = delivery_id
        if original_error:
            details["original_error"] = str(original_error)

        # Auto-detect code from message
        if code is None:
            msg_lower = message.lower()
            if "not found" in msg_lower:
                code = ErrorCode.WEBHOOK_NOT_FOUND
            elif "invalid" in msg_lower and "url" in msg_lower:
                code = ErrorCode.WEBHOOK_INVALID_URL

        super().__init__(message, details, code=code)
        self.webhook_id = webhook_id
        self.webhook_url = webhook_url
        self.delivery_id = delivery_id
        self.original_error = original_error


class TierError(SyncError):
    """Raised when tier requirements are not met.

    Examples:
        - Feature requires higher subscription tier
        - Resource quota exceeded for current tier
        - Tier not found
    """

    default_code = ErrorCode.TIER_UPGRADE_REQUIRED

    def __init__(
        self,
        message: str,
        required_tier: str | None = None,
        current_tier: str | None = None,
        feature: str | None = None,
        quota_type: str | None = None,
        quota_limit: int | None = None,
        quota_used: int | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize TierError.

        Args:
            message: Human-readable error description.
            required_tier: Tier required for the operation.
            current_tier: Current tier of the organization.
            feature: Feature that requires the tier.
            quota_type: Type of quota exceeded (configs, users, etc.).
            quota_limit: The quota limit for the tier.
            quota_used: Current usage count.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if required_tier:
            details["required_tier"] = required_tier
        if current_tier:
            details["current_tier"] = current_tier
        if feature:
            details["feature"] = feature
            if code is None:
                code = ErrorCode.TIER_FEATURE_DISABLED
        if quota_type:
            details["quota_type"] = quota_type
            if code is None:
                code = ErrorCode.TIER_QUOTA_EXCEEDED
        if quota_limit is not None:
            details["quota_limit"] = quota_limit
        if quota_used is not None:
            details["quota_used"] = quota_used
        super().__init__(message, details, code=code)
        self.required_tier = required_tier
        self.current_tier = current_tier
        self.feature = feature
        self.quota_type = quota_type
        self.quota_limit = quota_limit
        self.quota_used = quota_used


class LicenseError(SyncError):
    """Raised when license validation fails.

    Examples:
        - License key missing or not configured
        - License key is invalid or tampered
        - License has expired
        - License tier insufficient for feature
    """

    default_code = ErrorCode.LICENSE_MISSING

    def __init__(
        self,
        message: str,
        code: str | None = None,
        current_tier: str | None = None,
        required_tier: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize LicenseError.

        Args:
            message: Human-readable error description.
            code: Error code for troubleshooting.
            current_tier: Current license tier (if applicable).
            required_tier: Required tier for the operation (if applicable).
            **context: Additional context for the error.
        """
        details = dict(context)
        if current_tier:
            details["current_tier"] = current_tier
        if required_tier:
            details["required_tier"] = required_tier
        super().__init__(message, details, code=code)
        self.current_tier = current_tier
        self.required_tier = required_tier


class DestinationError(SyncError):
    """Raised when destination operations fail.

    This is the base exception for all destination-related errors,
    including Google Sheets, Excel Online, and other output targets.

    Examples:
        - Destination not found
        - Permission denied
        - Write operation failed
        - Unsupported destination type
    """

    default_code = "DEST_001"

    def __init__(
        self,
        message: str,
        destination_type: str | None = None,
        target_id: str | None = None,
        target_name: str | None = None,
        original_error: Exception | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize DestinationError.

        Args:
            message: Human-readable error description.
            destination_type: Type of destination (e.g., 'google_sheets').
            target_id: Target identifier (e.g., sheet ID).
            target_name: Target name (e.g., worksheet name).
            original_error: The underlying exception that caused this error.
            code: Error code for troubleshooting.
        """
        details: dict[str, Any] = {}
        if destination_type:
            details["destination_type"] = destination_type
        if target_id:
            details["target_id"] = target_id
        if target_name:
            details["target_name"] = target_name
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, details, code=code)
        self.destination_type = destination_type
        self.target_id = target_id
        self.target_name = target_name
        self.original_error = original_error


class PIIError(SyncError):
    """Base exception for PII-related errors.

    Examples:
        - PII detected and requires acknowledgment
        - PII transform failed
        - Organization policy blocks sync
    """

    default_code = ErrorCode.PII_DETECTED

    def __init__(
        self,
        message: str,
        code: str | None = None,
        columns: list[str] | None = None,
        **context: Any,
    ) -> None:
        """Initialize PIIError.

        Args:
            message: Human-readable error description.
            code: Error code for troubleshooting.
            columns: List of PII column names.
            **context: Additional context for the error.
        """
        details = dict(context)
        if columns:
            details["pii_columns"] = columns
        super().__init__(message, details, code=code)
        self.columns = columns or []


class PIIAcknowledgmentRequired(PIIError):
    """Raised when PII is detected and requires user acknowledgment.

    This exception includes the full PII detection result so the caller
    can inform the user about what was detected.

    Examples:
        - Auto-detected email column
        - Content-matched SSN patterns
        - Multiple PII columns requiring review
    """

    default_code = ErrorCode.PII_ACK_REQUIRED

    def __init__(
        self,
        message: str | None = None,
        pii_result: Any | None = None,  # PIIDetectionResult
        code: str | None = None,
    ) -> None:
        """Initialize PIIAcknowledgmentRequired.

        Args:
            message: Human-readable error description.
            pii_result: PIIDetectionResult with detection details.
            code: Error code for troubleshooting.
        """
        self.pii_result = pii_result

        # Build message from detection result
        if message is None and pii_result:
            columns = [col.column_name for col in pii_result.columns]
            message = (
                f"PII detected in {len(columns)} column(s): {', '.join(columns)}. "
                f"Use --pii-acknowledged to proceed or --pii-transform to apply transforms."
            )
        elif message is None:
            message = "PII detected. Acknowledgment required to proceed."

        # Extract column names for details
        columns = [col.column_name for col in pii_result.columns] if pii_result else []

        super().__init__(message, code=code, columns=columns)

    def to_dict(self, request_id: str | None = None) -> dict[str, Any]:
        """Convert exception to dictionary for API responses.

        Args:
            request_id: Optional request ID for correlation.

        Returns:
            Dictionary with error details and PII detection result.
        """
        result = super().to_dict(request_id)
        if self.pii_result:
            result["pii_detection"] = self.pii_result.to_dict()
        return result


class PIIPolicyBlockedError(PIIError):
    """Raised when organization policy blocks PII sync.

    Examples:
        - ENTERPRISE org requires all PII to be transformed
        - Block-unacknowledged policy prevents sync
    """

    default_code = ErrorCode.PII_POLICY_BLOCKED

    def __init__(
        self,
        message: str,
        policy_name: str | None = None,
        organization_id: int | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize PIIPolicyBlockedError.

        Args:
            message: Human-readable error description.
            policy_name: Name of the blocking policy.
            organization_id: Organization with the policy.
            code: Error code for troubleshooting.
        """
        super().__init__(message, code=code, policy_name=policy_name)
        self.policy_name = policy_name
        self.organization_id = organization_id
