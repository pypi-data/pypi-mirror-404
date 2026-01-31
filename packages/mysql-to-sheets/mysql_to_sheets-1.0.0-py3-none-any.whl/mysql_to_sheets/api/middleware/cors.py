"""CORS middleware re-export.

The actual CORSMiddleware is imported from fastapi/starlette.
This module exists for consistency with the middleware package structure.
"""

from starlette.middleware.cors import CORSMiddleware

__all__ = ["CORSMiddleware"]
