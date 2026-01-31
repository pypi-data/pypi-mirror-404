"""Tests for core/audit_export.py — audit log export in multiple formats."""

import io
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.audit_export import (
    _escape_cef_value,
    _log_to_cef,
    _log_to_row,
    export_audit_logs,
    get_supported_formats,
)


def _make_audit_log(**overrides):
    """Create a mock AuditLog with sensible defaults."""
    log = MagicMock()
    log.id = overrides.get("id", 1)
    log.timestamp = overrides.get("timestamp", datetime(2024, 6, 15, 12, 0, 0))
    log.user_id = overrides.get("user_id", 42)
    log.organization_id = overrides.get("organization_id", 1)
    log.action = overrides.get("action", "sync.completed")
    log.resource_type = overrides.get("resource_type", "config")
    log.resource_id = overrides.get("resource_id", "5")
    log.source_ip = overrides.get("source_ip", "10.0.0.1")
    log.user_agent = overrides.get("user_agent", "test-agent")
    log.query_executed = overrides.get("query_executed", "SELECT 1")
    log.rows_affected = overrides.get("rows_affected", 10)
    log.metadata = overrides.get("metadata", {"key": "val"})
    log.to_dict.return_value = {
        "id": log.id,
        "action": log.action,
        "resource_type": log.resource_type,
        "metadata": log.metadata,
    }
    return log


class TestLogToRow:
    def test_includes_metadata_by_default(self):
        log = _make_audit_log()
        row = _log_to_row(log)
        assert "metadata" in row
        assert row["id"] == 1

    def test_excludes_metadata(self):
        log = _make_audit_log()
        row = _log_to_row(log, include_metadata=False)
        assert "metadata" not in row

    def test_handles_none_timestamp(self):
        log = _make_audit_log(timestamp=None)
        row = _log_to_row(log)
        assert row["timestamp"] == ""


class TestEscapeCefValue:
    def test_empty(self):
        assert _escape_cef_value("") == ""

    def test_escapes_pipe(self):
        assert _escape_cef_value("a|b") == "a\\|b"

    def test_escapes_equals(self):
        assert _escape_cef_value("a=b") == "a\\=b"

    def test_escapes_backslash(self):
        assert _escape_cef_value("a\\b") == "a\\\\b"


class TestLogToCef:
    def test_basic_format(self):
        log = _make_audit_log()
        cef = _log_to_cef(log)
        assert cef.startswith("CEF:0|MySQLToSheets|SyncTool|1.0|")
        assert "sync_completed" in cef  # signature_id

    def test_severity_mapping(self):
        log = _make_audit_log(action="auth.login_failed")
        cef = _log_to_cef(log)
        # severity 7 for login_failed
        parts = cef.split("|")
        assert parts[6] == "7"


class TestExportAuditLogs:
    @patch("mysql_to_sheets.core.audit_export.get_audit_log_repository")
    def test_csv_export(self, mock_repo_fn):
        mock_repo = MagicMock()
        mock_repo.stream_logs.return_value = [[_make_audit_log()]]
        mock_repo_fn.return_value = mock_repo

        output = io.StringIO()
        result = export_audit_logs(1, output, "/tmp/db", format="csv")
        assert result.format == "csv"
        assert result.record_count == 1
        assert "id" in output.getvalue()

    @patch("mysql_to_sheets.core.audit_export.get_audit_log_repository")
    def test_json_export(self, mock_repo_fn):
        mock_repo = MagicMock()
        mock_repo.stream_logs.return_value = [[_make_audit_log()]]
        mock_repo_fn.return_value = mock_repo

        output = io.StringIO()
        result = export_audit_logs(1, output, "/tmp/db", format="json")
        assert result.format == "json"
        parsed = json.loads(output.getvalue())
        assert len(parsed) == 1

    @patch("mysql_to_sheets.core.audit_export.get_audit_log_repository")
    def test_jsonl_export(self, mock_repo_fn):
        mock_repo = MagicMock()
        mock_repo.stream_logs.return_value = [[_make_audit_log(), _make_audit_log(id=2)]]
        mock_repo_fn.return_value = mock_repo

        output = io.StringIO()
        result = export_audit_logs(1, output, "/tmp/db", format="jsonl")
        assert result.format == "jsonl"
        assert result.record_count == 2
        lines = output.getvalue().strip().split("\n")
        assert len(lines) == 2

    @patch("mysql_to_sheets.core.audit_export.get_audit_log_repository")
    def test_cef_export(self, mock_repo_fn):
        mock_repo = MagicMock()
        mock_repo.stream_logs.return_value = [[_make_audit_log()]]
        mock_repo_fn.return_value = mock_repo

        output = io.StringIO()
        result = export_audit_logs(1, output, "/tmp/db", format="cef")
        assert result.format == "cef"
        assert "CEF:0" in output.getvalue()

    def test_unsupported_format(self):
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_audit_logs(1, io.StringIO(), "/tmp/db", format="xml")


class TestGetSupportedFormats:
    def test_all_formats(self):
        fmts = get_supported_formats()
        assert set(fmts) == {"csv", "json", "jsonl", "cef"}
