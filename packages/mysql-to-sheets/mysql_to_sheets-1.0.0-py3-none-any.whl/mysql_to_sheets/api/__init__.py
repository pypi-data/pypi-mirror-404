"""REST API layer for MySQL to Google Sheets sync."""

from mysql_to_sheets.api.app import app, create_app

__all__ = ["create_app", "app"]
