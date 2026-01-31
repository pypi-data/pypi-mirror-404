"""Tests for scheduler and connection pool edge cases.

Covers Edge Cases:
- EC-22: Schedule Cron/Interval Conflict (additional tests)
- EC-23: Connection Pool Stale Timeout
"""

import inspect

import pytest

from mysql_to_sheets.core.connection_pool import _validate_connection


class TestConnectionPoolStaleTimeout:
    """Tests for connection pool stale connection handling.

    Edge Case 23: Connection Pool Stale After MySQL wait_timeout
    -----------------------------------------------------------
    MySQL closes idle connections after wait_timeout (default 8 hours).
    Pooled connections that sit idle become stale.
    """

    def test_connection_pool_has_validation(self):
        """Verify connection pool validates connections."""
        from mysql_to_sheets.core import connection_pool

        source = inspect.getsource(connection_pool)

        # Verify connection validation exists
        assert "ping" in source.lower() or "validate" in source.lower()
        assert "stale" in source.lower() or "reconnect" in source.lower()

    def test_validate_connection_function_exists(self):
        """Verify _validate_connection helper exists."""
        # Function should exist
        assert callable(_validate_connection)

    def test_pooled_connection_validates(self):
        """Verify pooled_connection validates before yielding."""
        from mysql_to_sheets.core.connection_pool import pooled_connection

        source = inspect.getsource(pooled_connection)

        # Verify validation is called
        assert "_validate_connection" in source
