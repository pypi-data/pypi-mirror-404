"""Audit logging service for enterprise compliance.

Provides a centralized service for logging auditable events across
the application. Supports thread-local request context for capturing
source IP, user agent, and user information.
"""

import re
import threading
from enum import Enum
from typing import Any

from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)


class AuditAction(str, Enum):
    """Types of actions that can be audited.

    Actions follow the format: resource.verb (e.g., sync.completed)
    """

    # Sync events
    SYNC_STARTED = "sync.started"
    SYNC_COMPLETED = "sync.completed"
    SYNC_FAILED = "sync.failed"

    # Error events
    SYNC_ERROR = "sync.error"
    CONNECTION_FAILED = "connection.failed"
    RETRY_EXHAUSTED = "retry.exhausted"
    CONSECUTIVE_FAILURES = "alert.consecutive_failures"

    # Authentication events
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_PASSWORD_CHANGED = "auth.password_changed"
    AUTH_PASSWORD_RESET = "auth.password_reset"

    # User management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_DEACTIVATED = "user.deactivated"
    USER_ACTIVATED = "user.activated"
    USER_ROLE_CHANGED = "user.role_changed"

    # Organization management
    ORG_CREATED = "org.created"
    ORG_UPDATED = "org.updated"
    ORG_DELETED = "org.deleted"
    ORG_DEACTIVATED = "org.deactivated"

    # Config management
    CONFIG_CREATED = "config.created"
    CONFIG_UPDATED = "config.updated"
    CONFIG_DELETED = "config.deleted"

    # Schedule management
    SCHEDULE_CREATED = "schedule.created"
    SCHEDULE_UPDATED = "schedule.updated"
    SCHEDULE_DELETED = "schedule.deleted"
    SCHEDULE_ENABLED = "schedule.enabled"
    SCHEDULE_DISABLED = "schedule.disabled"
    SCHEDULE_TRIGGERED = "schedule.triggered"

    # Webhook management
    WEBHOOK_CREATED = "webhook.created"
    WEBHOOK_UPDATED = "webhook.updated"
    WEBHOOK_DELETED = "webhook.deleted"
    WEBHOOK_ENABLED = "webhook.enabled"
    WEBHOOK_DISABLED = "webhook.disabled"

    # API key management
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"

    # Audit log access
    AUDIT_EXPORTED = "audit.exported"
    AUDIT_VIEWED = "audit.viewed"


# All valid action types as strings
VALID_AUDIT_ACTIONS = [a.value for a in AuditAction]


# Thread-local storage for request context
_request_context = threading.local()


class RequestContext:
    """Context for the current request.

    Stores request-scoped information for audit logging.
    """

    def __init__(
        self,
        source_ip: str | None = None,
        user_agent: str | None = None,
        user_id: int | None = None,
        organization_id: int | None = None,
    ) -> None:
        self.source_ip = source_ip
        self.user_agent = user_agent
        self.user_id = user_id
        self.organization_id = organization_id


def set_request_context(
    source_ip: str | None = None,
    user_agent: str | None = None,
    user_id: int | None = None,
    organization_id: int | None = None,
) -> None:
    """Set the request context for the current thread.

    Should be called at the start of each request to capture
    contextual information for audit logging.

    Args:
        source_ip: Client IP address.
        user_agent: Client user agent string.
        user_id: Authenticated user ID.
        organization_id: User's organization ID.
    """
    _request_context.context = RequestContext(
        source_ip=source_ip,
        user_agent=user_agent,
        user_id=user_id,
        organization_id=organization_id,
    )


def get_request_context() -> RequestContext | None:
    """Get the request context for the current thread.

    Returns:
        RequestContext if set, None otherwise.
    """
    return getattr(_request_context, "context", None)


def clear_request_context() -> None:
    """Clear the request context for the current thread.

    Should be called at the end of each request.
    """
    if hasattr(_request_context, "context"):
        del _request_context.context


def update_request_context(
    user_id: int | None = None,
    organization_id: int | None = None,
) -> None:
    """Update the request context with user information.

    Called after authentication to add user context.

    Args:
        user_id: Authenticated user ID.
        organization_id: User's organization ID.
    """
    ctx = get_request_context()
    if ctx:
        if user_id is not None:
            ctx.user_id = user_id
        if organization_id is not None:
            ctx.organization_id = organization_id


def sanitize_sql_query(query: str | None) -> str | None:
    """Sanitize SQL query by removing sensitive parameter values.

    Replaces literal values (strings, numbers) with placeholders to
    avoid logging sensitive data while preserving query structure.

    Args:
        query: SQL query string.

    Returns:
        Sanitized query or None if input is None.
    """
    if query is None:
        return None

    # Replace quoted string values with placeholder
    # Matches both single and double quoted strings
    sanitized = re.sub(r"'[^']*'", "'?'", query)
    sanitized = re.sub(r'"[^"]*"', '"?"', sanitized)

    # Replace numeric values in common patterns
    # After = or IN clauses
    sanitized = re.sub(r"=\s*\d+", "= ?", sanitized)
    sanitized = re.sub(r"IN\s*\([^)]+\)", "IN (?)", sanitized, flags=re.IGNORECASE)

    # Replace LIMIT/OFFSET values
    sanitized = re.sub(r"LIMIT\s+\d+", "LIMIT ?", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"OFFSET\s+\d+", "OFFSET ?", sanitized, flags=re.IGNORECASE)

    return sanitized


def log_action(
    action: str | AuditAction,
    resource_type: str,
    organization_id: int,
    db_path: str,
    resource_id: str | None = None,
    user_id: int | None = None,
    source_ip: str | None = None,
    user_agent: str | None = None,
    query_executed: str | None = None,
    rows_affected: int | None = None,
    metadata: dict[str, Any] | None = None,
    sanitize_query: bool = True,
) -> None:
    """Log an auditable action.

    This is the main function for recording audit events. It will use
    request context if available to fill in missing fields.

    Args:
        action: Action type (AuditAction enum or string).
        resource_type: Type of resource affected (e.g., "sync", "user").
        organization_id: Organization ID for the event.
        db_path: Path to the audit log database.
        resource_id: Optional identifier for the specific resource.
        user_id: User who performed the action (uses context if None).
        source_ip: Client IP (uses context if None).
        user_agent: Client user agent (uses context if None).
        query_executed: SQL query that was executed (optional).
        rows_affected: Number of rows affected (optional).
        metadata: Additional context as JSON-serializable dict.
        sanitize_query: Whether to sanitize the SQL query (default True).
    """
    from mysql_to_sheets.models.audit_logs import AuditLog, get_audit_log_repository

    # Convert enum to string if needed
    action_str = action.value if isinstance(action, AuditAction) else action

    # Get context values if not provided
    ctx = get_request_context()
    if ctx:
        user_id = user_id if user_id is not None else ctx.user_id
        source_ip = source_ip or ctx.source_ip
        user_agent = user_agent or ctx.user_agent

    # Sanitize SQL query if requested
    if sanitize_query and query_executed:
        query_executed = sanitize_sql_query(query_executed)

    # Truncate user agent if too long
    if user_agent and len(user_agent) > 500:
        user_agent = user_agent[:497] + "..."

    try:
        repo = get_audit_log_repository(db_path)
        log = AuditLog(
            action=action_str,
            resource_type=resource_type,
            organization_id=organization_id,
            user_id=user_id,
            resource_id=resource_id,
            source_ip=source_ip,
            user_agent=user_agent,
            query_executed=query_executed,
            rows_affected=rows_affected,
            metadata=metadata,
        )
        repo.add(log)
        logger.debug(f"Audit: {action_str} on {resource_type} (org={organization_id})")
    except (ImportError, OSError, RuntimeError) as e:
        # Audit logging should never break the main flow
        logger.warning(f"Failed to write audit log: {e}")


def log_sync_event(
    event: str,
    organization_id: int,
    db_path: str,
    sync_id: str | None = None,
    config_name: str | None = None,
    rows_synced: int | None = None,
    query: str | None = None,
    error: str | None = None,
    duration_seconds: float | None = None,
    source: str = "cli",
) -> None:
    """Log a sync-related audit event.

    Convenience function for sync operations.

    Args:
        event: Sync event type (started, completed, failed).
        organization_id: Organization ID.
        db_path: Path to audit log database.
        sync_id: Unique sync operation ID.
        config_name: Name of the sync configuration.
        rows_synced: Number of rows synced.
        query: SQL query executed.
        error: Error message if failed.
        duration_seconds: Sync duration in seconds.
        source: Source of sync (cli, api, web, scheduler).
    """
    action_map = {
        "started": AuditAction.SYNC_STARTED,
        "completed": AuditAction.SYNC_COMPLETED,
        "failed": AuditAction.SYNC_FAILED,
    }
    action = action_map.get(event, event)

    metadata = {
        "sync_id": sync_id,
        "config_name": config_name,
        "source": source,
    }
    if error:
        metadata["error"] = error
    if duration_seconds is not None:
        metadata["duration_seconds"] = str(round(duration_seconds, 2))

    log_action(
        action=action,
        resource_type="sync",
        organization_id=organization_id,
        db_path=db_path,
        resource_id=sync_id,
        query_executed=query,
        rows_affected=rows_synced,
        metadata=metadata,
    )


def log_auth_event(
    event: str,
    organization_id: int,
    db_path: str,
    user_id: int | None = None,
    email: str | None = None,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Log an authentication-related audit event.

    Convenience function for auth operations.

    Args:
        event: Auth event type (login, logout, login_failed).
        organization_id: Organization ID.
        db_path: Path to audit log database.
        user_id: User ID (if known).
        email: User email (for failed logins where user_id unknown).
        success: Whether the auth action succeeded.
        error: Error message if failed.
    """
    action_map = {
        "login": AuditAction.AUTH_LOGIN,
        "logout": AuditAction.AUTH_LOGOUT,
        "login_failed": AuditAction.AUTH_LOGIN_FAILED,
        "password_changed": AuditAction.AUTH_PASSWORD_CHANGED,
        "password_reset": AuditAction.AUTH_PASSWORD_RESET,
    }
    action = action_map.get(event, event)

    metadata: dict[str, Any] = {"success": success}
    if email:
        metadata["email"] = email
    if error:
        metadata["error"] = error

    log_action(
        action=action,
        resource_type="auth",
        organization_id=organization_id,
        db_path=db_path,
        user_id=user_id,
        resource_id=str(user_id) if user_id else None,
        metadata=metadata,
    )


def log_management_event(
    action: str | AuditAction,
    resource_type: str,
    resource_id: str | int,
    organization_id: int,
    db_path: str,
    changes: dict[str, Any] | None = None,
    user_id: int | None = None,
) -> None:
    """Log a resource management event.

    Convenience function for CRUD operations on configs, users,
    webhooks, schedules, etc.

    Args:
        action: Management action (created, updated, deleted, etc.).
        resource_type: Type of resource (user, config, webhook, etc.).
        resource_id: ID of the affected resource.
        organization_id: Organization ID.
        db_path: Path to audit log database.
        changes: Dict of changed fields (for updates).
        user_id: User who performed the action.
    """
    metadata = {}
    if changes:
        # Only include non-sensitive changes
        safe_changes = {
            k: v
            for k, v in changes.items()
            if k not in ("password", "password_hash", "secret", "api_key")
        }
        if safe_changes:
            metadata["changes"] = safe_changes

    log_action(
        action=action,
        resource_type=resource_type,
        organization_id=organization_id,
        db_path=db_path,
        resource_id=str(resource_id),
        user_id=user_id,
        metadata=metadata if metadata else None,
    )


def log_error_event(
    error_code: str,
    error_category: str,
    organization_id: int,
    db_path: str,
    error_message: str,
    resource_type: str = "sync",
    resource_id: str | None = None,
    connection_type: str | None = None,
) -> None:
    """Log an error audit event.

    Convenience function for recording errors with standardized error codes.

    Args:
        error_code: Standardized error code (e.g., DB_201).
        error_category: Error category (transient, permanent, etc.).
        organization_id: Organization ID.
        db_path: Path to audit log database.
        error_message: Human-readable error message.
        resource_type: Type of resource (sync, connection, etc.).
        resource_id: Optional resource identifier.
        connection_type: Type of connection (database, sheets).
    """
    metadata: dict[str, Any] = {
        "error_code": error_code,
        "error_category": error_category,
        "error_message": error_message,
    }
    if connection_type:
        metadata["connection_type"] = connection_type

    # Determine action based on error type
    if "connection" in resource_type.lower() or connection_type:
        action = AuditAction.CONNECTION_FAILED
    else:
        action = AuditAction.SYNC_ERROR

    log_action(
        action=action,
        resource_type=resource_type,
        organization_id=organization_id,
        db_path=db_path,
        resource_id=resource_id,
        metadata=metadata,
    )


def log_retry_exhausted_event(
    error_code: str,
    organization_id: int,
    db_path: str,
    attempts: int,
    last_error: str,
    operation: str = "sync",
    resource_id: str | None = None,
) -> None:
    """Log a retry exhausted audit event.

    Records when all retry attempts have been exhausted.

    Args:
        error_code: Error code of the final failure.
        organization_id: Organization ID.
        db_path: Path to audit log database.
        attempts: Total number of attempts made.
        last_error: Last error message.
        operation: Operation that was being retried.
        resource_id: Optional resource identifier.
    """
    metadata: dict[str, Any] = {
        "error_code": error_code,
        "attempts": attempts,
        "last_error": last_error,
        "operation": operation,
    }

    log_action(
        action=AuditAction.RETRY_EXHAUSTED,
        resource_type="retry",
        organization_id=organization_id,
        db_path=db_path,
        resource_id=resource_id,
        metadata=metadata,
    )


def log_consecutive_failures_alert(
    organization_id: int,
    db_path: str,
    config_id: str | int,
    consecutive_count: int,
    threshold: int,
    last_error: str | None = None,
) -> None:
    """Log a consecutive failures alert event.

    Records when consecutive failure count exceeds the alert threshold.

    Args:
        organization_id: Organization ID.
        db_path: Path to audit log database.
        config_id: Sync configuration ID.
        consecutive_count: Current consecutive failure count.
        threshold: Alert threshold that was exceeded.
        last_error: Most recent error message.
    """
    metadata: dict[str, Any] = {
        "config_id": str(config_id),
        "consecutive_count": consecutive_count,
        "threshold": threshold,
    }
    if last_error:
        metadata["last_error"] = last_error

    log_action(
        action=AuditAction.CONSECUTIVE_FAILURES,
        resource_type="alert",
        organization_id=organization_id,
        db_path=db_path,
        resource_id=str(config_id),
        metadata=metadata,
    )


# Context manager for request scope
class AuditContext:
    """Context manager for request-scoped audit logging.

    Usage:
        with AuditContext(source_ip="1.2.3.4", user_agent="Mozilla"):
            # Audit logs in this block will include context
            log_action(...)
    """

    def __init__(
        self,
        source_ip: str | None = None,
        user_agent: str | None = None,
        user_id: int | None = None,
        organization_id: int | None = None,
    ) -> None:
        self.source_ip = source_ip
        self.user_agent = user_agent
        self.user_id = user_id
        self.organization_id = organization_id

    def __enter__(self) -> "AuditContext":
        set_request_context(
            source_ip=self.source_ip,
            user_agent=self.user_agent,
            user_id=self.user_id,
            organization_id=self.organization_id,
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        clear_request_context()
