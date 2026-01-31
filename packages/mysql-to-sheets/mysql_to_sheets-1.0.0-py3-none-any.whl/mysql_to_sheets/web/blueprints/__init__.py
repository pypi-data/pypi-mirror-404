"""Flask blueprints for web dashboard routes.

This package contains modular route handlers organized by domain:
- auth: Login, logout, registration
- dashboard: Main pages (index, setup, schedules)
- api/: JSON API endpoints for AJAX operations
"""

from mysql_to_sheets.web.blueprints.auth import auth_bp
from mysql_to_sheets.web.blueprints.dashboard import dashboard_bp

__all__ = ["auth_bp", "dashboard_bp"]
