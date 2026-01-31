"""Structured logging configuration with JSON support and request ID tracing.

This module provides configurable logging that supports both traditional
text format and structured JSON format for log aggregation systems.
"""

import json
import logging
import re
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Context variables for request/correlation tracing
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
organization_id_var: ContextVar[int | None] = ContextVar("organization_id", default=None)
config_id_var: ContextVar[int | None] = ContextVar("config_id", default=None)


def get_request_id() -> str | None:
    """Get the current request ID from context.

    Returns:
        The current request ID, or None if not set.
    """
    return request_id_var.get()


def set_request_id(request_id: str | None = None) -> str:
    """Set the request ID in context.

    Args:
        request_id: The request ID to set. If None, generates a new UUID.

    Returns:
        The request ID that was set.
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def clear_request_id() -> None:
    """Clear the request ID from context."""
    request_id_var.set(None)


def get_organization_id() -> int | None:
    """Get the current organization ID from context.

    Returns:
        The current organization ID, or None if not set.
    """
    return organization_id_var.get()


def set_organization_id(org_id: int | None) -> None:
    """Set the organization ID in context.

    Args:
        org_id: The organization ID to set, or None to clear.
    """
    organization_id_var.set(org_id)


def get_config_id() -> int | None:
    """Get the current config ID from context.

    Returns:
        The current config ID, or None if not set.
    """
    return config_id_var.get()


def set_config_id(config_id: int | None) -> None:
    """Set the config ID in context.

    Args:
        config_id: The config ID to set, or None to clear.
    """
    config_id_var.set(config_id)


def clear_correlation_context() -> None:
    """Clear all correlation context variables."""
    request_id_var.set(None)
    organization_id_var.set(None)
    config_id_var.set(None)


class PIIMaskingFilter(logging.Filter):
    """Filter to mask PII patterns in log messages.

    This filter redacts sensitive information like email addresses,
    IP addresses, and password values from log messages to prevent
    accidental PII exposure in logs.

    Enable by setting LOG_PII_MASKING=true in environment.

    Example:
        >>> filter = PIIMaskingFilter()
        >>> # Will mask: "User email: test@example.com" -> "User email: [EMAIL]"
        >>> # Will mask: "IP: 192.168.1.1" -> "IP: [IP]"
        >>> # Will mask: "password='secret'" -> "password=[REDACTED]"
    """

    # Compiled regex patterns for PII detection
    PATTERNS: list[tuple[re.Pattern[str], str]] = [
        # Email addresses
        (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "[EMAIL]"),
        # IPv4 addresses
        (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[IP]"),
        # Password values (various formats)
        (
            re.compile(r'password["\']?\s*[:=]\s*["\']?[^\s"\']+', re.IGNORECASE),
            "password=[REDACTED]",
        ),
        # API keys and tokens (common patterns)
        (
            re.compile(r'(api[_-]?key|token|secret)["\']?\s*[:=]\s*["\']?[^\s"\']+', re.IGNORECASE),
            r"\1=[REDACTED]",
        ),
    ]

    def __init__(self, name: str = "") -> None:
        """Initialize PII masking filter.

        Args:
            name: Filter name (passed to parent).
        """
        super().__init__(name)

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log record, masking PII in the message.

        Args:
            record: The log record to filter.

        Returns:
            True (always allows the record through after masking).
        """
        # Mask PII in the message
        if record.msg:
            record.msg = self._mask_pii(str(record.msg))

        # Mask PII in args if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._mask_pii(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._mask_pii(str(arg)) if isinstance(arg, str) else arg for arg in record.args
                )

        return True

    def _mask_pii(self, text: str) -> str:
        """Mask PII patterns in text.

        Args:
            text: The text to mask.

        Returns:
            Text with PII patterns replaced.
        """
        for pattern, replacement in self.PATTERNS:
            text = pattern.sub(replacement, text)
        return text


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging.

    Outputs logs in JSON format suitable for log aggregation systems
    like ELK Stack, Splunk, or cloud logging services.
    """

    def __init__(
        self,
        include_request_id: bool = True,
        include_extras: bool = True,
    ) -> None:
        """Initialize JSON formatter.

        Args:
            include_request_id: Whether to include request ID in logs.
            include_extras: Whether to include extra fields from log records.
        """
        super().__init__()
        self.include_request_id = include_request_id
        self.include_extras = include_extras

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add location info
        if record.pathname:
            log_data["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add correlation IDs if available
        if self.include_request_id:
            request_id = get_request_id()
            if request_id:
                log_data["request_id"] = request_id

            # Include organization and config context
            org_id = get_organization_id()
            if org_id is not None:
                log_data["organization_id"] = org_id

            cfg_id = get_config_id()
            if cfg_id is not None:
                log_data["config_id"] = cfg_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from the log record
        if self.include_extras:
            # Standard log record attributes to exclude
            exclude_keys = {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "taskName",
            }
            for key, value in record.__dict__.items():
                if key not in exclude_keys and not key.startswith("_"):
                    try:
                        json.dumps(value)  # Check if serializable
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Enhanced text formatter with optional request ID.

    Extends the standard formatter to include request ID tracing.
    """

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        include_request_id: bool = True,
    ) -> None:
        """Initialize text formatter.

        Args:
            fmt: Log format string.
            datefmt: Date format string.
            include_request_id: Whether to include request ID.
        """
        if fmt is None:
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        super().__init__(fmt, datefmt)
        self.include_request_id = include_request_id

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional request ID.

        Args:
            record: The log record to format.

        Returns:
            Formatted log string.
        """
        if self.include_request_id:
            request_id = get_request_id()
            if request_id:
                record.msg = f"[{request_id[:8]}] {record.msg}"

        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: str | None = None,
    log_format: str = "text",
    logger_name: str = "mysql_to_sheets",
    pii_masking: bool = False,
    max_bytes: int = 10_485_760,
    backup_count: int = 5,
) -> logging.Logger:
    """Configure logging with file and console handlers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file.
        log_format: Log format ('text' or 'json').
        logger_name: Name of the logger to configure.
        max_bytes: Maximum log file size before rotation (default 10MB).
        backup_count: Number of rotated log files to keep (default 5).
        pii_masking: Whether to enable PII masking filter.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(logger_name)
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Clear existing handlers and filters
    logger.handlers.clear()
    logger.filters.clear()

    # Add PII masking filter if enabled
    if pii_masking:
        logger.addFilter(PIIMaskingFilter())

    # Create formatters based on format type
    if log_format == "json":
        console_formatter: logging.Formatter = JSONFormatter()
        file_formatter: logging.Formatter = JSONFormatter()
    else:
        console_formatter = TextFormatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
        file_formatter = TextFormatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if path provided)
    if log_file:
        log_path = Path(log_file)
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Fall back to platform directory if current location is not writable
            from mysql_to_sheets.core.paths import get_default_log_path

            log_path = get_default_log_path()
            log_path.parent.mkdir(parents=True, exist_ok=True)
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setLevel(logging.DEBUG)  # Always capture debug to file
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


class LogContext:
    """Context manager for adding structured data to logs.

    Use this to add extra fields to all logs within a context.

    Example:
        with LogContext(user_id="123", operation="sync"):
            logger.info("Starting operation")  # Will include user_id and operation
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize log context with extra fields.

        Args:
            **kwargs: Extra fields to add to all logs in this context.
        """
        self.extras = kwargs
        self._old_factory: Any = None

    def __enter__(self) -> "LogContext":
        """Enter context and modify log record factory."""
        old_factory = logging.getLogRecordFactory()
        self._old_factory = old_factory
        extras = self.extras

        def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = old_factory(*args, **kwargs)
            for key, value in extras.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: object,
    ) -> None:
        """Exit context and restore original log record factory."""
        if self._old_factory is not None:
            logging.setLogRecordFactory(self._old_factory)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **kwargs: Any,
) -> None:
    """Log a message with extra context fields.

    Args:
        logger: Logger instance.
        level: Log level (logging.INFO, etc.).
        message: Log message.
        **kwargs: Extra fields to include in the log.
    """
    logger.log(level, message, extra=kwargs)
