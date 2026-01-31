"""Pagination utilities for Flask blueprints.

EC-57: Provides bounded pagination to prevent OOM from unbounded limit parameters.
"""

from flask import Request


def get_bounded_pagination(
    request: Request,
    default_page: int = 1,
    default_per_page: int = 25,
    max_per_page: int = 100,
) -> tuple[int, int, int]:
    """Get bounded pagination parameters from request.

    EC-57: Pagination limit bounding to prevent OOM from unbounded values
    like ?per_page=999999999.

    Args:
        request: Flask request object.
        default_page: Default page number if not specified.
        default_per_page: Default items per page if not specified.
        max_per_page: Maximum allowed items per page.

    Returns:
        Tuple of (page, per_page, offset) where:
        - page: 1-indexed page number (minimum 1)
        - per_page: Items per page (bounded between 1 and max_per_page)
        - offset: Database offset for LIMIT/OFFSET queries
    """
    # Get page, ensure minimum of 1
    page = max(1, request.args.get("page", default_page, type=int))

    # Get per_page from either per_page or limit parameter
    per_page = request.args.get("per_page", default_per_page, type=int)
    if "limit" in request.args:
        per_page = request.args.get("limit", default_per_page, type=int)

    # Bound per_page between 1 and max_per_page
    per_page = min(max(1, per_page), max_per_page)

    # Calculate offset for database queries
    offset = (page - 1) * per_page

    return page, per_page, offset
