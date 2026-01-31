"""Google Sheets destination adapter.

This module encapsulates all gspread usage, providing a clean interface
that implements the DestinationConnection protocol.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

import gspread

from mysql_to_sheets.core.exceptions import ErrorCode, SheetsError

from .base import BaseDestinationConnection, DestinationConfig, WriteResult

if TYPE_CHECKING:
    from gspread import Client, Spreadsheet, Worksheet  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)

# Default timeout for Google Sheets API calls (seconds)
DEFAULT_SHEETS_TIMEOUT = 60


class GoogleSheetsDestination(BaseDestinationConnection):
    """Google Sheets destination adapter using gspread.

    This adapter encapsulates all gspread interactions, providing a clean
    interface for writing data to Google Sheets.

    Example:
        >>> config = DestinationConfig(
        ...     destination_type="google_sheets",
        ...     target_id="1a2B3c4D5e6F7g8h9i0j1k2l3m4n5o6p",
        ...     target_name="Sheet1",
        ...     credentials_file="./service_account.json",
        ... )
        >>> with GoogleSheetsDestination(config) as dest:
        ...     result = dest.write(["Name", "Age"], [["Alice", 30], ["Bob", 25]])
        ...     print(f"Wrote {result.rows_written} rows")
    """

    _destination_type = "google_sheets"

    def __init__(self, config: DestinationConfig) -> None:
        """Initialize the Google Sheets destination.

        Args:
            config: Destination configuration with sheet_id and worksheet name.
        """
        super().__init__(config)
        self._client: Client | None = None
        self._spreadsheet: Spreadsheet | None = None
        self._worksheet: Worksheet | None = None

    @property
    def destination_type(self) -> str:
        """Return the destination type identifier."""
        return self._destination_type

    @property
    def spreadsheet(self) -> Spreadsheet:
        """Get the connected spreadsheet.

        Returns:
            The gspread Spreadsheet object.

        Raises:
            SheetsError: If not connected.
        """
        if self._spreadsheet is None:
            raise SheetsError(
                message="Not connected to Google Sheets. Call connect() first.",
                code=ErrorCode.SHEETS_API_ERROR,
            )
        return self._spreadsheet

    @property
    def worksheet(self) -> Worksheet:
        """Get the connected worksheet.

        Returns:
            The gspread Worksheet object.

        Raises:
            SheetsError: If not connected.
        """
        if self._worksheet is None:
            raise SheetsError(
                message="No worksheet selected. Call connect() first.",
                code=ErrorCode.SHEETS_WORKSHEET_NOT_FOUND,
            )
        return self._worksheet

    def connect(self) -> None:
        """Establish connection to Google Sheets.

        Opens the spreadsheet and selects the target worksheet.

        Raises:
            SheetsError: If authentication fails, spreadsheet not found,
                or worksheet not found.
        """
        if self._connected:
            return

        credentials_file = self.config.credentials_file
        if credentials_file is None:
            credentials_file = os.getenv("SERVICE_ACCOUNT_FILE", "./service_account.json")

        timeout = self.config.timeout or int(
            os.getenv("SHEETS_TIMEOUT", str(DEFAULT_SHEETS_TIMEOUT))
        )

        try:
            # Create authenticated client
            self._client = gspread.service_account(filename=credentials_file)  # type: ignore[attr-defined]

            # Set timeout on the underlying HTTP session
            if hasattr(self._client, "http_client") and hasattr(
                self._client.http_client, "session"
            ):
                self._client.http_client.session.timeout = timeout

            logger.debug(f"Created Sheets client with {timeout}s timeout")

        except FileNotFoundError as e:
            raise SheetsError(
                message=f"Service account file not found: {credentials_file}",
                original_error=e,
                code=ErrorCode.SHEETS_AUTH_FAILED,
            ) from e
        except Exception as e:
            raise SheetsError(
                message=f"Failed to authenticate with Google Sheets: {e}",
                original_error=e,
                code=ErrorCode.SHEETS_AUTH_FAILED,
            ) from e

        # Open spreadsheet
        try:
            self._spreadsheet = self._client.open_by_key(self.config.target_id)
            logger.debug(f"Opened spreadsheet: {self.config.target_id}")
        except gspread.exceptions.SpreadsheetNotFound as e:
            raise SheetsError(
                message=f"Spreadsheet not found: {self.config.target_id}",
                sheet_id=self.config.target_id,
                original_error=e,
                code=ErrorCode.SHEETS_NOT_FOUND,
            ) from e
        except gspread.exceptions.APIError as e:
            error_str = str(e).lower()
            if "permission" in error_str or "403" in error_str:
                raise SheetsError(
                    message=(
                        f"Permission denied accessing spreadsheet {self.config.target_id}. "
                        "Ensure the service account email has edit access."
                    ),
                    sheet_id=self.config.target_id,
                    original_error=e,
                    code=ErrorCode.SHEETS_PERMISSION_DENIED,
                ) from e
            raise SheetsError(
                message=f"Failed to open spreadsheet: {e}",
                sheet_id=self.config.target_id,
                original_error=e,
                code=ErrorCode.SHEETS_API_ERROR,
            ) from e

        # Select worksheet
        worksheet_name = self.config.target_name or "Sheet1"
        create_if_missing = self.config.options.get("create_if_missing", False)

        try:
            self._worksheet = self._spreadsheet.worksheet(worksheet_name)
            logger.debug(f"Selected worksheet: {worksheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            if create_if_missing:
                rows = self.config.options.get("default_rows", 1000)
                cols = self.config.options.get("default_cols", 26)
                logger.info(f"Creating worksheet '{worksheet_name}' ({rows}x{cols})")
                self._worksheet = self._spreadsheet.add_worksheet(
                    title=worksheet_name, rows=rows, cols=cols
                )
            else:
                available = [ws.title for ws in self._spreadsheet.worksheets()]
                raise SheetsError(
                    message=(
                        f"Worksheet '{worksheet_name}' not found. "
                        f"Available: {', '.join(available)}. "
                        "Use create_if_missing=True to auto-create."
                    ),
                    sheet_id=self.config.target_id,
                    worksheet_name=worksheet_name,
                    code=ErrorCode.SHEETS_WORKSHEET_NOT_FOUND,
                )

        self._connected = True

    def write(
        self,
        headers: list[str],
        rows: list[list[Any]],
        mode: str = "replace",
    ) -> WriteResult:
        """Write data to Google Sheets.

        Args:
            headers: Column headers.
            rows: Data rows to write.
            mode: Write mode - 'replace' clears sheet first, 'append' adds rows.

        Returns:
            WriteResult with operation details.

        Raises:
            SheetsError: If write fails.
        """
        if not self._connected:
            self.connect()

        worksheet = self.worksheet
        total_rows = len(rows)

        try:
            if mode == "replace":
                # Clear existing data and write all at once
                worksheet.clear()

                if headers or rows:
                    # Combine headers and rows into single update
                    all_data = [headers] + rows if headers else rows
                    worksheet.update(all_data, value_input_option="RAW")

                logger.info(f"Replaced sheet with {total_rows} rows")
                return WriteResult(
                    success=True,
                    rows_written=total_rows,
                    message=f"Replaced {total_rows} rows in {self.config.target_name}",
                    metadata={"mode": "replace", "headers": headers},
                )

            elif mode == "append":
                # Append rows to existing data
                if rows:
                    worksheet.append_rows(rows, value_input_option="RAW")

                logger.info(f"Appended {total_rows} rows")
                return WriteResult(
                    success=True,
                    rows_written=total_rows,
                    message=f"Appended {total_rows} rows to {self.config.target_name}",
                    metadata={"mode": "append"},
                )

            else:
                raise SheetsError(
                    message=f"Unsupported write mode: {mode}. Use 'replace' or 'append'.",
                    code=ErrorCode.SHEETS_API_ERROR,
                )

        except gspread.exceptions.APIError as e:
            error_str = str(e).lower()

            if "quota" in error_str or "rate" in error_str or "429" in error_str:
                raise SheetsError(
                    message="Google Sheets API rate limit exceeded. Wait and retry.",
                    sheet_id=self.config.target_id,
                    worksheet_name=self.config.target_name,
                    original_error=e,
                    rate_limited=True,
                    retry_after=60.0,
                    code=ErrorCode.SHEETS_RATE_LIMITED,
                ) from e

            raise SheetsError(
                message=f"Failed to write to sheet: {e}",
                sheet_id=self.config.target_id,
                worksheet_name=self.config.target_name,
                original_error=e,
                code=ErrorCode.SHEETS_API_ERROR,
            ) from e

    def read(self) -> tuple[list[str], list[list[Any]]]:
        """Read all data from the worksheet.

        Returns:
            Tuple of (headers, data_rows). Headers is the first row,
            data_rows is all subsequent rows.

        Raises:
            SheetsError: If read fails.
        """
        if not self._connected:
            self.connect()

        try:
            all_values = self.worksheet.get_all_values()

            if not all_values:
                return [], []

            headers = all_values[0]
            rows = all_values[1:] if len(all_values) > 1 else []

            logger.debug(f"Read {len(rows)} rows from {self.config.target_name}")
            return headers, rows

        except gspread.exceptions.APIError as e:
            raise SheetsError(
                message=f"Failed to read from sheet: {e}",
                sheet_id=self.config.target_id,
                worksheet_name=self.config.target_name,
                original_error=e,
                code=ErrorCode.SHEETS_API_ERROR,
            ) from e

    def clear(self) -> None:
        """Clear all data from the worksheet.

        Raises:
            SheetsError: If clear fails.
        """
        if not self._connected:
            self.connect()

        try:
            self.worksheet.clear()
            logger.debug(f"Cleared worksheet {self.config.target_name}")

        except gspread.exceptions.APIError as e:
            raise SheetsError(
                message=f"Failed to clear sheet: {e}",
                sheet_id=self.config.target_id,
                worksheet_name=self.config.target_name,
                original_error=e,
                code=ErrorCode.SHEETS_API_ERROR,
            ) from e

    def close(self) -> None:
        """Close the Google Sheets connection.

        Note: gspread doesn't maintain persistent connections, so this
        primarily clears internal state.
        """
        self._client = None
        self._spreadsheet = None
        self._worksheet = None
        self._connected = False
        logger.debug("Closed Google Sheets connection")

    def test_connection(self) -> bool:
        """Test if the Google Sheets connection is valid.

        Returns:
            True if connection successful and worksheet accessible.
        """
        try:
            self.connect()
            # Verify we can access the worksheet
            _ = self.worksheet.title
            return True
        except Exception:
            return False
        finally:
            self.close()

    # Additional Google Sheets-specific methods

    def get_worksheet_info(self) -> dict[str, Any]:
        """Get information about the current worksheet.

        Returns:
            Dict with title, gid, row_count, col_count.
        """
        if not self._connected:
            self.connect()

        ws = self.worksheet
        return {
            "title": ws.title,
            "gid": ws.id,
            "row_count": ws.row_count,
            "col_count": ws.col_count,
        }

    def list_worksheets(self) -> list[dict[str, Any]]:
        """List all worksheets in the spreadsheet.

        Returns:
            List of dicts with title, gid, row_count, col_count for each worksheet.
        """
        if not self._connected:
            self.connect()

        worksheets = []
        for ws in self.spreadsheet.worksheets():
            worksheets.append(
                {
                    "title": ws.title,
                    "gid": ws.id,
                    "row_count": ws.row_count,
                    "col_count": ws.col_count,
                }
            )
        return worksheets

    def select_worksheet(self, name: str, create_if_missing: bool = False) -> None:
        """Switch to a different worksheet.

        Args:
            name: Worksheet name to select.
            create_if_missing: If True, create the worksheet if it doesn't exist.

        Raises:
            SheetsError: If worksheet not found and create_if_missing is False.
        """
        if not self._connected:
            self.connect()

        try:
            self._worksheet = self.spreadsheet.worksheet(name)
            self.config.target_name = name
            logger.debug(f"Selected worksheet: {name}")
        except gspread.exceptions.WorksheetNotFound:
            if create_if_missing:
                rows = self.config.options.get("default_rows", 1000)
                cols = self.config.options.get("default_cols", 26)
                self._worksheet = self.spreadsheet.add_worksheet(
                    title=name, rows=rows, cols=cols
                )
                self.config.target_name = name
                logger.info(f"Created worksheet: {name}")
            else:
                available = [ws.title for ws in self.spreadsheet.worksheets()]
                raise SheetsError(
                    message=f"Worksheet '{name}' not found. Available: {', '.join(available)}",
                    sheet_id=self.config.target_id,
                    worksheet_name=name,
                    code=ErrorCode.SHEETS_WORKSHEET_NOT_FOUND,
                )
