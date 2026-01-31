"""Users API blueprint for web dashboard.

Handles user CRUD operations via AJAX (multi-tenant).
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request

from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.web.blueprints.api.auth_helpers import (
    _get_user_or_401,
    _require_admin,
    _require_login,
)
from mysql_to_sheets.web.context import get_current_user

logger = logging.getLogger("mysql_to_sheets.web.api.users")

users_api_bp = Blueprint("users_api", __name__, url_prefix="/api/users")


@users_api_bp.route("", methods=["GET"])
def list_users() -> tuple[Response, int]:
    """List users in current organization.

    Query params:
    - include_inactive: If true, include inactive users

    Returns:
        JSON response with user list.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.users import get_user_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    include_inactive = request.args.get("include_inactive", "false").lower() == "true"

    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    users = user_repo.get_all(
        organization_id=current["organization_id"],
        include_inactive=include_inactive,
    )

    return jsonify(
        {
            "success": True,
            "users": [u.to_dict() for u in users],
            "total": len(users),
        }
    ), 200


@users_api_bp.route("", methods=["POST"])
def create_user() -> tuple[Response, int]:
    """Create a new user in current organization.

    Expects JSON body with:
    - email: User email (required)
    - display_name: Display name (required)
    - role: User role (optional, default: viewer)
    - password: Initial password (required)

    Returns:
        JSON response with created user.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.core.auth import hash_password, validate_password_strength
    from mysql_to_sheets.core.rbac import can_manage_role
    from mysql_to_sheets.models.users import User, get_user_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    # Validation
    if not data.get("email"):
        return jsonify(
            {"success": False, "error": "Email is required", "message": "Email is required"}
        ), 400
    if not data.get("display_name"):
        return jsonify(
            {
                "success": False,
                "error": "Display name is required",
                "message": "Display name is required",
            }
        ), 400
    if not data.get("password"):
        return jsonify(
            {"success": False, "error": "Password is required", "message": "Password is required"}
        ), 400

    role = data.get("role", "viewer")
    if not can_manage_role(current["role"], role):
        return jsonify(
            {
                "success": False,
                "error": f"You cannot assign the {role} role",
                "message": f"You cannot assign the {role} role",
            }
        ), 403

    # Validate password
    is_valid, errors = validate_password_strength(data["password"])
    if not is_valid:
        return jsonify(
            {
                "success": False,
                "error": "Password does not meet requirements",
                "message": "Password does not meet requirements",
                "errors": errors,
            }
        ), 400

    try:
        db_path = get_tenant_db_path()
        user_repo = get_user_repository(db_path)

        user = User(
            email=data["email"].strip().lower(),
            display_name=data["display_name"].strip(),
            organization_id=current["organization_id"],
            role=role,
            password_hash=hash_password(data["password"]),
        )

        user = user_repo.create(user)

        return jsonify(
            {
                "success": True,
                "user": user.to_dict(),
            }
        ), 201

    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400
    except Exception as e:
        logger.exception(f"Error creating user: {e}")
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 500


@users_api_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id: int) -> tuple[Response, int]:
    """Get a user by ID.

    Returns:
        JSON response with user details.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.users import get_user_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    user = user_repo.get_by_id(user_id, organization_id=current["organization_id"])

    if not user:
        return jsonify(
            {
                "success": False,
                "error": f"User {user_id} not found",
                "message": f"User {user_id} not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "user": user.to_dict(),
        }
    ), 200


@users_api_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id: int) -> tuple[Response, int]:
    """Update a user.

    Returns:
        JSON response with updated user.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.core.rbac import can_manage_role
    from mysql_to_sheets.models.users import get_user_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    user = user_repo.get_by_id(user_id, organization_id=current["organization_id"])

    if not user:
        return jsonify(
            {
                "success": False,
                "error": f"User {user_id} not found",
                "message": f"User {user_id} not found",
            }
        ), 404

    # Check if trying to change role
    if "role" in data and data["role"] != user.role:
        if not can_manage_role(current["role"], data["role"]):
            return jsonify(
                {
                    "success": False,
                    "error": f"You cannot assign the {data['role']} role",
                    "message": f"You cannot assign the {data['role']} role",
                }
            ), 403

    # Apply updates
    if "display_name" in data:
        user.display_name = data["display_name"].strip()
    if "email" in data:
        user.email = data["email"].strip().lower()
    if "role" in data:
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = data["is_active"]

    try:
        user = user_repo.update(user)
        return jsonify(
            {
                "success": True,
                "user": user.to_dict(),
            }
        ), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400


@users_api_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int) -> tuple[Response, int]:
    """Deactivate a user.

    Query params:
    - hard: If true, permanently delete instead of deactivate

    Returns:
        JSON response confirming deletion.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.users import get_user_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    hard_delete = request.args.get("hard", "false").lower() == "true"

    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    user = user_repo.get_by_id(user_id, organization_id=current["organization_id"])

    if not user:
        return jsonify(
            {
                "success": False,
                "error": f"User {user_id} not found",
                "message": f"User {user_id} not found",
            }
        ), 404

    # Cannot delete owner
    if user.role == "owner":
        return jsonify(
            {
                "success": False,
                "error": "Cannot delete organization owner",
                "message": "Cannot delete organization owner",
            }
        ), 400

    # Cannot delete yourself
    if user.id == current["id"]:
        return jsonify(
            {
                "success": False,
                "error": "Cannot delete your own account",
                "message": "Cannot delete your own account",
            }
        ), 400

    if hard_delete:
        user_repo.delete(user_id, organization_id=current["organization_id"])
        message = f"User {user.email} permanently deleted"
    else:
        user_repo.deactivate(user_id, organization_id=current["organization_id"])
        message = f"User {user.email} deactivated"

    return jsonify(
        {
            "success": True,
            "message": message,
        }
    ), 200


@users_api_bp.route("/<int:user_id>/reset-password", methods=["POST"])
def reset_user_password(user_id: int) -> tuple[Response, int]:
    """Reset a user's password.

    Expects JSON body with:
    - password: New password (required)

    Returns:
        JSON response confirming reset.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.core.auth import hash_password, validate_password_strength
    from mysql_to_sheets.models.users import get_user_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    if not data.get("password"):
        return jsonify(
            {"success": False, "error": "Password is required", "message": "Password is required"}
        ), 400

    # Validate password
    is_valid, errors = validate_password_strength(data["password"])
    if not is_valid:
        return jsonify(
            {
                "success": False,
                "error": "Password does not meet requirements",
                "message": "Password does not meet requirements",
                "errors": errors,
            }
        ), 400

    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    user = user_repo.get_by_id(user_id, organization_id=current["organization_id"])

    if not user:
        return jsonify(
            {
                "success": False,
                "error": f"User {user_id} not found",
                "message": f"User {user_id} not found",
            }
        ), 404

    user_repo.update_password(user_id, hash_password(data["password"]))

    return jsonify(
        {
            "success": True,
            "message": f"Password reset for {user.email}",
        }
    ), 200
