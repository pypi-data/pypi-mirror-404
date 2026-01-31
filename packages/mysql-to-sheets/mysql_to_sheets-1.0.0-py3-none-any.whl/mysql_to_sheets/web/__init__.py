"""Web dashboard for MySQL to Google Sheets sync."""

from mysql_to_sheets.web.app import app, create_app

__all__ = ["create_app", "app"]
