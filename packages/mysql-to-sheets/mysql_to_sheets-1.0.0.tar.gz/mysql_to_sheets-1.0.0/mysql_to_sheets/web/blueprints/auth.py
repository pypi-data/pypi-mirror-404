"""Authentication blueprint for Flask web dashboard.

Handles login, logout, and registration routes.
"""

import logging
import os
import re
from typing import cast

from flask import Blueprint, Response, flash, redirect, render_template, request, session, url_for

from mysql_to_sheets import __version__
from mysql_to_sheets.core.security import RateLimiter
from mysql_to_sheets.core.tenant import get_tenant_db_path

logger = logging.getLogger("mysql_to_sheets.web.auth")

# Rate limiter for authentication endpoints (10 requests/minute, burst of 5)
_auth_limiter = RateLimiter(requests_per_minute=10, burst_size=5)


def _log_auth_audit(
    event: str,
    organization_id: int | None,
    db_path: str,
    user_id: int | None = None,
    email: str | None = None,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Log an authentication audit event.

    Args:
        event: Auth event type (login, logout, login_failed).
        organization_id: Organization ID (may be None for failed logins).
        db_path: Path to tenant database.
        user_id: User ID if known.
        email: User email (for failed logins).
        success: Whether the action succeeded.
        error: Error message if failed.
    """
    try:
        from mysql_to_sheets.core.audit import log_auth_event

        # Use a default org ID for failed logins where org is unknown
        org_id = organization_id or 0

        log_auth_event(
            event=event,
            organization_id=org_id,
            db_path=db_path,
            user_id=user_id,
            email=email,
            success=success,
            error=error,
        )
    except Exception as e:
        logger.debug(f"Audit logging skipped or failed: {e}")


auth_bp = Blueprint("auth", __name__)


@auth_bp.before_app_request
def check_force_password_change() -> Response | None:
    """Redirect users who must change their password.

    This before_request hook ensures that users with force_password_change=True
    cannot access any page except the change password page and logout.
    """
    # Skip for unauthenticated requests
    if not session.get("user_id"):
        return None

    # Skip for change password and logout routes
    if request.endpoint in ("auth.change_password", "auth.logout", "static"):
        return None

    # Skip for API routes (they handle auth differently)
    if request.path.startswith("/api/"):
        return None

    # Redirect if password change required
    if session.get("force_password_change"):
        return cast(Response, redirect(url_for("auth.change_password")))
    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> str | Response | tuple[str, int]:
    """Handle login page and form submission.

    Returns:
        Rendered login page or redirect to dashboard.
    """
    if request.method == "GET":
        # Already logged in?
        if session.get("user_id"):
            return cast(Response, redirect(url_for("dashboard.index")))

        return render_template(
            "login.html",
            version=__version__,
            email=request.args.get("email", ""),
            message=request.args.get("message"),
        )

    # POST - handle login form
    # Rate limit login attempts
    client_ip = request.remote_addr or "unknown"
    if not _auth_limiter.is_allowed(f"login:{client_ip}"):
        logger.warning(f"Rate limit exceeded for login from {client_ip}")
        return render_template(
            "login.html",
            version=__version__,
            email=request.form.get("email", ""),
            error="Too many login attempts. Please wait a moment and try again.",
        ), 429
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    remember = request.form.get("remember") == "on"

    if not email or not password:
        return render_template(
            "login.html",
            version=__version__,
            email=email,
            error="Email and password are required",
        )

    try:
        from mysql_to_sheets.core.auth import verify_password
        from mysql_to_sheets.models.organizations import get_organization_repository
        from mysql_to_sheets.models.users import get_user_repository

        db_path = get_tenant_db_path()
        user_repo = get_user_repository(db_path)
        org_repo = get_organization_repository(db_path)

        # Find user by email (across all orgs for login)
        user = user_repo.get_by_email_global(email)

        if not user:
            _log_auth_audit(
                event="login_failed",
                organization_id=None,
                db_path=db_path,
                email=email,
                success=False,
                error="User not found",
            )
            return render_template(
                "login.html",
                version=__version__,
                email=email,
                error="Invalid email or password",
            )

        if not verify_password(password, user.password_hash):
            _log_auth_audit(
                event="login_failed",
                organization_id=user.organization_id,
                db_path=db_path,
                user_id=user.id,
                email=email,
                success=False,
                error="Invalid password",
            )
            return render_template(
                "login.html",
                version=__version__,
                email=email,
                error="Invalid email or password",
            )

        if not user.is_active:
            return render_template(
                "login.html",
                version=__version__,
                email=email,
                error="Your account has been deactivated",
            )

        # Get organization
        org = org_repo.get_by_id(user.organization_id)
        if not org or not org.is_active:
            return render_template(
                "login.html",
                version=__version__,
                email=email,
                error="Organization is inactive",
            )

        # Update last login - user.id should be set at this point
        assert user.id is not None, "User ID should be set"
        user_repo.update_last_login(user.id)

        # Log successful login
        _log_auth_audit(
            event="login",
            organization_id=user.organization_id,
            db_path=db_path,
            user_id=user.id,
            email=email,
            success=True,
        )

        # Set session
        session.permanent = remember
        session["user_id"] = user.id
        session["email"] = user.email
        session["display_name"] = user.display_name
        session["role"] = user.role
        session["organization_id"] = user.organization_id
        session["organization_name"] = org.name
        session["force_password_change"] = user.force_password_change

        # Debug: Log session state after login for Super Admin visibility debugging
        logger.info(
            f"Login session set: user_id={user.id}, email={user.email}, "
            f"session_role={session.get('role')!r}, db_role={user.role!r}"
        )

        # Check if user must change password
        if user.force_password_change:
            return cast(Response, redirect(url_for("auth.change_password")))

        # Redirect to next or dashboard
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return cast(Response, redirect(next_url))
        return cast(Response, redirect(url_for("dashboard.index")))

    except Exception as e:
        logger.error(f"Login error: {e}")
        return render_template(
            "login.html",
            version=__version__,
            email=email,
            error="An error occurred. Please try again.",
        )


@auth_bp.route("/register", methods=["GET", "POST"])
def register() -> str | Response | tuple[str, int]:
    """Handle registration page and form submission.

    Returns:
        Rendered registration page or redirect to login.
    """
    if request.method == "GET":
        # Already logged in?
        if session.get("user_id"):
            return cast(Response, redirect(url_for("dashboard.index")))

        return render_template(
            "register.html",
            version=__version__,
        )

    # POST - handle registration form
    # Rate limit registration attempts
    client_ip = request.remote_addr or "unknown"
    if not _auth_limiter.is_allowed(f"register:{client_ip}"):
        logger.warning(f"Rate limit exceeded for registration from {client_ip}")
        return render_template(
            "register.html",
            version=__version__,
            error="Too many registration attempts. Please wait a moment and try again.",
        ), 429

    org_name = request.form.get("org_name", "").strip()
    display_name = request.form.get("display_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Basic validation
    errors = []
    if not org_name:
        errors.append("Organization name is required")
    if not display_name:
        errors.append("Your name is required")
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")
    if password != confirm_password:
        errors.append("Passwords do not match")

    if errors:
        return render_template(
            "register.html",
            version=__version__,
            org_name=org_name,
            display_name=display_name,
            email=email,
            error="Please fix the following errors:",
            errors=errors,
        )

    try:
        from mysql_to_sheets.core.auth import hash_password, validate_password_strength
        from mysql_to_sheets.models.organizations import Organization, get_organization_repository
        from mysql_to_sheets.models.users import User, get_user_repository

        db_path = get_tenant_db_path()

        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

        # Validate password strength
        is_valid, pwd_errors = validate_password_strength(password)
        if not is_valid:
            return render_template(
                "register.html",
                version=__version__,
                org_name=org_name,
                display_name=display_name,
                email=email,
                error="Password does not meet requirements:",
                errors=pwd_errors,
            )

        org_repo = get_organization_repository(db_path)
        user_repo = get_user_repository(db_path)

        # Generate slug from org name
        slug = re.sub(r"[^a-z0-9]+", "-", org_name.lower()).strip("-")

        # Check if org slug exists
        existing_org = org_repo.get_by_slug(slug)
        if existing_org:
            return render_template(
                "register.html",
                version=__version__,
                org_name=org_name,
                display_name=display_name,
                email=email,
                error="An organization with this name already exists",
            )

        # Check if email already exists
        existing_user = user_repo.get_by_email_global(email)
        if existing_user:
            return render_template(
                "register.html",
                version=__version__,
                org_name=org_name,
                display_name=display_name,
                email=email,
                error="An account with this email already exists",
            )

        # Create organization
        org = Organization(
            name=org_name,
            slug=slug,
        )
        org = org_repo.create(org)

        # org.id should be set after create
        assert org.id is not None, "Organization ID should be set after creation"

        # Start trial for new organization
        try:
            from mysql_to_sheets.core.trial import start_trial

            start_trial(organization_id=org.id, db_path=db_path)
            logger.info(f"Started trial for new org {org.id}")
        except Exception as e:
            logger.warning(f"Failed to start trial for org {org.id}: {e}")

        # Create owner user
        user = User(
            email=email,
            display_name=display_name,
            organization_id=org.id,
            role="owner",
            password_hash=hash_password(password),
        )
        user = user_repo.create(user)

        # Redirect to login with success message
        return cast(Response, redirect(
            url_for("auth.login", message="Account created! Please sign in.", email=email)
        ))

    except ValueError as e:
        return render_template(
            "register.html",
            version=__version__,
            org_name=org_name,
            display_name=display_name,
            email=email,
            error=str(e),
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return render_template(
            "register.html",
            version=__version__,
            org_name=org_name,
            display_name=display_name,
            email=email,
            error="An error occurred. Please try again.",
        )


@auth_bp.route("/change-password", methods=["GET", "POST"])
def change_password() -> str | Response | tuple[str, int]:
    """Handle password change page and form submission.

    This page is shown when a user must change their password (e.g., first login
    for bootstrap users). Users are redirected here from login if their
    force_password_change flag is set.

    Returns:
        Rendered change password page or redirect to dashboard.
    """
    # Must be logged in
    if not session.get("user_id"):
        return cast(Response, redirect(url_for("auth.login")))

    is_forced = session.get("force_password_change", False)

    if request.method == "GET":
        return render_template(
            "change_password.html",
            version=__version__,
            is_forced=is_forced,
        )

    # POST - handle password change form
    client_ip = request.remote_addr or "unknown"
    if not _auth_limiter.is_allowed(f"change_password:{client_ip}"):
        logger.warning(f"Rate limit exceeded for password change from {client_ip}")
        return render_template(
            "change_password.html",
            version=__version__,
            is_forced=is_forced,
            error="Too many attempts. Please try again later.",
        ), 429

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Skip current password check for forced changes (bootstrap user)
    if not is_forced and not current_password:
        return render_template(
            "change_password.html",
            version=__version__,
            is_forced=is_forced,
            error="Current password is required",
        )

    if not new_password:
        return render_template(
            "change_password.html",
            version=__version__,
            is_forced=is_forced,
            error="New password is required",
        )

    if new_password != confirm_password:
        return render_template(
            "change_password.html",
            version=__version__,
            is_forced=is_forced,
            error="New passwords do not match",
        )

    try:
        from mysql_to_sheets.core.auth import (
            hash_password,
            validate_password_strength,
            verify_password,
        )
        from mysql_to_sheets.models.users import get_user_repository

        db_path = get_tenant_db_path()
        user_repo = get_user_repository(db_path)

        user_id = session["user_id"]
        user = user_repo.get_by_id(user_id)

        if not user:
            session.clear()
            return cast(Response, redirect(url_for("auth.login", message="Session expired")))

        # Verify current password (skip for forced changes)
        if not is_forced:
            if not verify_password(current_password, user.password_hash):
                return render_template(
                    "change_password.html",
                    version=__version__,
                    is_forced=is_forced,
                    error="Current password is incorrect",
                )

        # Validate new password strength
        is_valid, pwd_errors = validate_password_strength(new_password)
        if not is_valid:
            return render_template(
                "change_password.html",
                version=__version__,
                is_forced=is_forced,
                error="Password does not meet requirements:",
                errors=pwd_errors,
            )

        # Update password and clear force flag
        user_repo.update_password(user_id, hash_password(new_password), clear_force_change=True)

        # Update session
        session["force_password_change"] = False

        # Log the password change
        _log_auth_audit(
            event="password_changed",
            organization_id=session.get("organization_id"),
            db_path=db_path,
            user_id=user_id,
            success=True,
        )

        # Clear first run banner if this was from bootstrap
        if session.get("_first_run"):
            session.pop("_first_run", None)

        logger.info(f"Password changed for user {user_id}")

        # Redirect to dashboard with success message
        flash("Password changed successfully!", "success")
        return cast(Response, redirect(url_for("dashboard.index")))

    except Exception as e:
        logger.error(f"Password change error: {e}")
        return render_template(
            "change_password.html",
            version=__version__,
            is_forced=is_forced,
            error="An error occurred. Please try again.",
        )


@auth_bp.route("/logout")
def logout() -> Response:
    """Handle logout.

    Returns:
        Redirect to login page.
    """
    # Log logout before clearing session
    user_id = session.get("user_id")
    organization_id = session.get("organization_id")

    if user_id and organization_id:
        try:
            db_path = get_tenant_db_path()
            _log_auth_audit(
                event="logout",
                organization_id=organization_id,
                db_path=db_path,
                user_id=user_id,
                success=True,
            )
        except Exception as e:
            logger.debug(f"Logout audit logging failed: {e}")

    session.clear()
    return cast(Response, redirect(url_for("auth.login", message="You have been logged out")))
