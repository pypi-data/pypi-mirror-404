"""Google Sheets utility functions."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

import gspread

from mysql_to_sheets.core.exceptions import ErrorCode, SheetsError

if TYPE_CHECKING:
    from gspread import Spreadsheet, Worksheet  # type: ignore[attr-defined]

# Regex pattern to extract sheet ID from Google Sheets URL
# Matches: https://docs.google.com/spreadsheets/d/SHEET_ID/...
GOOGLE_SHEETS_URL_PATTERN = re.compile(
    r"^https?://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)"
)

# Pattern for valid sheet IDs (alphanumeric, underscores, hyphens)
SHEET_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

# Pattern to extract GID from URL fragment (e.g., #gid=123)
WORKSHEET_GID_PATTERN = re.compile(r"#gid=(\d+)")

# Patterns for other Google services (EC-33: Wrong Google Service URL)
GOOGLE_DOCS_URL_PATTERN = re.compile(r"^https?://docs\.google\.com/document/d/")
GOOGLE_FORMS_URL_PATTERN = re.compile(r"^https?://docs\.google\.com/forms/d/")
GOOGLE_SLIDES_URL_PATTERN = re.compile(r"^https?://docs\.google\.com/presentation/d/")
GOOGLE_DRIVE_URL_PATTERN = re.compile(r"^https?://drive\.google\.com/")


def validate_google_url(value: str) -> tuple[bool, str | None]:
    """Validate that a value is not a wrong Google service URL.

    This is used to detect when users accidentally paste a Google Docs,
    Forms, Slides, or Drive URL instead of a Google Sheets URL.

    Args:
        value: A potential Google Sheets URL or ID.

    Returns:
        Tuple of (is_valid, error_message). is_valid is True if the URL
        is valid or not a URL at all. error_message contains helpful
        guidance if a wrong service URL is detected.
    """
    if not value:
        return True, None

    value = value.strip()

    # Only check if it looks like a URL
    if not value.startswith(("http://", "https://")):
        return True, None

    # Check for wrong Google services FIRST (before checking if it's a valid Sheets URL)
    if GOOGLE_DOCS_URL_PATTERN.match(value):
        return False, (
            "This is a Google Docs URL, not a Google Sheets URL. "
            "Open your spreadsheet and copy the URL from the browser address bar. "
            "It should look like: https://docs.google.com/spreadsheets/d/SHEET_ID/..."
        )

    if GOOGLE_FORMS_URL_PATTERN.match(value):
        return False, (
            "This is a Google Forms URL, not a Google Sheets URL. "
            "To sync form responses, open the linked spreadsheet from "
            "Forms > Responses tab > 'View in Sheets' button, then copy that URL."
        )

    if GOOGLE_SLIDES_URL_PATTERN.match(value):
        return False, (
            "This is a Google Slides URL, not a Google Sheets URL. "
            "Open your spreadsheet and copy the URL from the browser address bar. "
            "It should look like: https://docs.google.com/spreadsheets/d/SHEET_ID/..."
        )

    if GOOGLE_DRIVE_URL_PATTERN.match(value):
        return False, (
            "This is a Google Drive URL. Please open the spreadsheet directly "
            "and copy the URL. It should look like: "
            "https://docs.google.com/spreadsheets/d/SHEET_ID/..."
        )

    # Not a wrong service URL
    return True, None


def parse_sheet_id(value: str) -> str:
    """Extract Google Sheet ID from URL or return raw ID.

    Accepts:
    - Full URL: https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=0
    - Full URL: https://docs.google.com/spreadsheets/d/SHEET_ID/edit
    - Full URL: https://docs.google.com/spreadsheets/d/SHEET_ID
    - Raw ID: 1a2B3c4D5e6F7g8h9i0j1k2l3m4n5o6p

    Args:
        value: A Google Sheets URL or raw sheet ID.

    Returns:
        The extracted sheet ID.

    Raises:
        ValueError: If URL format is invalid, ID cannot be extracted,
            or if the URL is for a different Google service (Docs, Forms, etc.).
    """
    value = value.strip()

    if not value:
        raise ValueError("Sheet ID cannot be empty")

    # Check if it looks like a URL
    if value.startswith(("http://", "https://")):
        # Check for wrong Google services FIRST (EC-33)
        is_valid, error_message = validate_google_url(value)
        if not is_valid:
            raise ValueError(error_message)

        # Now try to extract sheet ID from Sheets URL
        match = GOOGLE_SHEETS_URL_PATTERN.match(value)
        if not match:
            raise ValueError(
                "Invalid Google Sheets URL format. Expected: "
                "https://docs.google.com/spreadsheets/d/SHEET_ID/..."
            )
        return match.group(1)

    # Assume it's a raw sheet ID - validate format
    if not SHEET_ID_PATTERN.match(value):
        raise ValueError(
            "Invalid sheet ID format. Must contain only letters, numbers, underscores, and hyphens."
        )

    return value


def is_sheets_url(value: str) -> bool:
    """Check if a string looks like a Google Sheets URL.

    Args:
        value: String to check.

    Returns:
        True if it appears to be a Google Sheets URL.
    """
    return value.strip().startswith(("http://", "https://"))


def parse_worksheet_gid(value: str) -> int | None:
    """Extract worksheet GID from a URL fragment.

    Args:
        value: A string that may contain #gid=NNN fragment.

    Returns:
        The GID as an integer, or None if not found.

    Examples:
        >>> parse_worksheet_gid("https://...#gid=123")
        123
        >>> parse_worksheet_gid("Sheet1")
        None
    """
    match = WORKSHEET_GID_PATTERN.search(value)
    if match:
        return int(match.group(1))
    return None


def is_worksheet_url(value: str) -> bool:
    """Check if a value is a URL with a #gid= fragment.

    Args:
        value: String to check.

    Returns:
        True if value appears to be a URL with a GID fragment.
    """
    if not value:
        return False
    stripped = value.strip()
    return stripped.startswith(("http://", "https://")) and "#gid=" in stripped


def resolve_worksheet_name_from_gid(
    spreadsheet: Spreadsheet,
    gid: int,
) -> str:
    """Resolve a worksheet GID to its name via API lookup.

    Args:
        spreadsheet: An open gspread Spreadsheet object.
        gid: The worksheet GID (sheet_id property).

    Returns:
        The worksheet name (title).

    Raises:
        ValueError: If no worksheet with the given GID exists.
    """
    for worksheet in spreadsheet.worksheets():
        if worksheet.id == gid:
            return str(worksheet.title)

    # Build helpful error message with available GIDs
    available = [f"{ws.title} (gid={ws.id})" for ws in spreadsheet.worksheets()]
    raise ValueError(
        f"Worksheet with GID {gid} not found in spreadsheet. "
        f"Available worksheets: {', '.join(available)}"
    )


def parse_worksheet_identifier(
    value: str,
    spreadsheet: Spreadsheet | None = None,
) -> str:
    """Parse a worksheet identifier, resolving GID URLs to names.

    This is the main entry point for worksheet name resolution. It handles:
    - Plain worksheet names (returned as-is)
    - URLs with #gid= fragments (resolved to worksheet name via API)
    - URLs without GID (returns "Sheet1" default)
    - Empty values (returns "Sheet1" default)

    Args:
        value: Worksheet name or Google Sheets URL with #gid= fragment.
        spreadsheet: An open gspread Spreadsheet object (required for GID resolution).

    Returns:
        The resolved worksheet name.

    Raises:
        ValueError: If value contains a GID but spreadsheet is not provided,
            or if the GID doesn't exist in the spreadsheet.

    Examples:
        >>> parse_worksheet_identifier("Sheet1")
        "Sheet1"
        >>> parse_worksheet_identifier("https://...#gid=0", spreadsheet)
        "Sheet1"  # if GID 0 corresponds to Sheet1
    """
    if not value or not value.strip():
        return "Sheet1"

    value = value.strip()

    # Check if it looks like a URL (might have GID or not)
    if is_sheets_url(value):
        gid = parse_worksheet_gid(value)
        if gid is not None:
            if spreadsheet is None:
                raise ValueError(
                    "Cannot resolve worksheet GID without an open spreadsheet. "
                    "Please provide the spreadsheet parameter."
                )
            return resolve_worksheet_name_from_gid(spreadsheet, gid)
        # URL without GID - return default
        return "Sheet1"

    # Plain worksheet name - return as-is
    return value


def create_worksheet(
    spreadsheet: Spreadsheet,
    title: str,
    rows: int = 1000,
    cols: int = 26,
    logger: logging.Logger | None = None,
) -> Worksheet:
    """Create a new worksheet in the spreadsheet.

    Args:
        spreadsheet: An open gspread Spreadsheet object.
        title: Name for the new worksheet.
        rows: Number of rows (default 1000).
        cols: Number of columns (default 26, i.e., A-Z).
        logger: Optional logger instance.

    Returns:
        The newly created Worksheet object.

    Raises:
        SheetsError: If worksheet creation fails (e.g., name already exists).
    """
    if logger:
        logger.info(f"Creating worksheet '{title}' ({rows} rows x {cols} cols)")

    try:
        worksheet = spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)
        if logger:
            logger.info(f"Successfully created worksheet '{title}'")
        return worksheet
    except gspread.exceptions.APIError as e:
        error_str = str(e).lower()
        if "already exists" in error_str or "duplicate" in error_str:
            raise SheetsError(
                message=f"Worksheet '{title}' already exists in the spreadsheet",
                sheet_id=spreadsheet.id,
                worksheet_name=title,
                original_error=e,
                code=ErrorCode.SHEETS_API_ERROR,
            ) from e
        raise SheetsError(
            message=f"Failed to create worksheet '{title}': {e}",
            sheet_id=spreadsheet.id,
            worksheet_name=title,
            original_error=e,
            code=ErrorCode.SHEETS_API_ERROR,
        ) from e


def delete_worksheet(
    spreadsheet: Spreadsheet,
    title: str,
    logger: logging.Logger | None = None,
) -> bool:
    """Delete a worksheet from the spreadsheet.

    Args:
        spreadsheet: An open gspread Spreadsheet object.
        title: Name of the worksheet to delete.
        logger: Optional logger instance.

    Returns:
        True if worksheet was deleted successfully.

    Raises:
        SheetsError: If worksheet not found or deletion fails.
    """
    if logger:
        logger.info(f"Deleting worksheet '{title}'")

    try:
        worksheet = spreadsheet.worksheet(title)
        spreadsheet.del_worksheet(worksheet)
        if logger:
            logger.info(f"Successfully deleted worksheet '{title}'")
        return True
    except gspread.exceptions.WorksheetNotFound as e:
        raise SheetsError(
            message=f"Worksheet '{title}' not found",
            sheet_id=spreadsheet.id,
            worksheet_name=title,
            original_error=e,
            code=ErrorCode.SHEETS_WORKSHEET_NOT_FOUND,
        ) from e
    except gspread.exceptions.APIError as e:
        error_str = str(e).lower()
        if "cannot delete" in error_str or "last sheet" in error_str:
            raise SheetsError(
                message="Cannot delete the last worksheet in a spreadsheet",
                sheet_id=spreadsheet.id,
                worksheet_name=title,
                original_error=e,
                code=ErrorCode.SHEETS_API_ERROR,
            ) from e
        raise SheetsError(
            message=f"Failed to delete worksheet '{title}': {e}",
            sheet_id=spreadsheet.id,
            worksheet_name=title,
            original_error=e,
            code=ErrorCode.SHEETS_API_ERROR,
        ) from e


def list_worksheets(
    spreadsheet: Spreadsheet,
) -> list[dict[str, Any]]:
    """List all worksheets in a spreadsheet.

    Args:
        spreadsheet: An open gspread Spreadsheet object.

    Returns:
        List of worksheet info dicts with 'title', 'gid', 'rows', 'cols'.
    """
    worksheets = []
    for ws in spreadsheet.worksheets():
        worksheets.append(
            {
                "title": ws.title,
                "gid": ws.id,
                "rows": ws.row_count,
                "cols": ws.col_count,
            }
        )
    return worksheets


def get_or_create_worksheet(
    spreadsheet: Spreadsheet,
    title: str,
    create_if_missing: bool = False,
    rows: int = 1000,
    cols: int = 26,
    logger: logging.Logger | None = None,
) -> Worksheet:
    """Get a worksheet by name, optionally creating it if missing.

    This is the recommended way to get a worksheet when you want
    auto-creation behavior. It combines lookup and creation in a
    single operation.

    Args:
        spreadsheet: An open gspread Spreadsheet object.
        title: Name of the worksheet to get or create.
        create_if_missing: If True, create the worksheet if it doesn't exist.
        rows: Number of rows for new worksheet (default 1000).
        cols: Number of columns for new worksheet (default 26).
        logger: Optional logger instance.

    Returns:
        The Worksheet object (existing or newly created).

    Raises:
        SheetsError: If worksheet not found and create_if_missing is False,
            or if creation fails.
    """
    try:
        worksheet = spreadsheet.worksheet(title)
        if logger:
            logger.debug(f"Found existing worksheet '{title}'")
        return worksheet
    except gspread.exceptions.WorksheetNotFound:
        if create_if_missing:
            if logger:
                logger.info(f"Worksheet '{title}' not found, creating it")
            return create_worksheet(spreadsheet, title, rows, cols, logger)
        else:
            # Provide a helpful error message with available worksheets
            available = [ws.title for ws in spreadsheet.worksheets()]
            hint = (
                f"Available worksheets: {', '.join(available)}. "
                "Use --create-worksheet to auto-create missing worksheets."
            )
            raise SheetsError(
                message=f"Worksheet '{title}' not found. {hint}",
                sheet_id=spreadsheet.id,
                worksheet_name=title,
                code=ErrorCode.SHEETS_WORKSHEET_NOT_FOUND,
            )
