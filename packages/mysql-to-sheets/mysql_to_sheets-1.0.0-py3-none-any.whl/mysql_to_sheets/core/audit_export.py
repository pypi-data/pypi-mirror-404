"""Audit log export service.

Provides export functionality for audit logs in multiple formats:
- CSV: Standard comma-separated values
- JSON: JSON array of objects
- JSONL: JSON Lines (one JSON object per line)
- CEF: Common Event Format for SIEM integration

All exports stream results to avoid memory issues with large datasets.
"""

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TextIO

from mysql_to_sheets.models.audit_logs import AuditLog, get_audit_log_repository


@dataclass
class ExportOptions:
    """Options for audit log export.

    Attributes:
        from_date: Export logs after this timestamp.
        to_date: Export logs before this timestamp.
        action: Filter by action type.
        user_id: Filter by user ID.
        resource_type: Filter by resource type.
        include_metadata: Whether to include metadata field.
    """

    from_date: datetime | None = None
    to_date: datetime | None = None
    action: str | None = None
    user_id: int | None = None
    resource_type: str | None = None
    include_metadata: bool = True


@dataclass
class ExportResult:
    """Result of an export operation.

    Attributes:
        record_count: Number of records exported.
        format: Export format used.
        from_date: Start date filter (if any).
        to_date: End date filter (if any).
    """

    record_count: int
    format: str
    from_date: datetime | None = None
    to_date: datetime | None = None


def _log_to_row(log: AuditLog, include_metadata: bool = True) -> dict[str, Any]:
    """Convert AuditLog to exportable row.

    Args:
        log: AuditLog instance.
        include_metadata: Whether to include metadata field.

    Returns:
        Dictionary with export fields.
    """
    row = {
        "id": log.id,
        "timestamp": log.timestamp.isoformat() if log.timestamp else "",
        "user_id": log.user_id,
        "organization_id": log.organization_id,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id or "",
        "source_ip": log.source_ip or "",
        "user_agent": log.user_agent or "",
        "query_executed": log.query_executed or "",
        "rows_affected": log.rows_affected if log.rows_affected is not None else "",
    }
    if include_metadata:
        row["metadata"] = json.dumps(log.metadata) if log.metadata else ""
    return row


# CSV column order
CSV_COLUMNS = [
    "id",
    "timestamp",
    "user_id",
    "organization_id",
    "action",
    "resource_type",
    "resource_id",
    "source_ip",
    "user_agent",
    "query_executed",
    "rows_affected",
    "metadata",
]


def export_to_csv(
    organization_id: int,
    output: TextIO,
    db_path: str,
    options: ExportOptions | None = None,
) -> ExportResult:
    """Export audit logs to CSV format.

    Args:
        organization_id: Organization to export.
        output: File-like object to write to.
        db_path: Path to audit log database.
        options: Export filter options.

    Returns:
        ExportResult with record count.
    """
    options = options or ExportOptions()
    repo = get_audit_log_repository(db_path)

    columns = CSV_COLUMNS if options.include_metadata else CSV_COLUMNS[:-1]
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()

    record_count = 0
    for batch in repo.stream_logs(
        organization_id=organization_id,
        from_date=options.from_date,
        to_date=options.to_date,
        action=options.action,
        user_id=options.user_id,
    ):
        for log in batch:
            if options.resource_type and log.resource_type != options.resource_type:
                continue
            row = _log_to_row(log, options.include_metadata)
            writer.writerow(row)
            record_count += 1

    return ExportResult(
        record_count=record_count,
        format="csv",
        from_date=options.from_date,
        to_date=options.to_date,
    )


def export_to_json(
    organization_id: int,
    output: TextIO,
    db_path: str,
    options: ExportOptions | None = None,
    pretty: bool = False,
) -> ExportResult:
    """Export audit logs to JSON format.

    Exports as a JSON array of objects.

    Args:
        organization_id: Organization to export.
        output: File-like object to write to.
        db_path: Path to audit log database.
        options: Export filter options.
        pretty: Whether to pretty-print JSON.

    Returns:
        ExportResult with record count.
    """
    options = options or ExportOptions()
    repo = get_audit_log_repository(db_path)

    records = []
    record_count = 0

    for batch in repo.stream_logs(
        organization_id=organization_id,
        from_date=options.from_date,
        to_date=options.to_date,
        action=options.action,
        user_id=options.user_id,
    ):
        for log in batch:
            if options.resource_type and log.resource_type != options.resource_type:
                continue
            record = log.to_dict()
            if not options.include_metadata:
                record.pop("metadata", None)
            records.append(record)
            record_count += 1

    indent = 2 if pretty else None
    json.dump(records, output, indent=indent, default=str)

    return ExportResult(
        record_count=record_count,
        format="json",
        from_date=options.from_date,
        to_date=options.to_date,
    )


def export_to_jsonl(
    organization_id: int,
    output: TextIO,
    db_path: str,
    options: ExportOptions | None = None,
) -> ExportResult:
    """Export audit logs to JSON Lines format.

    Each line is a complete JSON object. This format is SIEM-friendly
    and supports streaming without loading all records into memory.

    Args:
        organization_id: Organization to export.
        output: File-like object to write to.
        db_path: Path to audit log database.
        options: Export filter options.

    Returns:
        ExportResult with record count.
    """
    options = options or ExportOptions()
    repo = get_audit_log_repository(db_path)

    record_count = 0
    for batch in repo.stream_logs(
        organization_id=organization_id,
        from_date=options.from_date,
        to_date=options.to_date,
        action=options.action,
        user_id=options.user_id,
    ):
        for log in batch:
            if options.resource_type and log.resource_type != options.resource_type:
                continue
            record = log.to_dict()
            if not options.include_metadata:
                record.pop("metadata", None)
            output.write(json.dumps(record, default=str))
            output.write("\n")
            record_count += 1

    return ExportResult(
        record_count=record_count,
        format="jsonl",
        from_date=options.from_date,
        to_date=options.to_date,
    )


def _escape_cef_value(value: str) -> str:
    """Escape special characters for CEF format.

    Args:
        value: String value to escape.

    Returns:
        Escaped string.
    """
    if not value:
        return ""
    # Escape backslash first, then pipe and equals
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace("|", "\\|")
    escaped = escaped.replace("=", "\\=")
    return escaped


def _log_to_cef(
    log: AuditLog, vendor: str = "MySQLToSheets", product: str = "SyncTool", version: str = "1.0"
) -> str:
    """Convert AuditLog to CEF format.

    CEF format:
    CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension

    Args:
        log: AuditLog instance.
        vendor: Device vendor name.
        product: Device product name.
        version: Device version.

    Returns:
        CEF formatted string.
    """
    # Map actions to severity (0-10)
    severity_map = {
        "auth.login_failed": 7,
        "auth.password_changed": 5,
        "sync.failed": 6,
        "user.deleted": 4,
        "org.deleted": 4,
    }
    severity = severity_map.get(log.action, 3)

    # Build extension fields
    extensions = []

    if log.timestamp:
        # CEF uses epoch milliseconds for time
        epoch_ms = int(log.timestamp.timestamp() * 1000)
        extensions.append(f"rt={epoch_ms}")

    if log.user_id:
        extensions.append(f"suid={log.user_id}")

    if log.source_ip:
        extensions.append(f"src={_escape_cef_value(log.source_ip)}")

    if log.resource_type:
        extensions.append(f"cs1={_escape_cef_value(log.resource_type)}")
        extensions.append("cs1Label=ResourceType")

    if log.resource_id:
        extensions.append(f"cs2={_escape_cef_value(log.resource_id)}")
        extensions.append("cs2Label=ResourceID")

    if log.rows_affected is not None:
        extensions.append(f"cn1={log.rows_affected}")
        extensions.append("cn1Label=RowsAffected")

    if log.organization_id:
        extensions.append(f"cs3={log.organization_id}")
        extensions.append("cs3Label=OrganizationID")

    extension_str = " ".join(extensions)

    # Build CEF line
    signature_id = log.action.replace(".", "_")
    name = log.action

    return f"CEF:0|{vendor}|{product}|{version}|{signature_id}|{name}|{severity}|{extension_str}"


def export_to_cef(
    organization_id: int,
    output: TextIO,
    db_path: str,
    options: ExportOptions | None = None,
    vendor: str = "MySQLToSheets",
    product: str = "SyncTool",
    version: str = "1.0",
) -> ExportResult:
    """Export audit logs to Common Event Format (CEF).

    CEF is a standard format for SIEM integration (ArcSight, Splunk, etc.).

    Args:
        organization_id: Organization to export.
        output: File-like object to write to.
        db_path: Path to audit log database.
        options: Export filter options.
        vendor: Device vendor name for CEF header.
        product: Device product name for CEF header.
        version: Device version for CEF header.

    Returns:
        ExportResult with record count.
    """
    options = options or ExportOptions()
    repo = get_audit_log_repository(db_path)

    record_count = 0
    for batch in repo.stream_logs(
        organization_id=organization_id,
        from_date=options.from_date,
        to_date=options.to_date,
        action=options.action,
        user_id=options.user_id,
    ):
        for log in batch:
            if options.resource_type and log.resource_type != options.resource_type:
                continue
            cef_line = _log_to_cef(log, vendor, product, version)
            output.write(cef_line)
            output.write("\n")
            record_count += 1

    return ExportResult(
        record_count=record_count,
        format="cef",
        from_date=options.from_date,
        to_date=options.to_date,
    )


def export_audit_logs(
    organization_id: int,
    output: TextIO,
    db_path: str,
    format: str = "csv",
    options: ExportOptions | None = None,
    **kwargs: Any,
) -> ExportResult:
    """Export audit logs to the specified format.

    Args:
        organization_id: Organization to export.
        output: File-like object to write to.
        db_path: Path to audit log database.
        format: Export format (csv, json, jsonl, cef).
        options: Export filter options.
        **kwargs: Format-specific options.

    Returns:
        ExportResult with record count.

    Raises:
        ValueError: If format is not supported.
    """
    format = format.lower()

    if format == "csv":
        return export_to_csv(organization_id, output, db_path, options)
    elif format == "json":
        return export_to_json(organization_id, output, db_path, options, **kwargs)
    elif format == "jsonl":
        return export_to_jsonl(organization_id, output, db_path, options)
    elif format == "cef":
        return export_to_cef(organization_id, output, db_path, options, **kwargs)
    else:
        raise ValueError(f"Unsupported export format: {format}. Use csv, json, jsonl, or cef.")


def get_supported_formats() -> list[str]:
    """Get list of supported export formats.

    Returns:
        List of format names.
    """
    return ["csv", "json", "jsonl", "cef"]
