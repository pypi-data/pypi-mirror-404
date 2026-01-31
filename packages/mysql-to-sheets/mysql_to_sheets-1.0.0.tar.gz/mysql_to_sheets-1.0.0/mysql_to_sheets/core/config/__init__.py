"""Configuration module for MySQL-to-Google Sheets sync.

This package provides configuration loading, parsing, and validation
for the sync tool. It maintains full backward compatibility with the
original config.py module interface.

Example:
    >>> from mysql_to_sheets.core.config import get_config, Config
    >>> config = get_config()
    >>> new_config = config.with_overrides(google_sheet_id="abc123")

    # Using request overrides helper (eliminates boilerplate)
    >>> from mysql_to_sheets.core.config import apply_request_overrides
    >>> config = apply_request_overrides(request_data)
"""

# Dataclass exports
from mysql_to_sheets.core.config.dataclass import Config, SheetTarget

# Request override helpers
from mysql_to_sheets.core.config.request_overrides import (
    SyncRequestLike,
    apply_request_overrides,
    extract_sync_options,
)

# Parsing exports
from mysql_to_sheets.core.config.parsing import (
    FALSY_VALUES,
    PLACEHOLDER_PATTERNS,
    TRUTHY_VALUES,
    # Backward compatibility aliases (underscore-prefixed)
    _is_placeholder,
    _parse_bool,
    _parse_env_sheet_id,
    _safe_parse_float,
    _safe_parse_int,
    encode_database_url_password,
    is_placeholder,
    parse_bool,
    parse_database_uri,
    parse_env_sheet_id,
    safe_parse_float,
    safe_parse_int,
)

# Singleton exports
from mysql_to_sheets.core.config.singleton import get_config, reset_config

# Validation exports
from mysql_to_sheets.core.config.validation import (
    SERVICE_ACCOUNT_REQUIRED_FIELDS,
    # Backward compatibility aliases (underscore-prefixed)
    _check_placeholders,
    _check_service_account_readable,
    _detect_sql_file_path,
    _strip_sql_comments,
    _validate_service_account_json,
    _validate_service_account_structure,
    check_placeholders,
    check_service_account_readable,
    detect_sql_file_path,
    get_service_account_email,
    strip_sql_comments,
    validate_service_account_json,
    validate_service_account_structure,
)

__all__ = [
    # Core classes
    "Config",
    "SheetTarget",
    # Singleton functions
    "get_config",
    "reset_config",
    # Request override helpers
    "apply_request_overrides",
    "extract_sync_options",
    "SyncRequestLike",
    # Parsing functions
    "encode_database_url_password",
    "parse_database_uri",
    "parse_bool",
    "safe_parse_int",
    "safe_parse_float",
    "parse_env_sheet_id",
    "is_placeholder",
    # Validation functions
    "get_service_account_email",
    "check_service_account_readable",
    "validate_service_account_json",
    "validate_service_account_structure",
    "detect_sql_file_path",
    "strip_sql_comments",
    "check_placeholders",
    # Constants
    "TRUTHY_VALUES",
    "FALSY_VALUES",
    "PLACEHOLDER_PATTERNS",
    "SERVICE_ACCOUNT_REQUIRED_FIELDS",
    # Backward compatibility aliases
    "_parse_bool",
    "_safe_parse_int",
    "_safe_parse_float",
    "_parse_env_sheet_id",
    "_is_placeholder",
    "_check_service_account_readable",
    "_validate_service_account_json",
    "_validate_service_account_structure",
    "_detect_sql_file_path",
    "_strip_sql_comments",
    "_check_placeholders",
]
