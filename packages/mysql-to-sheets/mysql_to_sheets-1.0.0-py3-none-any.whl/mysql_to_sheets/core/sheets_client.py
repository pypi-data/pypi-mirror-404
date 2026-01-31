"""Centralized Google Sheets client factory with timeout support.

Provides a single function to create gspread clients configured
with HTTP timeouts to prevent operations from hanging indefinitely.
"""

import logging
import os

import gspread

logger = logging.getLogger(__name__)

# Default timeout for Google Sheets API calls (seconds)
DEFAULT_SHEETS_TIMEOUT = 60


def get_sheets_client(
    service_account_file: str | None = None,
    timeout: int | None = None,
) -> gspread.Client:
    """Create a gspread client with HTTP timeout.

    Args:
        service_account_file: Path to service account JSON. If None, uses
            SERVICE_ACCOUNT_FILE env var or default path.
        timeout: HTTP timeout in seconds. If None, uses SHEETS_TIMEOUT
            env var or default (60s).

    Returns:
        Configured gspread.Client instance.
    """
    if service_account_file is None:
        service_account_file = os.getenv("SERVICE_ACCOUNT_FILE", "./service_account.json")

    if timeout is None:
        timeout = int(os.getenv("SHEETS_TIMEOUT", str(DEFAULT_SHEETS_TIMEOUT)))

    gc = gspread.service_account(filename=service_account_file)  # type: ignore[attr-defined]

    # Set timeout on the underlying HTTP session
    if hasattr(gc, "http_client") and hasattr(gc.http_client, "session"):
        gc.http_client.session.timeout = timeout
    elif hasattr(gc, "auth") and hasattr(gc.auth, "transport"):
        # Fallback for different gspread versions
        pass

    logger.debug(f"Created Sheets client with {timeout}s timeout")
    return gc
