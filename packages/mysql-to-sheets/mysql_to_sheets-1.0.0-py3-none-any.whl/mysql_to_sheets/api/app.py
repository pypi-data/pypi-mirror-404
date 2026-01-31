"""FastAPI application for MySQL to Google Sheets sync API."""

import asyncio
import logging
import os
import signal
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mysql_to_sheets import __version__
from mysql_to_sheets.api.audit_routes import router as audit_router
from mysql_to_sheets.api.billing_webhook_routes import router as billing_webhook_router
from mysql_to_sheets.api.freshness_routes import router as freshness_router
from mysql_to_sheets.api.job_routes import router as job_router
from mysql_to_sheets.api.metrics_routes import HTTPMetricsMiddleware
from mysql_to_sheets.api.metrics_routes import router as metrics_router
from mysql_to_sheets.api.middleware import (
    AuditContextMiddleware,
    AuthMiddleware,
    HTTPSRedirectMiddleware,
    OrganizationContextMiddleware,
    RateLimitMiddleware,
    RBACMiddleware,
    RequestSizeLimitMiddleware,
    ScopeMiddleware,
    UsageTrackerMiddleware,
    UserAuthMiddleware,
)
from mysql_to_sheets.api.rollback_routes import router as rollback_router
from mysql_to_sheets.api.routes import router
from mysql_to_sheets.api.routes_agent import router as agent_router
from mysql_to_sheets.api.routes_pii import router as pii_router
from mysql_to_sheets.api.usage_routes import router as usage_router
from mysql_to_sheets.core.config import get_config

logger = logging.getLogger("mysql_to_sheets.api")

# Global shutdown event for graceful shutdown
_shutdown_event: asyncio.Event | None = None
_active_requests: int = 0
_request_lock = asyncio.Lock()


async def increment_active_requests() -> None:
    """Increment active request counter."""
    global _active_requests
    async with _request_lock:
        _active_requests += 1


async def decrement_active_requests() -> None:
    """Decrement active request counter."""
    global _active_requests
    async with _request_lock:
        _active_requests -= 1


async def get_active_requests() -> int:
    """Get current active request count."""
    async with _request_lock:
        return _active_requests


async def wait_for_requests_to_drain(timeout: float = 30.0) -> bool:
    """Wait for in-flight requests to complete.

    Args:
        timeout: Maximum seconds to wait.

    Returns:
        True if all requests drained, False if timeout.
    """
    start = asyncio.get_event_loop().time()
    while await get_active_requests() > 0:
        if asyncio.get_event_loop().time() - start > timeout:
            logger.warning(f"Shutdown timeout: {await get_active_requests()} requests still active")
            return False
        await asyncio.sleep(0.1)
    return True


def _maybe_bootstrap_api_key() -> None:
    """Generate a bootstrap API key if auth is enabled and no keys exist."""
    try:
        config = get_config()
        if not config.api_auth_enabled:
            return

        from mysql_to_sheets.core.security import (
            generate_api_key,
            generate_api_key_salt,
            hash_api_key,
        )
        from mysql_to_sheets.models.api_keys import get_api_key_repository

        repo = get_api_key_repository(config.api_keys_db_path)
        if repo.count() > 0:
            return

        raw_key = generate_api_key()
        key_salt = generate_api_key_salt()
        key_hash = hash_api_key(raw_key, key_salt)
        repo.create(
            name="bootstrap",
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=raw_key[:8],
            description="Auto-generated on first API server start",
        )

        # Write key to a secure file instead of stdout to avoid log leaks
        key_file = os.path.join(os.path.dirname(config.api_keys_db_path), "bootstrap_api_key.txt")
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, "w") as f:
            f.write(raw_key)
        os.chmod(key_file, 0o600)

        print(f"\n  Bootstrap API key written to: {key_file}")
        print(f"  Default location: $API_KEYS_DB_PATH/../bootstrap_api_key.txt")
        print(f"  Lost your key? Create a new one with:")
        print(f"    mysql-to-sheets api-key create --name=my-key\n")
        logger.info(f"Bootstrap API key created (prefix={raw_key[:8]}...), saved to {key_file}")
    except Exception as e:
        logger.debug(f"Bootstrap API key generation skipped: {e}")


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
    """Validate license key and log warnings for invalid/expired licenses.

    This is advisory only — the app still starts, but operators get
    early visibility into license problems instead of discovering them
    at the first tier-gated request.
    """
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events.

    Args:
        app: FastAPI application instance.

    Yields:
        None after startup, cleanup after shutdown.
    """
    global _shutdown_event

    # Startup: Initialize resources
    _shutdown_event = asyncio.Event()
    logger.info(f"Starting MySQL to Sheets API v{__version__}")

    # Bootstrap: Generate initial API key if none exist and auth is enabled
    _maybe_bootstrap_api_key()

    # Wire up tier enforcement callback so @require_tier works
    _setup_tier_callback()

    # Validate license key at startup (warn only, don't block)
    _check_license_at_startup()

    # Setup signal handlers for graceful shutdown
    def handle_signal(signum: int, frame: object) -> None:
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        if _shutdown_event:
            _shutdown_event.set()

    # Register signal handlers (only in main thread)
    try:
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)
    except ValueError:
        # Signal handlers can only be set in main thread
        pass

    yield

    # Shutdown: Cleanup resources
    logger.info("Shutting down API server...")

    # Wait for in-flight requests to complete
    drained = await wait_for_requests_to_drain(timeout=30.0)
    if drained:
        logger.info("All requests completed, shutdown complete")
    else:
        logger.warning("Shutdown with pending requests")

    # Cleanup token blacklist expired entries
    try:
        from mysql_to_sheets.core.auth import cleanup_expired_tokens

        removed = cleanup_expired_tokens()
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired token blacklist entries")
    except Exception as e:
        logger.debug(f"Token cleanup skipped: {e}")

    # Close PostgreSQL connection pool if active
    try:
        from mysql_to_sheets.core.database.postgres import reset_pg_pool

        reset_pg_pool()
        logger.info("PostgreSQL connection pool closed")
    except Exception as e:
        logger.debug(f"PostgreSQL pool cleanup skipped: {e}")


def _parse_cors_origins(origins_str: str) -> list[str]:
    """Parse CORS origins from config string.

    Args:
        origins_str: Comma-separated origins or empty string.

    Returns:
        List of origin strings.
    """
    if not origins_str or not origins_str.strip():
        return []
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="MySQL to Google Sheets Sync API",
        description=(
            "REST API for synchronizing data from SQL databases to Google Sheets.\n\n"
            "## Authentication\n\n"
            "Most endpoints require an API key via the `X-API-Key` header. "
            "A bootstrap key is printed to stdout on first server start.\n\n"
            "To create additional keys:\n"
            "```\nmysql-to-sheets api-key create --name=my-key\n```\n\n"
            "Exempt paths: `/api/v1/health`, `/docs`, `/redoc`, `/metrics`"
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Load CORS configuration
    config = get_config()
    cors_origins = _parse_cors_origins(config.cors_allowed_origins)

    # Security: Warn if wildcard CORS is configured
    if config.cors_allowed_origins == "*":
        logger.warning(
            "CORS is configured with wildcard '*' - this is insecure for production. "
            "Set CORS_ALLOWED_ORIGINS to specific origins."
        )
        cors_origins = ["*"]

    # Security: Only allow credentials when origins are explicitly specified
    # (not wildcard) to prevent credential leakage
    allow_credentials = bool(cors_origins) and cors_origins != ["*"]

    # CORS middleware for frontend integrations
    # Default: No CORS (empty origins list) - most secure
    # Configure CORS_ALLOWED_ORIGINS for specific origins
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=allow_credentials,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )

    # HTTPS enforcement middleware - redirects HTTP to HTTPS
    # Enabled via HTTPS_REQUIRED=true (default: false)
    # Also adds HSTS headers for enhanced security
    https_required = os.getenv("HTTPS_REQUIRED", "false").lower() == "true"
    if https_required:
        logger.info("HTTPS enforcement is ENABLED - HTTP requests will be redirected")
    app.add_middleware(HTTPSRedirectMiddleware, enabled=https_required)

    # Usage tracking middleware (records sync operations and API calls)
    app.add_middleware(UsageTrackerMiddleware)

    # Audit context middleware (captures request info for audit logging)
    app.add_middleware(AuditContextMiddleware)

    # Request size limit middleware - prevent DoS via large payloads
    # Default: 10MB limit (configurable via MAX_REQUEST_SIZE_MB env var)
    max_request_size = int(os.getenv("MAX_REQUEST_SIZE_MB", "10")) * 1024 * 1024
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_body_size=max_request_size,
    )

    # Security middleware stack (order matters - outermost runs first)
    # 1. Rate limiting - prevent brute force/DoS
    # 2. API key auth - for machine-to-machine access
    # 3. JWT user auth - for user sessions
    # 4. Organization context - multi-tenant isolation
    # 5. RBAC - permission checks

    # Rate limiting middleware (enabled by RATE_LIMIT_ENABLED env var)
    app.add_middleware(
        RateLimitMiddleware,
        enabled=config.rate_limit_enabled,
        requests_per_minute=config.rate_limit_rpm,
    )

    # API key authentication (enabled by API_AUTH_ENABLED env var)
    # Default is now True for production security
    api_auth_enabled = config.api_auth_enabled
    if api_auth_enabled:
        logger.info("API key authentication is ENABLED")
    else:
        logger.warning(
            "API key authentication is DISABLED. Set API_AUTH_ENABLED=true for production."
        )

    app.add_middleware(
        AuthMiddleware,
        enabled=api_auth_enabled,
        db_path=config.api_keys_db_path,
    )

    # API key scope enforcement (validates key has required scopes for endpoints)
    # Enabled by API_KEY_SCOPE_ENABLED env var (default: true when auth is enabled)
    scope_enabled = os.getenv("API_KEY_SCOPE_ENABLED", "true").lower() == "true"
    if api_auth_enabled and scope_enabled:
        logger.info("API key scope enforcement is ENABLED")
        app.add_middleware(ScopeMiddleware, enabled=True)

    # JWT user authentication (enabled when JWT_SECRET_KEY is set)
    jwt_auth_enabled = bool(config.jwt_secret_key)
    if jwt_auth_enabled:
        logger.info("JWT user authentication is ENABLED")
        app.add_middleware(
            UserAuthMiddleware,
            enabled=True,
            db_path=config.tenant_db_path,
        )

        # Organization context (ensures multi-tenant isolation)
        app.add_middleware(
            OrganizationContextMiddleware,
            enabled=True,
        )

        # RBAC middleware (permission checks - fail-closed by default)
        app.add_middleware(
            RBACMiddleware,
            enabled=True,
        )

    # HTTP metrics middleware (records request counts and durations)
    # Only enabled when METRICS_ENABLED=true
    if config.metrics_enabled:
        logger.info("HTTP metrics collection is ENABLED")
        app.add_middleware(HTTPMetricsMiddleware, enabled=True)

    # Include API routes
    app.include_router(router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(billing_webhook_router, prefix="/api/v1")
    app.include_router(job_router, prefix="/api/v1")
    app.include_router(freshness_router, prefix="/api/v1")
    app.include_router(rollback_router, prefix="/api/v1")
    app.include_router(usage_router, prefix="/api/v1")
    app.include_router(pii_router, prefix="/api/v1")

    # Metrics endpoint at root level (not under /api/v1)
    app.include_router(metrics_router)

    # Agent API routes (separate auth via LINK_TOKEN)
    app.include_router(agent_router)

    return app


# Default application instance
app = create_app()


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
) -> None:
    """Run the API server.

    Args:
        host: Host to bind to.
        port: Port to listen on.
        reload: Enable auto-reload for development.
    """
    import uvicorn

    uvicorn.run(
        "mysql_to_sheets.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run_server(reload=True)
