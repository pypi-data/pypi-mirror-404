"""API key management blueprint for Flask web dashboard.

Provides UI for creating, listing, and revoking API keys.
"""

import logging
import os
from typing import Any, cast

from flask import Blueprint, Response, jsonify, redirect, render_template, request, session, url_for

from mysql_to_sheets import __version__
from mysql_to_sheets.core.security import generate_api_key, generate_api_key_salt, hash_api_key
from mysql_to_sheets.models.api_keys import APIKeyRepository
from mysql_to_sheets.web.context import get_current_user
from mysql_to_sheets.web.decorators import login_required

logger = logging.getLogger("mysql_to_sheets.web.api_keys")

api_keys_bp = Blueprint("api_keys", __name__)


def _get_api_keys_db_path() -> str:
    """Get the path to the API keys database.

    Returns:
        Database path string.
    """
    return os.getenv("API_KEYS_DB_PATH", "./data/api_keys.db")


@api_keys_bp.route("/api-keys")
@login_required
def api_keys_page() -> str | Response | tuple[str, int]:
    """Render the API keys management page.

    Returns:
        Rendered HTML template.
    """
    current = get_current_user()
    if not current:
        return cast(Response, redirect(url_for("auth.login")))

    # Check permission (admin+ only)
    if current["role"] not in ("owner", "admin"):
        return render_template(
            "error.html",
            version=__version__,
            error="Access Denied",
            message="You do not have permission to access this page.",
        ), 403

    db_path = _get_api_keys_db_path()
    repo = APIKeyRepository(db_path)

    # Get all API keys (not revoked)
    api_keys = repo.get_all(include_revoked=False)

    return render_template(
        "api_keys.html",
        version=__version__,
        api_keys=[key.to_dict() for key in api_keys],
    )


# API endpoints for API key management
api_keys_api_bp = Blueprint("api_keys_api", __name__, url_prefix="/api/api-keys")


@api_keys_api_bp.route("", methods=["GET"])
def list_api_keys() -> Response | tuple[Response, int]:
    """List all API keys.

    Returns:
        JSON response with list of API keys.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Check permission (admin+ only)
    if current["role"] not in ("owner", "admin"):
        return jsonify({"success": False, "error": "Permission denied"}), 403

    db_path = _get_api_keys_db_path()
    repo = APIKeyRepository(db_path)

    include_revoked = request.args.get("include_revoked", "false").lower() == "true"
    api_keys = repo.get_all(include_revoked=include_revoked)

    return jsonify(
        {
            "success": True,
            "api_keys": [key.to_dict() for key in api_keys],
        }
    ), 200


@api_keys_api_bp.route("", methods=["POST"])
def create_api_key() -> Response | tuple[Response, int]:
    """Create a new API key.

    Returns:
        JSON response with the new API key (shown only once).
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Check permission (admin+ only)
    if current["role"] not in ("owner", "admin"):
        return jsonify({"success": False, "error": "Permission denied"}), 403

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    description = data.get("description", "").strip() or None
    scopes = data.get("scopes", ["*"])

    if not name:
        return jsonify({"success": False, "error": "Name is required"}), 400

    if len(name) > 100:
        return jsonify({"success": False, "error": "Name must be 100 characters or less"}), 400

    # Validate scopes
    valid_scopes = {"*", "read", "sync", "config", "admin"}
    if not isinstance(scopes, list) or not all(s in valid_scopes for s in scopes):
        return jsonify({
            "success": False,
            "error": f"Invalid scopes. Valid values: {sorted(valid_scopes)}",
        }), 400

    db_path = _get_api_keys_db_path()
    repo = APIKeyRepository(db_path)

    # Generate the API key with per-key salt
    raw_key = generate_api_key()
    key_salt = generate_api_key_salt()
    key_hash = hash_api_key(raw_key, key_salt)
    key_prefix = raw_key[:10] + "..."  # Show first 10 chars for identification

    try:
        api_key = repo.create(
            name=name,
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=key_prefix,
            description=description,
            scopes=scopes,
        )

        logger.info(f"API key created: {api_key.id} by user {current['id']}")

        return jsonify(
            {
                "success": True,
                "message": "API key created successfully",
                "api_key": api_key.to_dict(),
                # Return the raw key ONLY on creation - it won't be retrievable later
                "raw_key": raw_key,
            }
        ), 201

    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        return jsonify({"success": False, "error": "Failed to create API key"}), 500


@api_keys_api_bp.route("/<int:key_id>", methods=["GET"])
def get_api_key(key_id: int) -> Response | tuple[Response, int]:
    """Get a specific API key by ID.

    Args:
        key_id: The API key ID.

    Returns:
        JSON response with API key details.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Check permission (admin+ only)
    if current["role"] not in ("owner", "admin"):
        return jsonify({"success": False, "error": "Permission denied"}), 403

    db_path = _get_api_keys_db_path()
    repo = APIKeyRepository(db_path)

    api_key = repo.get_by_id(key_id)
    if not api_key:
        return jsonify({"success": False, "error": "API key not found"}), 404

    return jsonify(
        {
            "success": True,
            "api_key": api_key.to_dict(),
        }
    ), 200


@api_keys_api_bp.route("/<int:key_id>", methods=["DELETE"])
def revoke_api_key(key_id: int) -> Response | tuple[Response, int]:
    """Revoke an API key.

    Args:
        key_id: The API key ID to revoke.

    Returns:
        JSON response with revocation result.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Check permission (admin+ only)
    if current["role"] not in ("owner", "admin"):
        return jsonify({"success": False, "error": "Permission denied"}), 403

    db_path = _get_api_keys_db_path()
    repo = APIKeyRepository(db_path)

    # Revoke (soft delete) the key
    revoked = repo.revoke(key_id)
    if not revoked:
        return jsonify({"success": False, "error": "API key not found"}), 404

    logger.info(f"API key revoked: {key_id} by user {current['id']}")

    return jsonify(
        {
            "success": True,
            "message": "API key revoked successfully",
        }
    ), 200


@api_keys_api_bp.route("/<int:key_id>/delete", methods=["DELETE"])
def delete_api_key(key_id: int) -> Response | tuple[Response, int]:
    """Permanently delete an API key.

    Args:
        key_id: The API key ID to delete.

    Returns:
        JSON response with deletion result.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Check permission (owner only for permanent deletion)
    if current["role"] != "owner":
        return jsonify(
            {"success": False, "error": "Only owners can permanently delete API keys"}
        ), 403

    db_path = _get_api_keys_db_path()
    repo = APIKeyRepository(db_path)

    # Permanently delete the key
    deleted = repo.delete(key_id)
    if not deleted:
        return jsonify({"success": False, "error": "API key not found"}), 404

    logger.info(f"API key permanently deleted: {key_id} by user {current['id']}")

    return jsonify(
        {
            "success": True,
            "message": "API key deleted permanently",
        }
    ), 200


@api_keys_api_bp.route("/<int:key_id>/usage", methods=["GET"])
def get_api_key_usage(key_id: int) -> Response | tuple[Response, int]:
    """Get usage statistics for an API key.

    Args:
        key_id: The API key ID.

    Returns:
        JSON response with usage statistics.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Check permission (admin+ only)
    if current["role"] not in ("owner", "admin"):
        return jsonify({"success": False, "error": "Permission denied"}), 403

    # Verify the key exists
    db_path = _get_api_keys_db_path()
    repo = APIKeyRepository(db_path)

    api_key = repo.get_by_id(key_id)
    if not api_key:
        return jsonify({"success": False, "error": "API key not found"}), 404

    # Get usage stats
    try:
        from mysql_to_sheets.models.api_key_usage import get_api_key_usage_repository

        days = request.args.get("days", 30, type=int)
        days = min(max(days, 1), 365)  # Clamp to 1-365 days

        usage_repo = get_api_key_usage_repository(db_path)
        stats = usage_repo.get_usage_stats(key_id, days=days)

        return jsonify(
            {
                "success": True,
                "api_key": api_key.to_dict(),
                "usage": stats,
            }
        ), 200

    except Exception as e:
        logger.error(f"Failed to get API key usage: {e}")
        return jsonify({"success": False, "error": "Failed to get usage statistics"}), 500


@api_keys_api_bp.route("/usage", methods=["GET"])
def get_all_api_key_usage() -> Response | tuple[Response, int]:
    """Get usage statistics for all API keys.

    Returns:
        JSON response with usage statistics for all keys.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Check permission (admin+ only)
    if current["role"] not in ("owner", "admin"):
        return jsonify({"success": False, "error": "Permission denied"}), 403

    try:
        from mysql_to_sheets.models.api_key_usage import get_api_key_usage_repository

        days = request.args.get("days", 30, type=int)
        days = min(max(days, 1), 365)  # Clamp to 1-365 days

        db_path = _get_api_keys_db_path()
        usage_repo = get_api_key_usage_repository(db_path)
        all_stats = usage_repo.get_all_usage_stats(days=days)

        return jsonify(
            {
                "success": True,
                "period_days": days,
                "usage": all_stats,
            }
        ), 200

    except Exception as e:
        logger.error(f"Failed to get all API key usage: {e}")
        return jsonify({"success": False, "error": "Failed to get usage statistics"}), 500
