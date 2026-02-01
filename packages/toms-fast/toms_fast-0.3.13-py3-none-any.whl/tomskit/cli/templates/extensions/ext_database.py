"""
Database Extension Template for tomskit CLI

This template file contains the template for generating ext_database.py file.
"""

TEMPLATE = '''"""
Database extension initialization
"""

from typing import Any

from tomskit.sqlalchemy import db

from configs import app_settings


def is_enabled() -> bool:
    """Check if the extension is enabled."""
    return True


def init_app(app: Any = None):
    """
    Initialize database session pool from app settings.

    Args:
        app: FastAPI application instance

    Returns:
        None
    """
    db.create_session_pool_from_config(app_settings.database)
'''
