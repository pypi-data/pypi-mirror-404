"""Flask web dashboard for MySQL to Google Sheets sync.

This module provides a Flask application factory that creates and configures
the web dashboard. The routes are organized into blueprints for maintainability:

- auth: Login, logout, registration (/login, /register, /logout)
- dashboard: Main pages (/, /setup, /schedules, /users, /configs, /webhooks, /favorites)
- sync_api: Sync operations (/api/sync, /api/validate, /api/history)
- schedules_api: Schedule CRUD (/api/schedules/*)
- users_api: User management (/api/users/*)
- configs_api: Config management (/api/configs/*)
- webhooks_api: Webhook management (/api/webhooks/*)
- favorites_api: Favorites management (/api/favorites/queries/*, /api/favorites/sheets/*)
- jobs_api: Job queue operations (/api/jobs/*)
- freshness_api: Freshness monitoring (/api/freshness/*)
- tier: Tier status page (/tier)
- freshness: Freshness monitoring page (/freshness)
- api_keys: API key management (/api-keys)
- diagnostics: System diagnostics (/diagnostics)
"""

import atexit
import logging
import os
import secrets
import string
from datetime import timedelta
from typing import Any

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from mysql_to_sheets import __version__
from mysql_to_sheets.core.paths import (
    get_data_dir,
    get_static_dir,
    get_template_dir,
    is_bundled,
)
from mysql_to_sheets.web.context import inject_user

# Initialize CSRF protection
csrf = CSRFProtect()

# Default admin email (password is generated randomly on first run)
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@localhost")

# Store the generated password for display (only during first run session)
_generated_admin_password: str | None = None

logger = logging.getLogger("mysql_to_sheets.web")


def _generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password.

    Args:
        length: Password length (default: 16 characters).

    Returns:
        Random password with mixed case, digits, and special characters.
    """
    # Ensure password meets complexity requirements
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"

    # Generate password ensuring at least one of each type
    password = [
        secrets.choice(string.ascii_uppercase),  # Uppercase
        secrets.choice(string.ascii_lowercase),  # Lowercase
        secrets.choice(string.digits),  # Digit
        secrets.choice("!@#$%^&*"),  # Special char
    ]

    # Fill remaining with random characters
    password.extend(secrets.choice(alphabet) for _ in range(length - 4))

    # Shuffle to avoid predictable pattern
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)

    return "".join(password_list)


def _get_or_create_desktop_secret() -> str:
    """Get or create a persistent session secret for the desktop app.

    When running as a PyInstaller bundle, we need a session secret but can't
    require the user to set one manually. This function creates a secret file
    in the platform-specific data directory and reuses it across launches.

    Returns:
        A 64-character hex string suitable for use as SECRET_KEY.
    """
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    secret_file = data_dir / ".session_secret"

    if secret_file.exists():
        try:
            return secret_file.read_text().strip()
        except OSError:
            pass  # Fall through to generate new secret

    # Generate new secret
    secret_key = secrets.token_hex(32)  # 64 hex characters

    # Save for future sessions
    try:
        secret_file.write_text(secret_key)
        # Restrict permissions on Unix-like systems
        secret_file.chmod(0o600)
        logger.info(f"Generated desktop session secret at {secret_file}")
    except OSError as e:
        logger.warning(f"Could not persist session secret: {e}")

    return secret_key


def _bootstrap_admin_if_needed() -> bool:
    """Create default organization and admin user if no users exist.

    This provides a seamless first-run experience where the owner
    doesn't need to manually register.

    SECURITY: Generates a random password instead of using a hardcoded default.
    The password is displayed once in the first-run banner and should be
    changed immediately.

    Returns:
        True if bootstrap was performed (first run), False otherwise.
    """
    global _generated_admin_password

    from mysql_to_sheets.core.auth import hash_password
    from mysql_to_sheets.core.tenant import get_tenant_db_path
    from mysql_to_sheets.models.organizations import (
        Organization,
        get_organization_repository,
    )
    from mysql_to_sheets.models.users import User, get_user_repository

    db_path = get_tenant_db_path()

    try:
        org_repo = get_organization_repository(db_path)

        # Check if any organizations exist
        existing_orgs = org_repo.get_all(include_inactive=True)
        if existing_orgs:
            # Not first run
            return False

        # Create default organization
        org = Organization(
            name="Default",
            slug="default",
        )
        org = org_repo.create(org)
        logger.info(f"Bootstrap: Created default organization (id={org.id})")

        # Generate secure random password
        _generated_admin_password = _generate_secure_password()

        # Create admin user with random password and force password change
        user_repo = get_user_repository(db_path)
        if org.id is None:
            raise ValueError("Organization ID cannot be None after creation")
        admin_user = User(
            email=DEFAULT_ADMIN_EMAIL,
            display_name="Administrator",
            password_hash=hash_password(_generated_admin_password),
            role="owner",
            organization_id=org.id,
            force_password_change=True,  # Require password change on first login
        )
        admin_user = user_repo.create(admin_user)
        logger.info(f"Bootstrap: Created default admin user (id={admin_user.id})")

        # Start trial period for the new organization
        try:
            from mysql_to_sheets.core.trial import start_trial

            trial_info = start_trial(org.id, db_path=db_path)
            logger.info(
                f"Bootstrap: Started trial for org {org.id} "
                f"(expires {trial_info.trial_ends_at})"
            )
        except Exception as trial_err:
            logger.debug(f"Trial auto-start skipped: {trial_err}")

        # Log password securely (for server-side access)
        # In production, this should be handled differently (e.g., via setup wizard)
        logger.warning(
            "FIRST RUN: Admin account created. "
            "Check the web interface for credentials. "
            "CHANGE THE PASSWORD IMMEDIATELY!"
        )

        return True

    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")
        return False


def _setup_tier_callback() -> None:
    """Wire up tier enforcement so @require_tier decorators work.

    Registers a callback that resolves an organization's subscription tier
    from the database, enabling tier-gated features to enforce limits.
    """
    try:
        from mysql_to_sheets.core.tenant import get_tenant_db_path
        from mysql_to_sheets.core.tier import Tier, set_tier_callback

        def _get_org_tier(org_id: int) -> Tier:
            from mysql_to_sheets.models.organizations import get_organization_repository

            db_path = get_tenant_db_path()
            repo = get_organization_repository(db_path)
            org = repo.get_by_id(org_id)
            if org:
                return org.tier
            return Tier.FREE

        set_tier_callback(_get_org_tier)
        logger.info("Tier enforcement callback registered")
    except Exception as e:
        logger.warning(f"Tier enforcement setup skipped: {e}")


def _check_license_at_startup() -> None:
    """Validate license key and log warnings for invalid/expired licenses."""
    try:
        from mysql_to_sheets.core.config import get_config
        from mysql_to_sheets.core.license import LicenseStatus, validate_license

        config = get_config()
        license_key = getattr(config, "license_key", None) or os.getenv("LICENSE_KEY", "")
        if not license_key:
            logger.info("No LICENSE_KEY set — running in FREE tier")
            return

        info = validate_license(license_key)
        if info.status == LicenseStatus.VALID:
            logger.info(f"License valid: tier={info.tier.value}, expires={info.expires_at}")
        elif info.status == LicenseStatus.GRACE_PERIOD:
            logger.warning(
                f"License EXPIRED but in grace period (days left: {info.days_until_expiry}). "
                "Renew your subscription to avoid service interruption."
            )
        elif info.status == LicenseStatus.EXPIRED:
            logger.warning(
                "License EXPIRED — features will be restricted to FREE tier. "
                "Renew your subscription at the billing portal."
            )
        elif info.status == LicenseStatus.INVALID:
            logger.warning(f"License INVALID: {info.error}")
        else:
            logger.warning(f"License status: {info.status.value}")
    except Exception as e:
        logger.debug(f"License check skipped: {e}")


def create_app(config: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Optional configuration dictionary to override defaults.

    Returns:
        Configured Flask application instance.
    """
    # Ensure platform directories exist before any config access
    from mysql_to_sheets.core.paths import ensure_directories

    ensure_directories()

    # Get the templates and static directories (handles PyInstaller bundling)
    template_dir = get_template_dir()
    static_dir = get_static_dir()

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
    )

    # Security configuration
    secret_key = os.getenv("SESSION_SECRET_KEY")
    if not secret_key:
        # Priority order:
        # 1. Desktop app (bundled): auto-generate and persist
        # 2. Dev/test mode: use default key
        # 3. Production: require explicit configuration
        if is_bundled():
            # Desktop app: auto-generate and persist secret for seamless UX
            secret_key = _get_or_create_desktop_secret()
            logger.info("Using auto-generated session secret for desktop app")
        elif (
            os.getenv("FLASK_ENV") == "development"
            or os.getenv("FLASK_DEBUG") == "1"
            or os.getenv("TESTING") == "1"
            or os.getenv("PYTEST_CURRENT_TEST")  # pytest sets this
        ):
            secret_key = "dev-secret-change-in-production"
            logger.warning("Using default SECRET_KEY - set SESSION_SECRET_KEY for production")
        else:
            raise RuntimeError(
                "SESSION_SECRET_KEY environment variable is required in production. "
                'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
    app.config["SECRET_KEY"] = secret_key
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        hours=int(os.getenv("SESSION_LIFETIME_HOURS", "24"))
    )

    # Session cookie security flags
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # HTTPS enforcement configuration
    app.config["HTTPS_REQUIRED"] = os.getenv("HTTPS_REQUIRED", "false").lower() == "true"
    if app.config["HTTPS_REQUIRED"]:
        logger.info("HTTPS enforcement is ENABLED - HTTP requests will be redirected")

    # Apply custom config if provided
    if config:
        app.config.update(config)

    # CSRF configuration - exempt API routes (they use their own auth)
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True
    app.config["WTF_CSRF_TIME_LIMIT"] = 3600  # 1 hour

    # Initialize CSRF protection
    csrf.init_app(app)

    # Register context processor for injecting current_user into templates
    app.context_processor(inject_user)

    # Wire up tier enforcement callback
    _setup_tier_callback()

    # Validate license key at startup (warn only, don't block)
    _check_license_at_startup()

    # Track if bootstrap check has been done this process
    setattr(app, '_bootstrap_checked', False)

    @app.before_request
    def enforce_https() -> Any:
        """Redirect HTTP to HTTPS when HTTPS_REQUIRED is enabled."""
        from flask import redirect, request

        if not app.config.get("HTTPS_REQUIRED"):
            return None

        # Check if request is already HTTPS
        # Handle both direct connections and proxy forwarding
        is_https = (
            request.is_secure
            or request.headers.get("X-Forwarded-Proto", "").lower() == "https"
            or request.headers.get("X-Forwarded-Ssl") == "on"
        )

        if not is_https:
            # Build HTTPS URL and redirect
            https_url = request.url.replace("http://", "https://", 1)
            return redirect(https_url, code=301)

        return None

    @app.after_request
    def add_security_headers(response: Any) -> Any:
        """Add security headers to HTTPS responses."""
        from flask import request

        if app.config.get("HTTPS_REQUIRED"):
            # Check if this is an HTTPS request
            is_https = (
                request.is_secure
                or request.headers.get("X-Forwarded-Proto", "").lower() == "https"
                or request.headers.get("X-Forwarded-Ssl") == "on"
            )
            if is_https:
                # Add HSTS header
                hsts_max_age = int(os.getenv("HSTS_MAX_AGE", "31536000"))
                include_subdomains = os.getenv("HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true"
                preload = os.getenv("HSTS_PRELOAD", "false").lower() == "true"

                hsts_parts = [f"max-age={hsts_max_age}"]
                if include_subdomains:
                    hsts_parts.append("includeSubDomains")
                if preload:
                    hsts_parts.append("preload")

                response.headers["Strict-Transport-Security"] = "; ".join(hsts_parts)
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["X-XSS-Protection"] = "1; mode=block"

        return response

    @app.before_request
    def check_bootstrap() -> None:
        """Check if bootstrap is needed on first request."""
        from flask import session

        if not getattr(app, '_bootstrap_checked', False):
            if _bootstrap_admin_if_needed():
                # Mark session as first run to show banner
                session["_first_run"] = True
                logger.info("First run detected - showing credentials banner")
            setattr(app, '_bootstrap_checked', True)

    @app.before_request
    def set_tenant_context() -> None:
        """Set tenant context from session for multi-tenant isolation."""
        from flask import g, session

        from mysql_to_sheets.models.repository import set_tenant

        org_id = session.get("organization_id")
        if org_id is not None:
            try:
                g._tenant_token = set_tenant(org_id)
            except (ValueError, TypeError):
                pass

    @app.teardown_request
    def clear_tenant_context(exc: BaseException | None = None) -> None:
        """Clear tenant context after each request."""
        from flask import g

        from mysql_to_sheets.models.repository import clear_tenant

        token = getattr(g, "_tenant_token", None)
        clear_tenant(token)

    @app.context_processor
    def inject_first_run() -> dict[str, Any]:
        """Inject first_run credentials info into templates.

        SECURITY: The generated password is only shown during the first
        session after bootstrap. It's cleared after display to prevent
        password leakage in subsequent requests.
        """
        from flask import session

        global _generated_admin_password

        show_banner = session.get("_first_run", False)
        password_to_show = _generated_admin_password if show_banner else None

        # Clear password from memory after first display
        if password_to_show is not None:
            _generated_admin_password = None

        return {
            "show_first_run_banner": show_banner,
            "default_admin_email": DEFAULT_ADMIN_EMAIL,
            "default_admin_password": password_to_show,
            "password_change_required": show_banner,
        }

    @app.context_processor
    def inject_tier_alerts() -> dict[str, Any]:
        """Inject tier-related alerts into all templates.

        Checks for:
        - Trial expiring (3, 1, 0 days warning)
        - Usage threshold warning (80%)
        - Usage exceeded (100%)
        """
        from flask import session

        tier_alerts: list[dict[str, Any]] = []

        # Only check for authenticated users
        if not session.get("user_id"):
            return {"tier_alerts": tier_alerts}

        try:
            from mysql_to_sheets.core.tenant import get_tenant_db_path
            from mysql_to_sheets.core.tier import TIER_LIMITS, Tier
            from mysql_to_sheets.core.trial import TrialStatus, check_trial_status
            from mysql_to_sheets.models.organizations import get_organization_repository
            from mysql_to_sheets.models.sync_configs import get_sync_config_repository

            org_id = session.get("organization_id")
            if not org_id:
                return {"tier_alerts": tier_alerts}

            db_path = get_tenant_db_path()

            # Check trial status
            try:
                trial_info = check_trial_status(org_id, db_path=db_path)
                if trial_info.status == TrialStatus.ACTIVE:
                    days = trial_info.days_remaining
                    if days <= 0:
                        tier_alerts.append(
                            {
                                "type": "error",
                                "title": "Trial Expired",
                                "message": "Your trial has ended. Upgrade to continue using premium features.",
                                "cta_text": "Upgrade Now",
                                "cta_url": "/tier",
                            }
                        )
                    elif days == 1:
                        tier_alerts.append(
                            {
                                "type": "warning",
                                "title": "Trial Expires Tomorrow",
                                "message": "Your trial ends tomorrow. Upgrade now to avoid service interruption.",
                                "cta_text": "Upgrade Now",
                                "cta_url": "/tier",
                            }
                        )
                    elif days <= 3:
                        tier_alerts.append(
                            {
                                "type": "info",
                                "title": f"Trial Expires in {days} Days",
                                "message": f"Your trial ends in {days} days. Consider upgrading to continue using premium features.",
                                "cta_text": "View Plans",
                                "cta_url": "/tier",
                            }
                        )
            except Exception:
                pass  # Silently ignore trial check errors

            # Check usage quotas
            try:
                org_repo = get_organization_repository(db_path)
                org = org_repo.get_by_id(org_id)

                if org:
                    tier_str = org.subscription_tier or "free"
                    try:
                        tier = Tier(tier_str.lower())
                    except ValueError:
                        tier = Tier.FREE

                    limits = TIER_LIMITS.get(tier, TIER_LIMITS[Tier.FREE])

                    # Check config usage
                    if limits.max_configs is not None:
                        config_repo = get_sync_config_repository(db_path)
                        configs = config_repo.get_all(organization_id=org_id)
                        current_configs = len(configs)
                        usage_percent = (current_configs / limits.max_configs) * 100

                        if current_configs >= limits.max_configs:
                            tier_alerts.append(
                                {
                                    "type": "error",
                                    "title": "Config Limit Reached",
                                    "message": f"You've reached your limit of {limits.max_configs} sync configurations. Upgrade to add more.",
                                    "cta_text": "Upgrade",
                                    "cta_url": "/tier",
                                }
                            )
                        elif usage_percent >= 80:
                            tier_alerts.append(
                                {
                                    "type": "warning",
                                    "title": "Approaching Config Limit",
                                    "message": f"You're using {current_configs} of {limits.max_configs} sync configurations ({usage_percent:.0f}%).",
                                    "cta_text": "View Plans",
                                    "cta_url": "/tier",
                                }
                            )
            except Exception:
                pass  # Silently ignore usage check errors

        except Exception as e:
            logger.debug(f"Tier alert injection skipped: {e}")

        return {"tier_alerts": tier_alerts}

    @app.context_processor
    def inject_setup_status() -> dict[str, Any]:
        """Inject onboarding setup status into all templates.

        This tracks the user's progress through the setup wizard and
        provides completion percentage for the onboarding checklist.
        """
        from pathlib import Path

        def get_setup_status() -> dict[str, Any]:
            """Calculate setup completion status."""
            status = {
                "db_configured": bool(
                    os.getenv("DB_HOST")
                    or os.getenv("DATABASE_URL")
                    or os.getenv("DB_NAME")
                ),
                "sheets_configured": bool(os.getenv("GOOGLE_SHEET_ID")),
                "credentials_present": Path(
                    os.getenv("SERVICE_ACCOUNT_FILE", "./service_account.json")
                ).exists(),
                "first_sync_complete": False,
                "schedule_created": False,
            }

            # Check history for first sync
            try:
                from mysql_to_sheets.core.history import get_history_repository

                history = get_history_repository()
                recent = history.get_recent(limit=1)
                status["first_sync_complete"] = len(recent) > 0
            except Exception:
                pass

            # Check for schedules if scheduler is enabled
            try:
                from mysql_to_sheets.core.config import get_config

                config = get_config()
                if config.scheduler_enabled:
                    scheduler_db_path = os.getenv("SCHEDULER_DB_PATH", "./data/scheduler.db")
                    if Path(scheduler_db_path).exists():
                        from mysql_to_sheets.core.scheduler import get_scheduler_service

                        service = get_scheduler_service(config)
                        scheduler_status = service.get_status()
                        status["schedule_created"] = scheduler_status.get("total_jobs", 0) > 0
            except Exception:
                pass

            # Calculate completion percentage
            completed_count = sum(1 for v in status.values() if v)
            total_count = len(status)
            status["percent"] = int((completed_count / total_count) * 100)
            status["completed"] = completed_count
            status["total"] = total_count

            return status

        return {"get_setup_status": get_setup_status}

    @app.context_processor
    def inject_breadcrumbs() -> dict[str, Any]:
        """Inject automatic breadcrumbs based on the current route.

        This provides a default breadcrumb trail that can be overridden
        in individual templates if needed.
        """
        from flask import request

        # Map routes to breadcrumb configurations
        # Format: 'path': [{'label': 'Section'}, {'label': 'Page'}]
        breadcrumb_map: dict[str, list[dict[str, str | None]]] = {
            # Sync section
            "/configs": [{"label": "Sync", "url": "/configs"}, {"label": "Configurations", "url": None}],
            "/worksheets": [{"label": "Sync", "url": "/configs"}, {"label": "Worksheets", "url": None}],
            "/favorites": [{"label": "Sync", "url": "/configs"}, {"label": "Favorites", "url": None}],
            "/snapshots": [{"label": "Sync", "url": "/configs"}, {"label": "Snapshots", "url": None}],
            "/reverse-sync": [{"label": "Sync", "url": "/configs"}, {"label": "Reverse Sync", "url": None}],
            "/multi-sync": [{"label": "Sync", "url": "/configs"}, {"label": "Multi-Sheet Sync", "url": None}],
            "/history": [{"label": "Sync", "url": "/configs"}, {"label": "History", "url": None}],
            # Schedule section
            "/schedules": [{"label": "Schedule", "url": "/schedules"}, {"label": "Schedules", "url": None}],
            "/jobs": [{"label": "Schedule", "url": "/schedules"}, {"label": "Job Queue", "url": None}],
            "/freshness": [{"label": "Schedule", "url": "/schedules"}, {"label": "Freshness", "url": None}],
            "/agents": [{"label": "Monitoring", "url": "/agents"}, {"label": "Agents", "url": None}],
            # Admin section
            "/users": [{"label": "Admin", "url": "/users"}, {"label": "Users", "url": None}],
            "/api-keys": [{"label": "Admin", "url": "/users"}, {"label": "API Keys", "url": None}],
            "/webhooks": [{"label": "Admin", "url": "/users"}, {"label": "Webhooks", "url": None}],
            "/tier": [{"label": "Admin", "url": "/users"}, {"label": "Tier & Usage", "url": None}],
            "/audit": [{"label": "Admin", "url": "/users"}, {"label": "Audit Log", "url": None}],
            # Help section
            "/health": [{"label": "Help", "url": "/health"}, {"label": "System Health", "url": None}],
            "/diagnostics": [{"label": "Help", "url": "/health"}, {"label": "Diagnostics", "url": None}],
            "/errors": [{"label": "Help", "url": "/health"}, {"label": "Error Log", "url": None}],
            "/setup": [{"label": "Setup Wizard", "url": None}],
        }

        path = request.path
        auto_breadcrumbs = breadcrumb_map.get(path, [])

        return {"auto_breadcrumbs": auto_breadcrumbs}

    # Inject version into all templates
    @app.context_processor
    def inject_version() -> dict[str, str]:
        """Inject application version into all templates."""
        return {"version": __version__}

    # Inject super admin flag into all templates
    @app.context_processor
    def inject_super_admin_flag() -> dict[str, bool]:
        """Inject super admin enabled flag into all templates."""
        from flask import session

        from mysql_to_sheets.web.blueprints.super_admin import is_super_admin_enabled

        enabled = is_super_admin_enabled()
        role = session.get("role")
        user_id = session.get("user_id")

        # Debug logging for intermittent Super Admin visibility issue
        if user_id:
            visible = enabled and role == "owner"
            print(
                f"[SUPER_ADMIN] visibility check: enabled={enabled}, "
                f"session_role={role!r}, user_id={user_id}, visible={visible}",
                flush=True,
            )

        return {"super_admin_enabled": enabled}

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    logger.info(f"Flask app created (version {__version__})")
    return app


def _register_blueprints(app: Flask) -> None:
    """Register all blueprints with the application.

    Args:
        app: Flask application instance.
    """
    from mysql_to_sheets.web.blueprints.agents_bp import agents_api_bp, agents_bp
    from mysql_to_sheets.web.blueprints.api.audit import audit_api_bp
    from mysql_to_sheets.web.blueprints.api.configs import configs_api_bp
    from mysql_to_sheets.web.blueprints.api.favorites import favorites_api_bp
    from mysql_to_sheets.web.blueprints.api.freshness import freshness_api_bp
    from mysql_to_sheets.web.blueprints.api.jobs import jobs_api_bp
    from mysql_to_sheets.web.blueprints.api.schedules import schedules_api_bp
    from mysql_to_sheets.web.blueprints.api.snapshots import snapshots_api_bp
    from mysql_to_sheets.web.blueprints.api.sync import sync_api_bp
    from mysql_to_sheets.web.blueprints.api.users import users_api_bp
    from mysql_to_sheets.web.blueprints.api.webhooks import webhooks_api_bp
    from mysql_to_sheets.web.blueprints.api.worksheets import worksheets_api_bp
    from mysql_to_sheets.web.blueprints.api_keys_bp import api_keys_api_bp, api_keys_bp
    from mysql_to_sheets.web.blueprints.auth import auth_bp
    from mysql_to_sheets.web.blueprints.dashboard import dashboard_bp
    from mysql_to_sheets.web.blueprints.databases_bp import databases_bp
    from mysql_to_sheets.web.blueprints.diagnostics_bp import diagnostics_api_bp, diagnostics_bp
    from mysql_to_sheets.web.blueprints.errors import errors_bp
    from mysql_to_sheets.web.blueprints.freshness_bp import freshness_bp, freshness_page_api_bp
    from mysql_to_sheets.web.blueprints.health import health_bp
    from mysql_to_sheets.web.blueprints.heartbeat import heartbeat_bp
    from mysql_to_sheets.web.blueprints.multi_sheet_bp import multi_sheet_api_bp, multi_sheet_bp
    from mysql_to_sheets.web.blueprints.offline import offline_bp
    from mysql_to_sheets.web.blueprints.progress_sse import progress_sse_bp
    from mysql_to_sheets.web.blueprints.reverse_sync_bp import reverse_sync_api_bp, reverse_sync_bp
    from mysql_to_sheets.web.blueprints.super_admin import (
        is_super_admin_enabled,
        super_admin_api_bp,
        super_admin_bp,
    )
    from mysql_to_sheets.web.blueprints.tier_bp import tier_api_bp, tier_bp

    # Auth routes (no prefix)
    app.register_blueprint(auth_bp)

    # Dashboard routes (no prefix)
    app.register_blueprint(dashboard_bp)

    # Troubleshooting routes (no prefix)
    app.register_blueprint(errors_bp)
    app.register_blueprint(health_bp)

    # Heartbeat for desktop app browser tracking (exempt from CSRF)
    app.register_blueprint(heartbeat_bp)
    csrf.exempt(heartbeat_bp)

    # New feature pages (no prefix)
    app.register_blueprint(tier_bp)
    app.register_blueprint(freshness_bp)
    app.register_blueprint(api_keys_bp)
    app.register_blueprint(diagnostics_bp)
    app.register_blueprint(reverse_sync_bp)
    app.register_blueprint(multi_sheet_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(databases_bp)

    # Super admin routes (only if enabled)
    if is_super_admin_enabled():
        app.register_blueprint(super_admin_bp)
        app.register_blueprint(super_admin_api_bp)
        csrf.exempt(super_admin_api_bp)
        logger.info("Super admin feature is ENABLED")

    # API routes (prefixed) - exempt from CSRF (they use their own auth)
    api_blueprints = [
        sync_api_bp,
        schedules_api_bp,
        users_api_bp,
        configs_api_bp,
        webhooks_api_bp,
        favorites_api_bp,
        audit_api_bp,
        jobs_api_bp,
        freshness_api_bp,
        snapshots_api_bp,
        worksheets_api_bp,
        # New API routes
        tier_api_bp,
        freshness_page_api_bp,
        api_keys_api_bp,
        diagnostics_api_bp,
        reverse_sync_api_bp,
        multi_sheet_api_bp,
        agents_api_bp,
        progress_sse_bp,
        offline_bp,
    ]
    for bp in api_blueprints:
        app.register_blueprint(bp)
        csrf.exempt(bp)

    logger.debug("All blueprints registered")


def _register_error_handlers(app: Flask) -> None:
    """Register error handlers for the application.

    Args:
        app: Flask application instance.
    """
    from flask import jsonify, render_template, request

    from mysql_to_sheets.core.exceptions import SyncError

    @app.errorhandler(404)
    def not_found(error: Exception) -> tuple[Any, int]:
        """Handle 404 errors."""
        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "success": False,
                    "error": {"code": "NOT_FOUND", "message": "Resource not found"},
                    "message": str(error),
                }
            ), 404
        return render_template(
            "error.html",
            error="Page Not Found",
            message="The page you requested could not be found.",
            error_code=None,
            error_category=None,
            remediation=None,
            show_retry=False,
        ), 404

    @app.errorhandler(500)
    def server_error(error: Exception) -> tuple[Any, int]:
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}")
        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "success": False,
                    "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"},
                    "message": str(error),
                }
            ), 500
        return render_template(
            "error.html",
            error="Server Error",
            message="An internal server error occurred. Please try again later.",
            error_code="INTERNAL_ERROR",
            error_category="transient",
            remediation="Try refreshing the page. If the problem persists, check the server logs.",
            show_retry=True,
        ), 500

    @app.errorhandler(SyncError)
    def handle_sync_error(error: SyncError) -> tuple[Any, int]:
        """Handle SyncError exceptions with detailed error info."""
        logger.error(f"SyncError: {error.code} - {error.message}")
        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "success": False,
                    "error": {
                        "code": error.code,
                        "message": error.message,
                        "category": error.category.value if error.category else None,
                        "remediation": error.remediation,
                    },
                    "message": error.message,
                }
            ), 500
        return render_template(
            "error.html",
            error=error.message,
            message=str(error),
            error_code=error.code,
            error_category=error.category.value if error.category else None,
            remediation=error.remediation,
            show_retry=error.category and error.category.value == "transient",
        ), 500

    @app.errorhandler(403)
    def forbidden(error: Exception) -> tuple[Any, int]:
        """Handle 403 errors."""
        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "success": False,
                    "error": {"code": "FORBIDDEN", "message": "Access denied"},
                    "message": str(error),
                }
            ), 403
        return render_template(
            "error.html",
            error="Access Denied",
            message="You don't have permission to access this resource.",
            error_code="FORBIDDEN",
            error_category="permission",
            remediation="Contact your administrator if you believe you should have access.",
            show_retry=False,
        ), 403

    @app.errorhandler(401)
    def unauthorized(error: Exception) -> tuple[Any, int]:
        """Handle 401 errors."""
        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "success": False,
                    "error": {"code": "UNAUTHORIZED", "message": "Authentication required"},
                    "message": str(error),
                }
            ), 401
        return render_template(
            "error.html",
            error="Authentication Required",
            message="Please log in to access this page.",
            error_code="UNAUTHORIZED",
            error_category="permission",
            remediation="Log in with your credentials to continue.",
            show_retry=False,
        ), 401


def _cleanup_on_shutdown() -> None:
    """Perform cleanup tasks on application shutdown.

    Called via atexit to ensure cleanup happens even on SIGTERM.
    """
    try:
        from mysql_to_sheets.core.auth import cleanup_expired_tokens

        removed = cleanup_expired_tokens()
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired token blacklist entries")
    except Exception as e:
        logger.debug(f"Shutdown cleanup skipped: {e}")


# Register shutdown cleanup
atexit.register(_cleanup_on_shutdown)


# Create default app instance for gunicorn/flask run
app = create_app()
