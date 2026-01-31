"""Validation utilities for configuration values.

This module provides functions for validating configuration settings
such as service account files, SQL queries, and environment values.
"""

import json
import os
import re
from pathlib import Path

# Required fields for Google Service Account JSON
SERVICE_ACCOUNT_REQUIRED_FIELDS = {"type", "client_email", "private_key"}


def check_service_account_readable(path: str) -> tuple[bool, str | None]:
    """Check if service account file exists and is readable.

    This check runs BEFORE attempting to parse JSON, to give a more specific
    error message when the file exists but has permission issues.

    Args:
        path: Path to the service account JSON file.

    Returns:
        Tuple of (is_readable, error_message). error_message is None if readable.
    """
    if not os.path.exists(path):
        return True, None  # Let the "file not found" error handle this case

    if not os.access(path, os.R_OK):
        return False, (
            f"Service account file exists but cannot be read due to file permissions.\n\n"
            f"File: {path}\n\n"
            f"To fix on Linux/macOS:\n"
            f"  chmod 644 {path}\n\n"
            f"Or move to a user-writable location:\n"
            f"  cp {path} ./service_account.json"
        )

    return True, None


def validate_service_account_json(path: str) -> tuple[bool, str | None]:
    """Validate service account file contains valid JSON.

    Handles UTF-8 BOM (Byte Order Mark) which is common when editing
    with Windows Notepad. Uses utf-8-sig encoding to auto-strip BOM.

    Args:
        path: Path to the service account JSON file.

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    try:
        # Use utf-8-sig to auto-strip UTF-8 BOM if present
        with open(path, encoding="utf-8-sig") as f:
            json.load(f)
        return True, None
    except json.JSONDecodeError as e:
        # Check if this might be a BOM issue that wasn't handled
        # (e.g., different BOM or encoding issue)
        try:
            with open(path, "rb") as f:
                first_bytes = f.read(3)
                if first_bytes == b"\xef\xbb\xbf":
                    return False, (
                        f"Service account file '{path}' has UTF-8 BOM (Byte Order Mark). "
                        "This is common when editing with Windows Notepad. "
                        "Open the file in a text editor (like VS Code or Notepad++) "
                        "and save as 'UTF-8' without BOM, or re-download from Google Cloud Console."
                    )
        except Exception:
            pass
        return False, (
            f"Invalid JSON in service account file '{path}': {e.msg} at line {e.lineno}. "
            "Re-download the JSON key from Google Cloud Console > IAM & Admin > Service Accounts."
        )
    except UnicodeDecodeError:
        return False, (
            f"Invalid encoding in service account file '{path}'. "
            "The file must be UTF-8 encoded. Re-download the JSON key from Google Cloud Console."
        )


def validate_service_account_structure(path: str) -> tuple[bool, str | None]:
    """Validate service account JSON has required fields.

    Args:
        path: Path to the service account JSON file.

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    try:
        # Use utf-8-sig to handle BOM consistently
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Already caught by JSON validation
        return True, None

    if not isinstance(data, dict):
        return False, (
            f"Service account file must be a JSON object, got {type(data).__name__}. "
            "Ensure you downloaded a Service Account key (not OAuth credentials)."
        )

    # Check type field FIRST (if present) - this gives better error messages
    # for OAuth2 credentials which have a different type
    if "type" in data and data.get("type") != "service_account":
        actual_type = data.get("type")
        return False, (
            f"Invalid credential type: '{actual_type}'. Expected 'service_account'. "
            "You may have downloaded OAuth2 credentials or an API key instead. "
            "Go to Google Cloud Console > IAM & Admin > Service Accounts to download the correct key."
        )

    # Check for required fields
    missing = SERVICE_ACCOUNT_REQUIRED_FIELDS - set(data.keys())
    if missing:
        return False, (
            f"Service account file missing required fields: {', '.join(sorted(missing))}. "
            "Ensure you downloaded a Service Account key (not OAuth credentials) from "
            "Google Cloud Console > IAM & Admin > Service Accounts > Keys > Add Key > Create new key (JSON)."
        )

    return True, None


def get_service_account_email(path: str | None) -> str | None:
    """Extract client_email from service account JSON file.

    Args:
        path: Path to the service account JSON file.

    Returns:
        The client_email value, or None if file doesn't exist or can't be parsed.
    """
    if not path or not Path(path).exists():
        return None
    try:
        # Use utf-8-sig to handle BOM if present
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
        return data.get("client_email")
    except Exception:
        return None


def detect_sql_file_path(query: str) -> str | None:
    """Detect if SQL_QUERY looks like a file path instead of actual SQL.

    Common mistake: users from other ETL tools enter file paths like
    /path/to/query.sql or C:\\queries\\report.sql instead of actual SQL.

    Args:
        query: The SQL query string to check.

    Returns:
        Error message if query looks like a file path, None otherwise.
    """
    if not query:
        return None

    query_stripped = query.strip()
    if not query_stripped:
        return None

    # Check for file path patterns that end with .sql
    looks_like_sql_file = query_stripped.lower().endswith(".sql") and (
        query_stripped.startswith("/")  # Unix absolute
        or query_stripped.startswith("./")  # Unix relative
        or query_stripped.startswith("../")  # Unix parent relative
        or query_stripped.startswith("~")  # Unix home
        or (len(query_stripped) > 2 and query_stripped[1] == ":")  # Windows drive C:\
    )

    if looks_like_sql_file:
        return (
            f"SQL_QUERY appears to be a file path: '{query_stripped}'\n\n"
            f"To load SQL from a file, read its contents:\n"
            f"  SQL_QUERY=$(cat {query_stripped})\n\n"
            f"Or in Python:\n"
            f"  with open('{query_stripped}') as f: query = f.read()"
        )
    return None


def strip_sql_comments(query: str) -> str:
    """Strip SQL comments from query to check for actual content.

    Removes:
    - Single-line comments: -- comment and # comment
    - Multi-line comments: /* comment */

    Args:
        query: SQL query string.

    Returns:
        Query with comments removed and whitespace stripped.
    """
    if not query:
        return ""

    # Remove single-line comments (-- and #)
    # Be careful not to remove # in strings or -- in identifiers
    # Simple approach: remove lines starting with -- or # after stripping
    query = re.sub(r"--[^\n]*", "", query)
    query = re.sub(r"#[^\n]*", "", query)

    # Remove multi-line comments /* */
    query = re.sub(r"/\*.*?\*/", "", query, flags=re.DOTALL)

    return query.strip()


def check_placeholders(
    db_user: str,
    db_password: str,
    db_name: str,
    google_sheet_id: str,
) -> list[str]:
    """Check for placeholder values in required fields.

    Args:
        db_user: Database username.
        db_password: Database password.
        db_name: Database name.
        google_sheet_id: Google Sheet ID.

    Returns:
        List of field names that contain placeholder values.
    """
    from mysql_to_sheets.core.config.parsing import is_placeholder

    fields_to_check = [
        ("DB_USER", db_user),
        ("DB_PASSWORD", db_password),
        ("DB_NAME", db_name),
        ("GOOGLE_SHEET_ID", google_sheet_id),
    ]

    placeholders_found = []
    for name, value in fields_to_check:
        if value and is_placeholder(value):
            placeholders_found.append(name)

    return placeholders_found


# Backward compatibility aliases
_check_service_account_readable = check_service_account_readable
_validate_service_account_json = validate_service_account_json
_validate_service_account_structure = validate_service_account_structure
_detect_sql_file_path = detect_sql_file_path
_strip_sql_comments = strip_sql_comments
_check_placeholders = check_placeholders
