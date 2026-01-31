"""Super Admin blueprint for Flask web dashboard.

Provides cross-tenant administrative views for system-level management.
This blueprint is opt-in via SUPER_ADMIN_ENABLED environment variable
and restricted to users with the 'owner' role.

Security:
- Disabled by default (returns 404 when SUPER_ADMIN_ENABLED is not set)
- Requires 'owner' role (highest privilege level)
- View-only access (no cross-org modifications)
- All access is logged to audit trail
"""

import logging
import os
from functools import wraps
from typing import Any, Callable, cast

from flask import (
    Blueprint,
    Response,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from mysql_to_sheets import __version__
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.organizations import get_organization_repository
from mysql_to_sheets.models.users import VALID_ROLES, get_user_repository
from mysql_to_sheets.web.context import get_current_user
from mysql_to_sheets.web.decorators import login_required

logger = logging.getLogger("mysql_to_sheets.web.super_admin")


def is_super_admin_enabled() -> bool:
    """Check if super admin feature is enabled.

    Returns:
        True if SUPER_ADMIN_ENABLED environment variable is set to 'true'.
    """
    return os.getenv("SUPER_ADMIN_ENABLED", "").lower() == "true"


def require_super_admin(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require super admin access.

    Checks that:
    1. SUPER_ADMIN_ENABLED is set to 'true'
    2. User is authenticated
    3. User has 'owner' role

    Returns 404 if disabled (to hide existence of the feature).
    Returns 403 if user lacks permission.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Check if feature is enabled
        if not is_super_admin_enabled():
            abort(404)

        # Check authentication
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.url))

        # Check role
        current = get_current_user()
        if not current:
            return redirect(url_for("auth.login"))

        if current.get("role") != "owner":
            logger.warning(
                f"Super admin access denied for user {current.get('email')} "
                f"(role: {current.get('role')})"
            )
            abort(403)

        # Log access for audit
        logger.info(
            f"Super admin access: user={current.get('email')} "
            f"org={current.get('organization_id')} "
            f"path={request.path}"
        )

        return f(*args, **kwargs)

    return decorated_function


# Create blueprints
super_admin_bp = Blueprint("super_admin", __name__, url_prefix="/super-admin")


@super_admin_bp.route("/users")
@login_required
@require_super_admin
def users_list() -> str | Response:
    """Render the super admin users list page.

    Shows all users across all organizations with filtering and pagination.

    Query parameters:
        page: Page number (default 1)
        per_page: Items per page (25, 50, or 100, default 25)
        search: Search term for email/name
        org: Organization ID filter
        role: Role filter
        status: Status filter ('active' or 'inactive')

    Returns:
        Rendered HTML template.
    """
    current = get_current_user()
    if not current:
        return cast(Response, redirect(url_for("auth.login")))

    db_path = get_tenant_db_path()

    # Parse query parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("search", "").strip() or None
    org_filter = request.args.get("org", type=int)
    role_filter = request.args.get("role", "").strip() or None
    status_filter = request.args.get("status", "").strip()

    # Validate per_page
    if per_page not in (25, 50, 100):
        per_page = 25

    # Validate role filter
    if role_filter and role_filter not in VALID_ROLES:
        role_filter = None

    # Determine include_inactive based on status filter
    include_inactive = status_filter == "inactive" or status_filter == "all"

    # Calculate offset
    offset = (page - 1) * per_page

    # Fetch users
    user_repo = get_user_repository(db_path)
    users, total_count = user_repo.get_all_users_global(
        include_inactive=include_inactive if status_filter == "all" else (status_filter == "inactive"),
        limit=per_page,
        offset=offset,
        search=search,
        organization_id=org_filter,
        role=role_filter,
    )

    # If filtering by active only (default), we need to re-query
    if status_filter == "active" or not status_filter:
        users, total_count = user_repo.get_all_users_global(
            include_inactive=False,
            limit=per_page,
            offset=offset,
            search=search,
            organization_id=org_filter,
            role=role_filter,
        )

    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages

    # Fetch organizations for filter dropdown
    org_repo = get_organization_repository(db_path)
    organizations = org_repo.get_all(include_inactive=True)

    return render_template(
        "super_admin/users.html",
        version=__version__,
        users=users,
        total_count=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        search=search or "",
        org_filter=org_filter,
        role_filter=role_filter or "",
        status_filter=status_filter or "active",
        organizations=organizations,
        valid_roles=VALID_ROLES,
    )


# API endpoints for super admin
super_admin_api_bp = Blueprint("super_admin_api", __name__, url_prefix="/api/super-admin")


@super_admin_api_bp.route("/users", methods=["GET"])
def api_users_list() -> Response | tuple[Response, int]:
    """Get all users across all organizations via API.

    Query parameters:
        limit: Maximum results (default 50, max 100)
        offset: Results to skip (default 0)
        search: Search term for email/name
        org_id: Organization ID filter
        role: Role filter
        include_inactive: Include inactive users (default false)

    Returns:
        JSON response with users list and pagination info.
    """
    # Check if feature is enabled
    if not is_super_admin_enabled():
        return jsonify({"success": False, "error": "Not found"}), 404

    # Check authentication
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    # Check role
    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    if current.get("role") != "owner":
        return jsonify({"success": False, "error": "Forbidden"}), 403

    db_path = get_tenant_db_path()

    # Parse parameters
    limit = min(request.args.get("limit", 50, type=int), 100)
    offset = request.args.get("offset", 0, type=int)
    search = request.args.get("search", "").strip() or None
    org_id = request.args.get("org_id", type=int)
    role = request.args.get("role", "").strip() or None
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"

    # Validate role
    if role and role not in VALID_ROLES:
        role = None

    # Fetch users
    user_repo = get_user_repository(db_path)
    users, total_count = user_repo.get_all_users_global(
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
        search=search,
        organization_id=org_id,
        role=role,
    )

    return jsonify(
        {
            "success": True,
            "users": users,
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }
    ), 200


@super_admin_api_bp.route("/stats", methods=["GET"])
def api_stats() -> Response | tuple[Response, int]:
    """Get super admin statistics.

    Returns:
        JSON response with system-wide statistics.
    """
    # Check if feature is enabled
    if not is_super_admin_enabled():
        return jsonify({"success": False, "error": "Not found"}), 404

    # Check authentication
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    # Check role
    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    if current.get("role") != "owner":
        return jsonify({"success": False, "error": "Forbidden"}), 403

    db_path = get_tenant_db_path()

    # Get counts
    org_repo = get_organization_repository(db_path)
    user_repo = get_user_repository(db_path)

    total_orgs = org_repo.count(include_inactive=False)
    total_orgs_all = org_repo.count(include_inactive=True)

    # Count all users (we need to query without org filter)
    all_users, total_users = user_repo.get_all_users_global(
        include_inactive=False, limit=1, offset=0
    )
    all_users_inactive, total_users_all = user_repo.get_all_users_global(
        include_inactive=True, limit=1, offset=0
    )

    return jsonify(
        {
            "success": True,
            "stats": {
                "organizations": {
                    "active": total_orgs,
                    "total": total_orgs_all,
                },
                "users": {
                    "active": total_users,
                    "total": total_users_all,
                },
            },
        }
    ), 200
