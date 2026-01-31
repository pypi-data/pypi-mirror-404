"""Parsing utilities for configuration values.

This module provides functions for parsing environment variables and
connection URIs into properly typed values.
"""

import os
import re
from typing import Any
from urllib.parse import quote, unquote, urlparse

from mysql_to_sheets.core.exceptions import ConfigError

# EC-46: Boolean parsing - Truthy and falsy values for environment variables
# Users from other tools expect "1", "yes", "on" to work as true
TRUTHY_VALUES = frozenset({"true", "1", "yes", "on", "enabled"})
FALSY_VALUES = frozenset({"false", "0", "no", "off", "disabled", ""})


def parse_bool(env_var: str, default: bool = False) -> bool:
    """Parse a boolean value from an environment variable.

    Accepts common truthy values: true, 1, yes, on, enabled (case-insensitive)
    Accepts common falsy values: false, 0, no, off, disabled, empty string

    Args:
        env_var: Name of the environment variable.
        default: Default value if env var is not set.

    Returns:
        Parsed boolean value.

    Raises:
        ConfigError: If value is not a valid boolean.

    Examples:
        >>> os.environ["MY_VAR"] = "yes"
        >>> parse_bool("MY_VAR")
        True
        >>> os.environ["MY_VAR"] = "0"
        >>> parse_bool("MY_VAR")
        False
    """
    raw_value = os.getenv(env_var)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()

    if normalized in TRUTHY_VALUES:
        return True
    if normalized in FALSY_VALUES:
        return False

    # Invalid boolean value
    raise ConfigError(
        message=(
            f"Invalid boolean value for {env_var}: '{raw_value}'. "
            f"Accepted truthy values: true, 1, yes, on, enabled. "
            f"Accepted falsy values: false, 0, no, off, disabled, (empty)."
        ),
        missing_fields=[env_var],
        code="CONFIG_123",
    )


def safe_parse_int(
    env_var: str,
    default: int,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """Safely parse an integer from environment variable.

    Args:
        env_var: Name of the environment variable.
        default: Default value if env var is not set.
        min_value: Optional minimum allowed value (inclusive).
        max_value: Optional maximum allowed value (inclusive).

    Returns:
        Parsed integer value.

    Raises:
        ConfigError: If value is not a valid integer or out of bounds.
    """
    raw_value = os.getenv(env_var)
    if raw_value is None:
        return default

    raw_value = raw_value.strip()
    if not raw_value:
        return default

    try:
        value = int(raw_value)
    except ValueError as e:
        raise ConfigError(
            message=(
                f"Invalid integer value for {env_var}: '{raw_value}'. "
                f"Expected a valid integer, got non-numeric value."
            ),
            missing_fields=[env_var],
            code="CONFIG_102",
        ) from e

    if min_value is not None and value < min_value:
        raise ConfigError(
            message=(
                f"Value for {env_var} is too small: {value}. "
                f"Minimum allowed value is {min_value}."
            ),
            missing_fields=[env_var],
            code="CONFIG_102",
        )

    if max_value is not None and value > max_value:
        raise ConfigError(
            message=(
                f"Value for {env_var} is too large: {value}. "
                f"Maximum allowed value is {max_value}."
            ),
            missing_fields=[env_var],
            code="CONFIG_102",
        )

    return value


def safe_parse_float(env_var: str, default: float) -> float:
    """Safely parse a float from environment variable.

    Args:
        env_var: Name of the environment variable.
        default: Default value if env var is not set.

    Returns:
        Parsed float value.

    Raises:
        ConfigError: If value is not a valid float.
    """
    raw_value = os.getenv(env_var)
    if raw_value is None:
        return default

    raw_value = raw_value.strip()
    if not raw_value:
        return default

    try:
        return float(raw_value)
    except ValueError as e:
        raise ConfigError(
            message=(
                f"Invalid float value for {env_var}: '{raw_value}'. "
                f"Expected a valid number."
            ),
            missing_fields=[env_var],
            code="CONFIG_102",
        ) from e


def encode_database_url_password(password: str) -> str:
    """URL-encode a password for use in a DATABASE_URL.

    Special characters like @, #, /, ?, etc. must be URL-encoded when
    used in a connection URI. This helper properly encodes passwords.

    Args:
        password: Raw password string.

    Returns:
        URL-encoded password safe for use in DATABASE_URL.

    Example:
        >>> encode_database_url_password("pass@word#123")
        'pass%40word%23123'
    """
    # Encode all special characters except unreserved ones
    return quote(password, safe="")


def parse_database_uri(uri: str) -> dict[str, Any]:
    """Parse a database connection URI into components.

    Supports MySQL, PostgreSQL, SQLite, and MSSQL connection strings.
    IPv6 addresses are supported in brackets per RFC 3986 (EC-49).

    IMPORTANT: Passwords containing special characters (@, #, /, ?, etc.)
    must be URL-encoded. Use encode_database_url_password() to encode them,
    or manually encode (e.g., @ becomes %40, # becomes %23).

    Args:
        uri: Database connection URI in format:
            - mysql://user:pass@host:port/dbname
            - postgres://user:pass@host:port/dbname
            - postgresql://user:pass@host:port/dbname
            - sqlite:///path/to/file.db
            - sqlite:////absolute/path/to/file.db (4 slashes for absolute)
            - mssql://user:pass@host:port/dbname
            - mysql://user:pass@[::1]:3306/dbname (IPv6 localhost)
            - postgres://user:pass@[2001:db8::1]:5432/dbname (IPv6)

    Returns:
        Dictionary with keys: db_type, db_host, db_port, db_user, db_password, db_name

    Raises:
        ValueError: If URI format is invalid or unsupported scheme.

    Example:
        >>> parse_database_uri("mysql://root:secret@localhost:3306/mydb")
        {'db_type': 'mysql', 'db_host': 'localhost', 'db_port': 3306,
         'db_user': 'root', 'db_password': 'secret', 'db_name': 'mydb'}

        # With special characters in password (must be URL-encoded):
        >>> parse_database_uri("mysql://root:pass%40word@localhost:3306/mydb")
        {'db_type': 'mysql', ..., 'db_password': 'pass@word', ...}

        # IPv6 address in brackets:
        >>> parse_database_uri("mysql://root:secret@[::1]:3306/mydb")
        {'db_type': 'mysql', 'db_host': '::1', 'db_port': 3306, ...}
    """
    if not uri or not uri.strip():
        raise ValueError("Database URI cannot be empty")

    # Check for potential unencoded special characters in credentials
    # Skip this check for sqlite:// which doesn't have credentials
    if not uri.startswith("sqlite://"):
        scheme_end = uri.find("://")
        if scheme_end > 0:
            credentials_and_host = uri[scheme_end + 3 :]

            # EC-49: Handle IPv6 addresses in brackets (e.g., [::1] or [2001:db8::1])
            # IPv6 addresses are enclosed in brackets per RFC 3986
            # Check if this looks like an IPv6 URL before flagging multiple @
            has_ipv6_brackets = "[" in credentials_and_host and "]" in credentials_and_host

            # Find the @ that separates credentials from host
            # (should be exactly one after the scheme, unless IPv6 brackets present)
            at_count = credentials_and_host.count("@")
            if at_count > 1 and not has_ipv6_brackets:
                raise ValueError(
                    "DATABASE_URL appears to contain an unencoded '@' in the password. "
                    "Passwords with special characters must be URL-encoded. "
                    "Use encode_database_url_password() to encode your password, "
                    "or manually encode: @ → %40, # → %23, / → %2F, ? → %3F, "
                    ": → %3A, [ → %5B, ] → %5D"
                )

            # Check for # (fragment) which would truncate the URL
            # Note: # in the password must be encoded as %23
            if "#" in credentials_and_host:
                at_pos = credentials_and_host.find("@")
                if at_pos > 0:
                    # Check if # appears before the @ (i.e., in credentials)
                    creds_part = credentials_and_host[:at_pos]
                    if "#" in creds_part:
                        raise ValueError(
                            "DATABASE_URL appears to contain an unencoded '#' in credentials. "
                            "This character truncates the URL. Encode # as %23. "
                            "Use encode_database_url_password() to encode your password."
                        )

    # Parse the URI
    parsed = urlparse(uri)

    # Map scheme to db_type
    scheme_map = {
        "mysql": "mysql",
        "mysql+mysqlconnector": "mysql",
        "mysql+pymysql": "mysql",
        "postgres": "postgres",
        "postgresql": "postgres",
        "postgresql+psycopg2": "postgres",
        "sqlite": "sqlite",
        "mssql": "mssql",
        "mssql+pymssql": "mssql",
        "mssql+pyodbc": "mssql",
    }

    scheme = parsed.scheme.lower()
    if scheme not in scheme_map:
        raise ValueError(
            f"Unsupported database scheme: {scheme}. "
            f"Supported: mysql, postgres, postgresql, sqlite, mssql"
        )

    db_type = scheme_map[scheme]

    # Handle SQLite specially - it uses file path, not host/port
    if db_type == "sqlite":
        # SQLite URI: sqlite:///relative/path or sqlite:////absolute/path
        # After urlparse, path contains the file path
        db_path = parsed.path
        if db_path.startswith("//"):
            # sqlite:////absolute/path -> path is //absolute/path
            db_path = db_path[1:]  # Remove leading slash to get /absolute/path
        elif db_path.startswith("/"):
            # sqlite:///relative/path -> path is /relative/path
            db_path = db_path[1:]  # Remove leading slash for relative path

        if not db_path:
            raise ValueError("SQLite URI must include database file path")

        return {
            "db_type": "sqlite",
            "db_host": "",
            "db_port": 0,
            "db_user": "",
            "db_password": "",
            "db_name": db_path,
        }

    # For other database types, require host
    if not parsed.hostname:
        raise ValueError(f"Database URI must include hostname for {db_type}")

    # Default ports
    default_ports = {
        "mysql": 3306,
        "postgres": 5432,
        "mssql": 1433,
    }

    # Extract database name from path (remove leading /)
    db_name = parsed.path.lstrip("/") if parsed.path else ""
    if not db_name:
        raise ValueError("Database URI must include database name")

    # URL-decode username and password for special characters
    username = unquote(parsed.username) if parsed.username else ""
    password = unquote(parsed.password) if parsed.password else ""

    return {
        "db_type": db_type,
        "db_host": parsed.hostname,
        "db_port": parsed.port or default_ports.get(db_type, 0),
        "db_user": username,
        "db_password": password,
        "db_name": db_name,
    }


def parse_env_sheet_id(value: str) -> str:
    """Parse sheet ID from environment value, supporting URLs.

    Args:
        value: Raw value from GOOGLE_SHEET_ID env var (URL or raw ID).

    Returns:
        Extracted sheet ID, or original value if parsing fails.
    """
    if not value:
        return ""
    from mysql_to_sheets.core.sheets_utils import parse_sheet_id

    try:
        return parse_sheet_id(value)
    except ValueError:
        # Let validation catch invalid IDs later
        return value


# Patterns that indicate placeholder values
PLACEHOLDER_PATTERNS = [
    re.compile(r"^your[_-]", re.IGNORECASE),  # your_password, your-database
    re.compile(r"^<.+>$"),  # <your_password>
    re.compile(r"^\[.+\]$"),  # [your_password]
    re.compile(r"^x{3,}$", re.IGNORECASE),  # xxx, xxxx, XXX
    re.compile(r"^placeholder$", re.IGNORECASE),  # placeholder
    re.compile(r"^example$", re.IGNORECASE),  # example
    re.compile(r"^changeme$", re.IGNORECASE),  # changeme
    re.compile(r"^change[_-]?me$", re.IGNORECASE),  # CHANGE_ME, CHANGE-ME
    re.compile(r"^todo$", re.IGNORECASE),  # TODO
    re.compile(r"^test$", re.IGNORECASE),  # test (only exact match)
    re.compile(r"^sample$", re.IGNORECASE),  # sample
    re.compile(r"^demo$", re.IGNORECASE),  # demo
]


def is_placeholder(value: str) -> bool:
    """Check if a value looks like an unmodified placeholder.

    Args:
        value: The value to check.

    Returns:
        True if the value matches a common placeholder pattern.
    """
    if not value:
        return False
    value_stripped = value.strip()
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.match(value_stripped):
            return True
    return False


# Backward compatibility aliases
_parse_bool = parse_bool
_safe_parse_int = safe_parse_int
_safe_parse_float = safe_parse_float
_parse_env_sheet_id = parse_env_sheet_id
_is_placeholder = is_placeholder
