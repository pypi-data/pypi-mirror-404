"""Worksheets API blueprint for web dashboard.

Handles worksheet management operations (list, create, delete) for Google Sheets.
No authentication required - accessible like the main dashboard.
"""

import logging
from typing import TYPE_CHECKING, Any

import gspread
from flask import Blueprint, Response, jsonify, request

from mysql_to_sheets.core.config import get_config, reset_config
from mysql_to_sheets.core.exceptions import SheetsError
from mysql_to_sheets.core.sheets_utils import (
    create_worksheet,
    delete_worksheet,
    list_worksheets,
    parse_sheet_id,
)

if TYPE_CHECKING:
    import gspread

logger = logging.getLogger("mysql_to_sheets.web.api.worksheets")

worksheets_api_bp = Blueprint("worksheets_api", __name__, url_prefix="/api/worksheets")


def _get_spreadsheet(sheet_id: str | None = None) -> Any:
    """Get spreadsheet connection using config or override.

    Args:
        sheet_id: Optional sheet ID or URL to override config.

    Returns:
        An open gspread Spreadsheet object.

    Raises:
        SheetsError: If connection or authentication fails.
    """
    reset_config()
    config = get_config()

    try:
        target_id = parse_sheet_id(sheet_id) if sheet_id else config.google_sheet_id
    except ValueError as e:
        raise SheetsError(
            message=str(e),
            sheet_id=sheet_id or "",
        ) from e

    if not target_id:
        raise SheetsError(
            message="No sheet ID provided and GOOGLE_SHEET_ID not configured",
            sheet_id="",
        )

    try:
        gc = gspread.service_account(filename=config.service_account_file)  # type: ignore[attr-defined]
        return gc.open_by_key(target_id)
    except FileNotFoundError as e:
        raise SheetsError(
            message=f"Service account file not found: {config.service_account_file}",
            sheet_id=target_id,
            original_error=e,
        ) from e
    except gspread.exceptions.APIError as e:
        error_str = str(e).lower()
        if "not found" in error_str:
            raise SheetsError(
                message="Spreadsheet not found or not shared with service account",
                sheet_id=target_id,
                original_error=e,
            ) from e
        raise SheetsError(
            message=f"Google Sheets API error: {e}",
            sheet_id=target_id,
            original_error=e,
        ) from e


@worksheets_api_bp.route("", methods=["GET"])
def list_all() -> tuple[Response, int]:
    """List all worksheets in the configured spreadsheet.

    Query params:
    - sheet_id: Optional sheet ID or URL to override config

    Returns:
        JSON response with worksheet list.
    """
    sheet_id = request.args.get("sheet_id")

    try:
        spreadsheet = _get_spreadsheet(sheet_id)
        worksheets = list_worksheets(spreadsheet)

        return jsonify(
            {
                "success": True,
                "worksheets": worksheets,
                "spreadsheet_title": spreadsheet.title,
                "spreadsheet_id": spreadsheet.id,
                "total": len(worksheets),
            }
        ), 200

    except SheetsError as e:
        logger.warning(f"Failed to list worksheets: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 400
    except Exception as e:
        logger.exception(f"Unexpected error listing worksheets: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 500


@worksheets_api_bp.route("", methods=["POST"])
def create() -> tuple[Response, int]:
    """Create a new worksheet in the spreadsheet.

    Expects JSON body with:
    - title: Worksheet name (required)
    - rows: Number of rows (optional, default: 1000)
    - cols: Number of columns (optional, default: 26)
    - sheet_id: Optional sheet ID or URL to override config

    Returns:
        JSON response with created worksheet info.
    """
    data = request.get_json() or {}

    title = data.get("title", "").strip()
    if not title:
        return jsonify(
            {
                "success": False,
                "error": "Worksheet title is required",
                "message": "Worksheet title is required",
            }
        ), 400

    rows = data.get("rows", 1000)
    cols = data.get("cols", 26)
    sheet_id = data.get("sheet_id")

    # Validate rows and cols
    try:
        rows = int(rows)
        cols = int(cols)
        if rows < 1 or rows > 10000000:
            raise ValueError("Rows must be between 1 and 10,000,000")
        if cols < 1 or cols > 18278:
            raise ValueError("Columns must be between 1 and 18,278")
    except (ValueError, TypeError) as e:
        return jsonify(
            {
                "success": False,
                "error": str(e) if "must be" in str(e) else "Invalid rows or cols value",
                "message": str(e) if "must be" in str(e) else "Invalid rows or cols value",
            }
        ), 400

    try:
        spreadsheet = _get_spreadsheet(sheet_id)
        worksheet = create_worksheet(spreadsheet, title, rows, cols, logger)

        return jsonify(
            {
                "success": True,
                "message": f"Worksheet '{title}' created successfully",
                "worksheet": {
                    "title": worksheet.title,
                    "gid": worksheet.id,
                    "rows": worksheet.row_count,
                    "cols": worksheet.col_count,
                },
            }
        ), 201

    except SheetsError as e:
        logger.warning(f"Failed to create worksheet: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 400
    except Exception as e:
        logger.exception(f"Unexpected error creating worksheet: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 500


@worksheets_api_bp.route("/<title>", methods=["DELETE"])
def delete(title: str) -> tuple[Response, int]:
    """Delete a worksheet from the spreadsheet.

    Args:
        title: Name of the worksheet to delete.

    Query params:
    - sheet_id: Optional sheet ID or URL to override config

    Returns:
        JSON response confirming deletion.
    """
    sheet_id = request.args.get("sheet_id")

    if not title or not title.strip():
        return jsonify(
            {
                "success": False,
                "error": "Worksheet title is required",
                "message": "Worksheet title is required",
            }
        ), 400

    try:
        spreadsheet = _get_spreadsheet(sheet_id)
        delete_worksheet(spreadsheet, title, logger)

        return jsonify(
            {
                "success": True,
                "message": f"Worksheet '{title}' deleted successfully",
            }
        ), 200

    except SheetsError as e:
        logger.warning(f"Failed to delete worksheet: {e}")
        status_code = 404 if "not found" in str(e).lower() else 400
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), status_code
    except Exception as e:
        logger.exception(f"Unexpected error deleting worksheet: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 500
