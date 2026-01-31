"""Centralized logging utilities for consistent logger creation.

This module provides helper functions for creating loggers with consistent
naming conventions across the codebase.
"""

import logging


def get_module_logger(module_name: str | None = None) -> logging.Logger:
    """Get a logger for the given module with consistent naming.

    If module_name is provided, it should be the module's __name__.
    The function strips the 'mysql_to_sheets.' prefix if present and
    ensures consistent naming.

    Args:
        module_name: The module's __name__, e.g. 'mysql_to_sheets.core.sync'.
                     If None, returns the root 'mysql_to_sheets' logger.

    Returns:
        A configured Logger instance.

    Example:
        >>> from mysql_to_sheets.core.logging_utils import get_module_logger
        >>> logger = get_module_logger(__name__)
    """
    if module_name is None:
        return logging.getLogger("mysql_to_sheets")

    # Ensure consistent base prefix
    if not module_name.startswith("mysql_to_sheets"):
        logger_name = f"mysql_to_sheets.{module_name}"
    else:
        logger_name = module_name

    return logging.getLogger(logger_name)
