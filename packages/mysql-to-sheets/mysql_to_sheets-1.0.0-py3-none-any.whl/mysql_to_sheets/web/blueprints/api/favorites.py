"""Favorites API blueprint for web dashboard.

Handles favorite queries and sheets CRUD operations via AJAX (multi-tenant).
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request

from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.web.blueprints.api.auth_helpers import (
    _get_user_or_401,
    _require_login,
)
from mysql_to_sheets.web.context import get_current_user

logger = logging.getLogger("mysql_to_sheets.web.api.favorites")

favorites_api_bp = Blueprint("favorites_api", __name__, url_prefix="/api/favorites")


# =============================================================================
# Query Endpoints
# =============================================================================


@favorites_api_bp.route("/queries", methods=["GET"])
def list_queries() -> tuple[Response, int]:
    """List favorite queries in current organization.

    Query params:
    - include_inactive: If true, include inactive favorites

    Returns:
        JSON response with query list.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import get_favorite_query_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    include_inactive = request.args.get("include_inactive", "false").lower() == "true"

    db_path = get_tenant_db_path()
    query_repo = get_favorite_query_repository(db_path)

    queries = query_repo.get_all(
        organization_id=current["organization_id"],
        user_id=current["id"],
        include_inactive=include_inactive,
    )

    return jsonify(
        {
            "success": True,
            "queries": [q.to_dict() for q in queries],
            "total": len(queries),
        }
    ), 200


@favorites_api_bp.route("/queries", methods=["POST"])
def create_query() -> tuple[Response, int]:
    """Create a new favorite query.

    Expects JSON body with:
    - name: Query name (required)
    - sql_query: SQL query string (required)
    - description: Optional description
    - tags: Optional list of tags
    - is_private: Optional boolean (default: false)

    Returns:
        JSON response with created query.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import FavoriteQuery, get_favorite_query_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    # Validation
    if not data.get("name"):
        return jsonify(
            {"success": False, "error": "Name is required", "message": "Name is required"}
        ), 400
    if not data.get("sql_query"):
        return jsonify(
            {"success": False, "error": "SQL query is required", "message": "SQL query is required"}
        ), 400

    try:
        db_path = get_tenant_db_path()
        query_repo = get_favorite_query_repository(db_path)

        favorite = FavoriteQuery(
            name=data["name"].strip(),
            sql_query=data["sql_query"],
            organization_id=current["organization_id"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            is_private=data.get("is_private", False),
            created_by_user_id=current["id"],
        )

        favorite = query_repo.create(favorite)

        return jsonify(
            {
                "success": True,
                "message": "Favorite query created",
                "query": favorite.to_dict(),
            }
        ), 201

    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400
    except Exception as e:
        logger.exception(f"Error creating favorite query: {e}")
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 500


@favorites_api_bp.route("/queries/<int:query_id>", methods=["GET"])
def get_query(query_id: int) -> tuple[Response, int]:
    """Get a favorite query by ID.

    Returns:
        JSON response with query details.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import get_favorite_query_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    query_repo = get_favorite_query_repository(db_path)

    query = query_repo.get_by_id(
        query_id,
        organization_id=current["organization_id"],
        user_id=current["id"],
    )

    if not query:
        return jsonify(
            {
                "success": False,
                "error": f"Query {query_id} not found",
                "message": f"Query {query_id} not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "query": query.to_dict(),
        }
    ), 200


@favorites_api_bp.route("/queries/<int:query_id>", methods=["PUT"])
def update_query(query_id: int) -> tuple[Response, int]:
    """Update a favorite query.

    Returns:
        JSON response with updated query.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import get_favorite_query_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    query_repo = get_favorite_query_repository(db_path)

    query = query_repo.get_by_id(
        query_id,
        organization_id=current["organization_id"],
        user_id=current["id"],
    )

    if not query:
        return jsonify(
            {
                "success": False,
                "error": f"Query {query_id} not found",
                "message": f"Query {query_id} not found",
            }
        ), 404

    # Check ownership for private queries
    if query.is_private and query.created_by_user_id != current["id"]:
        return jsonify(
            {
                "success": False,
                "error": "Cannot edit another user's private query",
                "message": "Cannot edit another user's private query",
            }
        ), 403

    # Apply updates
    if "name" in data:
        query.name = data["name"].strip()
    if "sql_query" in data:
        query.sql_query = data["sql_query"]
    if "description" in data:
        query.description = data["description"]
    if "tags" in data:
        query.tags = data["tags"]
    if "is_private" in data:
        query.is_private = data["is_private"]

    try:
        query = query_repo.update(query)
        return jsonify(
            {
                "success": True,
                "message": "Favorite query updated",
                "query": query.to_dict(),
            }
        ), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400


@favorites_api_bp.route("/queries/<int:query_id>", methods=["DELETE"])
def delete_query(query_id: int) -> tuple[Response, int]:
    """Deactivate a favorite query.

    Query params:
    - hard: If true, permanently delete instead of deactivate

    Returns:
        JSON response confirming deletion.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import get_favorite_query_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    hard_delete = request.args.get("hard", "false").lower() == "true"

    db_path = get_tenant_db_path()
    query_repo = get_favorite_query_repository(db_path)

    query = query_repo.get_by_id(
        query_id,
        organization_id=current["organization_id"],
        user_id=current["id"],
    )

    if not query:
        return jsonify(
            {
                "success": False,
                "error": f"Query {query_id} not found",
                "message": f"Query {query_id} not found",
            }
        ), 404

    # Check ownership for private queries
    if query.is_private and query.created_by_user_id != current["id"]:
        return jsonify(
            {
                "success": False,
                "error": "Cannot delete another user's private query",
                "message": "Cannot delete another user's private query",
            }
        ), 403

    if hard_delete:
        query_repo.delete(query_id, organization_id=current["organization_id"])
        message = f"Query '{query.name}' permanently deleted"
    else:
        query_repo.deactivate(query_id, organization_id=current["organization_id"])
        message = f"Query '{query.name}' deactivated"

    return jsonify(
        {
            "success": True,
            "message": message,
        }
    ), 200


# =============================================================================
# Sheet Endpoints
# =============================================================================


@favorites_api_bp.route("/sheets", methods=["GET"])
def list_sheets() -> tuple[Response, int]:
    """List favorite sheets in current organization.

    Query params:
    - include_inactive: If true, include inactive favorites

    Returns:
        JSON response with sheet list.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import get_favorite_sheet_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    include_inactive = request.args.get("include_inactive", "false").lower() == "true"

    db_path = get_tenant_db_path()
    sheet_repo = get_favorite_sheet_repository(db_path)

    sheets = sheet_repo.get_all(
        organization_id=current["organization_id"],
        user_id=current["id"],
        include_inactive=include_inactive,
    )

    return jsonify(
        {
            "success": True,
            "sheets": [s.to_dict() for s in sheets],
            "total": len(sheets),
        }
    ), 200


@favorites_api_bp.route("/sheets", methods=["POST"])
def create_sheet() -> tuple[Response, int]:
    """Create a new favorite sheet.

    Expects JSON body with:
    - name: Sheet name (required)
    - sheet_id: Google Sheet ID (required)
    - description: Optional description
    - default_worksheet: Optional worksheet name (default: Sheet1)
    - tags: Optional list of tags
    - is_private: Optional boolean (default: false)

    Returns:
        JSON response with created sheet.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import FavoriteSheet, get_favorite_sheet_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    # Validation
    if not data.get("name"):
        return jsonify(
            {"success": False, "error": "Name is required", "message": "Name is required"}
        ), 400
    if not data.get("sheet_id"):
        return jsonify(
            {"success": False, "error": "Sheet ID is required", "message": "Sheet ID is required"}
        ), 400

    # Parse sheet ID from URL or raw ID
    from mysql_to_sheets.core.sheets_utils import parse_sheet_id

    try:
        sheet_id = parse_sheet_id(data["sheet_id"])
    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400

    try:
        db_path = get_tenant_db_path()
        sheet_repo = get_favorite_sheet_repository(db_path)

        favorite = FavoriteSheet(
            name=data["name"].strip(),
            sheet_id=sheet_id,
            organization_id=current["organization_id"],
            description=data.get("description", ""),
            default_worksheet=data.get("default_worksheet", "Sheet1"),
            tags=data.get("tags", []),
            is_private=data.get("is_private", False),
            created_by_user_id=current["id"],
        )

        favorite = sheet_repo.create(favorite)

        return jsonify(
            {
                "success": True,
                "message": "Favorite sheet created",
                "sheet": favorite.to_dict(),
            }
        ), 201

    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400
    except Exception as e:
        logger.exception(f"Error creating favorite sheet: {e}")
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 500


@favorites_api_bp.route("/sheets/<int:sheet_id>", methods=["GET"])
def get_sheet(sheet_id: int) -> tuple[Response, int]:
    """Get a favorite sheet by ID.

    Returns:
        JSON response with sheet details.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import get_favorite_sheet_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    sheet_repo = get_favorite_sheet_repository(db_path)

    sheet = sheet_repo.get_by_id(
        sheet_id,
        organization_id=current["organization_id"],
        user_id=current["id"],
    )

    if not sheet:
        return jsonify(
            {
                "success": False,
                "error": f"Sheet {sheet_id} not found",
                "message": f"Sheet {sheet_id} not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "sheet": sheet.to_dict(),
        }
    ), 200


@favorites_api_bp.route("/sheets/<int:sheet_id>", methods=["PUT"])
def update_sheet(sheet_id: int) -> tuple[Response, int]:
    """Update a favorite sheet.

    Returns:
        JSON response with updated sheet.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import get_favorite_sheet_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    sheet_repo = get_favorite_sheet_repository(db_path)

    sheet = sheet_repo.get_by_id(
        sheet_id,
        organization_id=current["organization_id"],
        user_id=current["id"],
    )

    if not sheet:
        return jsonify(
            {
                "success": False,
                "error": f"Sheet {sheet_id} not found",
                "message": f"Sheet {sheet_id} not found",
            }
        ), 404

    # Check ownership for private sheets
    if sheet.is_private and sheet.created_by_user_id != current["id"]:
        return jsonify(
            {
                "success": False,
                "error": "Cannot edit another user's private sheet",
                "message": "Cannot edit another user's private sheet",
            }
        ), 403

    # Apply updates
    if "name" in data:
        sheet.name = data["name"].strip()
    if "sheet_id" in data:
        # Parse sheet ID from URL or raw ID
        from mysql_to_sheets.core.sheets_utils import parse_sheet_id

        try:
            sheet.sheet_id = parse_sheet_id(data["sheet_id"])
        except ValueError as e:
            return jsonify({"success": False, "error": str(e), "message": str(e)}), 400
    if "description" in data:
        sheet.description = data["description"]
    if "default_worksheet" in data:
        sheet.default_worksheet = data["default_worksheet"]
    if "tags" in data:
        sheet.tags = data["tags"]
    if "is_private" in data:
        sheet.is_private = data["is_private"]

    try:
        sheet = sheet_repo.update(sheet)
        return jsonify(
            {
                "success": True,
                "message": "Favorite sheet updated",
                "sheet": sheet.to_dict(),
            }
        ), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400


@favorites_api_bp.route("/sheets/<int:sheet_id>", methods=["DELETE"])
def delete_sheet(sheet_id: int) -> tuple[Response, int]:
    """Deactivate a favorite sheet.

    Query params:
    - hard: If true, permanently delete instead of deactivate

    Returns:
        JSON response confirming deletion.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import get_favorite_sheet_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    hard_delete = request.args.get("hard", "false").lower() == "true"

    db_path = get_tenant_db_path()
    sheet_repo = get_favorite_sheet_repository(db_path)

    sheet = sheet_repo.get_by_id(
        sheet_id,
        organization_id=current["organization_id"],
        user_id=current["id"],
    )

    if not sheet:
        return jsonify(
            {
                "success": False,
                "error": f"Sheet {sheet_id} not found",
                "message": f"Sheet {sheet_id} not found",
            }
        ), 404

    # Check ownership for private sheets
    if sheet.is_private and sheet.created_by_user_id != current["id"]:
        return jsonify(
            {
                "success": False,
                "error": "Cannot delete another user's private sheet",
                "message": "Cannot delete another user's private sheet",
            }
        ), 403

    if hard_delete:
        sheet_repo.delete(sheet_id, organization_id=current["organization_id"])
        message = f"Sheet '{sheet.name}' permanently deleted"
    else:
        sheet_repo.deactivate(sheet_id, organization_id=current["organization_id"])
        message = f"Sheet '{sheet.name}' deactivated"

    return jsonify(
        {
            "success": True,
            "message": message,
        }
    ), 200


@favorites_api_bp.route("/sheets/<int:sheet_id>/verify", methods=["POST"])
def verify_sheet(sheet_id: int) -> tuple[Response, int]:
    """Verify access to a favorite sheet.

    Tests that the service account can access the Google Sheet
    and updates the last_verified_at timestamp.

    Returns:
        JSON response with verification result.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.favorites import get_favorite_sheet_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    sheet_repo = get_favorite_sheet_repository(db_path)

    sheet = sheet_repo.get_by_id(
        sheet_id,
        organization_id=current["organization_id"],
        user_id=current["id"],
    )

    if not sheet:
        return jsonify(
            {
                "success": False,
                "error": f"Sheet {sheet_id} not found",
                "message": f"Sheet {sheet_id} not found",
            }
        ), 404

    try:
        import gspread

        from mysql_to_sheets.core.config import get_config
        from mysql_to_sheets.core.sheets_utils import parse_worksheet_identifier

        config = get_config()
        gc = gspread.service_account(filename=config.service_account_file)  # type: ignore[attr-defined]

        # Try to open the sheet
        spreadsheet = gc.open_by_key(sheet.sheet_id)

        # Resolve worksheet name from GID URL if needed
        worksheet_name = parse_worksheet_identifier(
            sheet.default_worksheet,
            spreadsheet=spreadsheet,
        )

        # Try to access the worksheet
        worksheet = spreadsheet.worksheet(worksheet_name)

        # Update verified timestamp
        sheet_repo.update_verified(sheet_id, organization_id=current["organization_id"])

        return jsonify(
            {
                "success": True,
                "message": f"Access verified for '{sheet.name}'",
                "spreadsheet_title": spreadsheet.title,
                "worksheet_name": worksheet.title,
                "row_count": worksheet.row_count,
                "col_count": worksheet.col_count,
            }
        ), 200

    except Exception as e:
        error_message = str(e)

        # Provide helpful error messages
        if "not found" in error_message.lower():
            error_message = "Spreadsheet not found or not shared with service account"
        elif "permission" in error_message.lower():
            error_message = "Permission denied - sheet may not be shared with service account"
        elif "worksheet" in error_message.lower():
            error_message = f"Worksheet '{sheet.default_worksheet}' not found"

        return jsonify(
            {
                "success": False,
                "error": error_message,
                "message": error_message,
            }
        ), 400
