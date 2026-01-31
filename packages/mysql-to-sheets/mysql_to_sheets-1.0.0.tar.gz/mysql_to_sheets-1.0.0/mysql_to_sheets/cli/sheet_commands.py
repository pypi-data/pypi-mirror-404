"""CLI commands for Google Sheets worksheet management.

Contains: sheet create, sheet list, sheet delete commands.
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

import gspread

from mysql_to_sheets.cli.utils import output_result

if TYPE_CHECKING:
    import gspread.spreadsheet


from mysql_to_sheets.core.config import get_config, reset_config
from mysql_to_sheets.core.exceptions import ConfigError, SheetsError
from mysql_to_sheets.core.sheets_utils import (
    create_worksheet,
    delete_worksheet,
    list_worksheets,
    parse_sheet_id,
)


def add_sheet_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add sheet management command parsers.

    Args:
        subparsers: Parent subparsers to add commands to.
    """
    sheet_parser = subparsers.add_parser(
        "sheet",
        help="Manage Google Sheets worksheets",
    )
    sheet_subparsers = sheet_parser.add_subparsers(dest="sheet_command")

    # sheet create
    create_parser = sheet_subparsers.add_parser(
        "create",
        help="Create a new worksheet in the spreadsheet",
    )
    create_parser.add_argument(
        "--name",
        required=True,
        help="Name for the new worksheet",
    )
    create_parser.add_argument(
        "--rows",
        type=int,
        default=None,
        help="Number of rows (default: from config or 1000)",
    )
    create_parser.add_argument(
        "--cols",
        type=int,
        default=None,
        help="Number of columns (default: from config or 26)",
    )
    create_parser.add_argument(
        "--sheet-id",
        dest="sheet_id",
        help="Google Sheet ID or URL (default: from .env)",
    )
    create_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # sheet list
    list_parser = sheet_subparsers.add_parser(
        "list",
        help="List all worksheets in the spreadsheet",
    )
    list_parser.add_argument(
        "--sheet-id",
        dest="sheet_id",
        help="Google Sheet ID or URL (default: from .env)",
    )
    list_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # sheet delete
    delete_parser = sheet_subparsers.add_parser(
        "delete",
        help="Delete a worksheet from the spreadsheet",
    )
    delete_parser.add_argument(
        "--name",
        required=True,
        help="Name of the worksheet to delete",
    )
    delete_parser.add_argument(
        "--sheet-id",
        dest="sheet_id",
        help="Google Sheet ID or URL (default: from .env)",
    )
    delete_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )
    delete_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # sheet cleanup-staging
    cleanup_parser = sheet_subparsers.add_parser(
        "cleanup-staging",
        help="Clean up stale staging worksheets from interrupted atomic syncs",
    )
    cleanup_parser.add_argument(
        "--max-age",
        type=int,
        default=60,
        dest="max_age",
        help="Maximum age in minutes for staging sheets (default: 60)",
    )
    cleanup_parser.add_argument(
        "--prefix",
        default="_staging_",
        help="Staging worksheet name prefix (default: _staging_)",
    )
    cleanup_parser.add_argument(
        "--sheet-id",
        dest="sheet_id",
        help="Google Sheet ID or URL (default: from .env)",
    )
    cleanup_parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def _get_spreadsheet(
    config_sheet_id: str | None,
    cli_sheet_id: str | None,
    service_account_file: str,
) -> tuple["gspread.spreadsheet.Spreadsheet", str]:
    """Get a spreadsheet connection.

    Args:
        config_sheet_id: Sheet ID from config.
        cli_sheet_id: Sheet ID from CLI argument.
        service_account_file: Path to service account JSON.

    Returns:
        Tuple of (spreadsheet object, sheet_id used).

    Raises:
        ConfigError: If no sheet ID is provided.
        SheetsError: If connection fails.
    """
    # Determine which sheet ID to use
    if cli_sheet_id:
        try:
            sheet_id = parse_sheet_id(cli_sheet_id)
        except ValueError as e:
            raise ConfigError(str(e))
    elif config_sheet_id:
        sheet_id = config_sheet_id
    else:
        raise ConfigError(
            "No Google Sheet ID provided. Use --sheet-id or set GOOGLE_SHEET_ID in .env"
        )

    try:
        gc = gspread.service_account(filename=service_account_file)  # type: ignore[attr-defined]
        spreadsheet = gc.open_by_key(sheet_id)
        return spreadsheet, sheet_id
    except gspread.exceptions.SpreadsheetNotFound as e:
        raise SheetsError(
            message=f"Spreadsheet not found: {sheet_id}",
            sheet_id=sheet_id,
            original_error=e,
        ) from e
    except Exception as e:
        raise SheetsError(
            message=f"Failed to connect to Google Sheets: {e}",
            sheet_id=sheet_id,
            original_error=e,
        ) from e


def cmd_sheet_create(args: argparse.Namespace) -> int:
    """Execute sheet create command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    reset_config()
    config = get_config()

    try:
        spreadsheet, sheet_id = _get_spreadsheet(
            config.google_sheet_id,
            getattr(args, "sheet_id", None),
            config.service_account_file,
        )

        # Determine row/col counts
        rows = args.rows if args.rows is not None else config.worksheet_default_rows
        cols = args.cols if args.cols is not None else config.worksheet_default_cols

        worksheet = create_worksheet(
            spreadsheet,
            args.name,
            rows=rows,
            cols=cols,
        )

        output_result(
            {
                "success": True,
                "message": f"Worksheet '{args.name}' created successfully",
                "worksheet": {
                    "title": worksheet.title,
                    "gid": worksheet.id,
                    "rows": worksheet.row_count,
                    "cols": worksheet.col_count,
                },
                "sheet_id": sheet_id,
            },
            args.output,
        )
        return 0

    except (ConfigError, SheetsError) as e:
        output_result(
            {
                "success": False,
                "message": e.message,
                "error": e.message,
                "code": getattr(e, "code", None),
            },
            args.output,
        )
        return 1


def cmd_sheet_list(args: argparse.Namespace) -> int:
    """Execute sheet list command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    reset_config()
    config = get_config()

    try:
        spreadsheet, sheet_id = _get_spreadsheet(
            config.google_sheet_id,
            getattr(args, "sheet_id", None),
            config.service_account_file,
        )

        worksheets = list_worksheets(spreadsheet)

        output_result(
            {
                "success": True,
                "message": f"Found {len(worksheets)} worksheet(s)",
                "spreadsheet_title": spreadsheet.title,
                "sheet_id": sheet_id,
                "worksheets": worksheets,
            },
            args.output,
        )
        return 0

    except (ConfigError, SheetsError) as e:
        output_result(
            {
                "success": False,
                "message": e.message,
                "error": e.message,
                "code": getattr(e, "code", None),
            },
            args.output,
        )
        return 1


def cmd_sheet_delete(args: argparse.Namespace) -> int:
    """Execute sheet delete command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    reset_config()
    config = get_config()

    # Confirmation prompt if not forced
    if not args.force and args.output == "text":
        confirm = input(
            f"Are you sure you want to delete worksheet '{args.name}'? "
            "This cannot be undone. [y/N]: "
        )
        if confirm.lower() not in ("y", "yes"):
            print("Deletion cancelled.")
            return 0

    try:
        spreadsheet, sheet_id = _get_spreadsheet(
            config.google_sheet_id,
            getattr(args, "sheet_id", None),
            config.service_account_file,
        )

        delete_worksheet(spreadsheet, args.name)

        output_result(
            {
                "success": True,
                "message": f"Worksheet '{args.name}' deleted successfully",
                "sheet_id": sheet_id,
            },
            args.output,
        )
        return 0

    except (ConfigError, SheetsError) as e:
        output_result(
            {
                "success": False,
                "message": e.message,
                "error": e.message,
                "code": getattr(e, "code", None),
            },
            args.output,
        )
        return 1


def cmd_sheet_cleanup_staging(args: argparse.Namespace) -> int:
    """Execute sheet cleanup-staging command.

    Cleans up stale staging worksheets left behind by interrupted atomic syncs.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    reset_config()
    config = get_config()

    try:
        spreadsheet, sheet_id = _get_spreadsheet(
            config.google_sheet_id,
            getattr(args, "sheet_id", None),
            config.service_account_file,
        )

        from mysql_to_sheets.core.atomic_streaming import cleanup_stale_staging_sheets

        cleaned_count = cleanup_stale_staging_sheets(
            spreadsheet,
            max_age_minutes=args.max_age,
            staging_prefix=args.prefix,
        )

        output_result(
            {
                "success": True,
                "message": f"Cleaned up {cleaned_count} stale staging worksheet(s)",
                "cleaned_count": cleaned_count,
                "max_age_minutes": args.max_age,
                "prefix": args.prefix,
                "sheet_id": sheet_id,
            },
            args.output,
        )
        return 0

    except (ConfigError, SheetsError) as e:
        output_result(
            {
                "success": False,
                "message": e.message,
                "error": e.message,
                "code": getattr(e, "code", None),
            },
            args.output,
        )
        return 1


def handle_sheet_command(args: argparse.Namespace) -> int:
    """Route sheet subcommands to handlers.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    if not args.sheet_command:
        print("Usage: mysql-to-sheets sheet <create|list|delete|cleanup-staging> [options]")
        print("\nCommands:")
        print("  create          Create a new worksheet")
        print("  list            List all worksheets")
        print("  delete          Delete a worksheet")
        print("  cleanup-staging Clean up stale staging worksheets")
        print("\nRun 'mysql-to-sheets sheet <command> --help' for command options.")
        return 0

    handlers = {
        "create": cmd_sheet_create,
        "list": cmd_sheet_list,
        "delete": cmd_sheet_delete,
        "cleanup-staging": cmd_sheet_cleanup_staging,
    }

    handler = handlers.get(args.sheet_command)
    if handler:
        return handler(args)

    print(f"Unknown sheet command: {args.sheet_command}")
    return 1
