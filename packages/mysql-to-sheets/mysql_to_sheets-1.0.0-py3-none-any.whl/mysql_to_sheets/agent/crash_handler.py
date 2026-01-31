"""Crash handler for Hybrid Agents.

Provides automatic crash reporting when the agent encounters unhandled
exceptions. Reports are sanitized to remove sensitive data before being
sent to the control plane.

Usage:
    from mysql_to_sheets.agent.crash_handler import setup_crash_handler

    setup_crash_handler(
        agent_id=self._agent_id,
        control_plane_url=self._control_plane_url,
        link_token=self._link_token,
    )

Security:
- Passwords, tokens, and API keys are sanitized from tracebacks
- Email addresses are removed
- Tracebacks are truncated to configurable max size (default 100KB)
"""

from __future__ import annotations

import logging
import re
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

import requests

logger = logging.getLogger(__name__)

# Patterns to sanitize from crash reports
SANITIZE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Passwords in various formats
    (re.compile(r"password\s*[=:]\s*['\"]?[^'\"\s,}]+", re.IGNORECASE), "password=***REDACTED***"),
    (re.compile(r"DB_PASSWORD\s*[=:]\s*[^\s]+", re.IGNORECASE), "DB_PASSWORD=***REDACTED***"),
    (re.compile(r"MYSQL_PASSWORD\s*[=:]\s*[^\s]+", re.IGNORECASE), "MYSQL_PASSWORD=***REDACTED***"),
    # Tokens and API keys
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]+", re.IGNORECASE), "Bearer ***REDACTED***"),
    (re.compile(r"api_key\s*[=:]\s*[^\s,}]+", re.IGNORECASE), "api_key=***REDACTED***"),
    (re.compile(r"LINK_TOKEN\s*[=:]\s*[^\s]+", re.IGNORECASE), "LINK_TOKEN=***REDACTED***"),
    (re.compile(r"SECRET_KEY\s*[=:]\s*[^\s]+", re.IGNORECASE), "SECRET_KEY=***REDACTED***"),
    (re.compile(r"token\s*[=:]\s*['\"]?eyJ[A-Za-z0-9\-_\.]+", re.IGNORECASE), "token=***REDACTED***"),
    # JWT tokens in strings
    (re.compile(r"eyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"), "***JWT_REDACTED***"),
    # Email addresses
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "***EMAIL_REDACTED***"),
    # Connection strings with passwords
    (re.compile(r"(mysql|postgres|postgresql)://[^:]+:[^@]+@"), r"\1://***:***@"),
]

# Default max size for traceback (100KB)
DEFAULT_MAX_TRACEBACK_SIZE = 100 * 1024


def sanitize_crash_report(
    text: str,
    max_size_kb: int = 100,
) -> str:
    """Sanitize a crash report by removing sensitive information.

    Args:
        text: Raw traceback or error message.
        max_size_kb: Maximum size in KB (truncates if exceeded).

    Returns:
        Sanitized text with sensitive data removed.
    """
    if not text:
        return text

    # Apply all sanitization patterns
    sanitized = text
    for pattern, replacement in SANITIZE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    # Truncate if too large
    max_bytes = max_size_kb * 1024
    if len(sanitized.encode("utf-8")) > max_bytes:
        # Truncate and add notice
        truncated = sanitized.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
        sanitized = truncated + "\n\n... [TRUNCATED - exceeded max size]"

    return sanitized


@dataclass
class CrashReporter:
    """Reports crashes to the control plane.

    Sends sanitized crash reports when unhandled exceptions occur.

    Attributes:
        agent_id: Unique identifier for this agent.
        control_plane_url: Base URL of the control plane API.
        link_token: Authentication token for control plane.
        version: Agent software version.
        max_traceback_kb: Max traceback size in KB.
        enabled: Whether crash reporting is enabled.
    """

    agent_id: str
    control_plane_url: str
    link_token: str
    version: str = "unknown"
    max_traceback_kb: int = 100
    enabled: bool = True
    _original_excepthook: Callable[..., Any] | None = field(default=None, init=False, repr=False)

    def report(
        self,
        exception_type: str,
        exception_message: str,
        tb: str | None = None,
        job_id: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Send a crash report to the control plane.

        Args:
            exception_type: Type of exception (e.g., "DatabaseError").
            exception_message: Exception message.
            tb: Full traceback (will be sanitized).
            job_id: Job being processed, if any.
            context: Additional context (config_id, sync_mode, etc.).

        Returns:
            True if report was sent successfully, False otherwise.
        """
        if not self.enabled:
            logger.debug("Crash reporting disabled, skipping report")
            return False

        # Sanitize the traceback
        sanitized_tb = sanitize_crash_report(tb or "", self.max_traceback_kb)
        sanitized_message = sanitize_crash_report(exception_message, 10)  # 10KB for message

        payload = {
            "agent_id": self.agent_id,
            "exception_type": exception_type,
            "exception_message": sanitized_message,
            "traceback": sanitized_tb,
            "job_id": job_id,
            "version": self.version,
            "context": context or {},
        }

        url = f"{self.control_plane_url.rstrip('/')}/api/agent/crash-report"
        headers = {
            "Authorization": f"Bearer {self.link_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                logger.info(f"Crash report sent successfully for {exception_type}")
                return True
            else:
                logger.warning(
                    f"Failed to send crash report: {response.status_code} - {response.text}"
                )
                return False
        except requests.RequestException as e:
            logger.warning(f"Failed to send crash report: {e}")
            return False

    def report_exception(
        self,
        exc: BaseException,
        job_id: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Report an exception to the control plane.

        Convenience method that extracts exception details and sends a report.

        Args:
            exc: Exception to report.
            job_id: Job being processed, if any.
            context: Additional context.

        Returns:
            True if report was sent successfully, False otherwise.
        """
        exc_type = type(exc).__name__
        exc_message = str(exc)
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        return self.report(
            exception_type=exc_type,
            exception_message=exc_message,
            tb=tb,
            job_id=job_id,
            context=context,
        )

    def install_excepthook(self) -> None:
        """Install as the global exception handler.

        Installs this reporter as sys.excepthook to catch unhandled
        exceptions. The original excepthook is preserved and called
        after reporting.
        """
        self._original_excepthook = sys.excepthook

        def crash_handler(
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_tb: Any,
        ) -> None:
            # Report the crash
            tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            self.report(
                exception_type=exc_type.__name__,
                exception_message=str(exc_value),
                tb=tb,
            )

            # Call original excepthook
            if self._original_excepthook:
                self._original_excepthook(exc_type, exc_value, exc_tb)

        sys.excepthook = crash_handler
        logger.debug("Installed crash handler as sys.excepthook")

    def uninstall_excepthook(self) -> None:
        """Restore the original exception handler."""
        if self._original_excepthook:
            sys.excepthook = self._original_excepthook
            self._original_excepthook = None
            logger.debug("Restored original sys.excepthook")


# Global crash reporter instance
_crash_reporter: CrashReporter | None = None


def setup_crash_handler(
    agent_id: str,
    control_plane_url: str,
    link_token: str,
    version: str = "unknown",
    max_traceback_kb: int = 100,
    install_excepthook: bool = True,
) -> CrashReporter:
    """Set up the global crash handler.

    Creates a CrashReporter and optionally installs it as the global
    exception handler.

    Args:
        agent_id: Unique identifier for this agent.
        control_plane_url: Base URL of the control plane API.
        link_token: Authentication token for control plane.
        version: Agent software version.
        max_traceback_kb: Max traceback size in KB.
        install_excepthook: Whether to install as sys.excepthook.

    Returns:
        CrashReporter instance.
    """
    global _crash_reporter

    _crash_reporter = CrashReporter(
        agent_id=agent_id,
        control_plane_url=control_plane_url,
        link_token=link_token,
        version=version,
        max_traceback_kb=max_traceback_kb,
    )

    if install_excepthook:
        _crash_reporter.install_excepthook()

    logger.info(f"Crash handler setup for agent {agent_id}")
    return _crash_reporter


def get_crash_reporter() -> CrashReporter | None:
    """Get the global crash reporter instance.

    Returns:
        CrashReporter if setup has been called, None otherwise.
    """
    return _crash_reporter


def teardown_crash_handler() -> None:
    """Tear down the global crash handler.

    Uninstalls the excepthook and clears the global instance.
    """
    global _crash_reporter

    if _crash_reporter:
        _crash_reporter.uninstall_excepthook()
        _crash_reporter = None
        logger.debug("Crash handler torn down")
