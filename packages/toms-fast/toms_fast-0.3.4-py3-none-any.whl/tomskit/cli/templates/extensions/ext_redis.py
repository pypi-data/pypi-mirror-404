"""
Redis Extension Template for tomskit CLI

This template file contains the template for generating ext_redis.py file.
"""

TEMPLATE = '''"""
Redis extension initialization
"""
from typing import Any

from tomskit.redis import RedisClientWrapper

from configs import app_settings


def is_enabled() -> bool:
    """Check if the extension is enabled."""
    return True


def init_app(app: Any = None):
    """
    Initialize Redis connection from app settings.

    Args:
        app: FastAPI application instance

    Returns:
        None
    """
    RedisClientWrapper.initialize(app_settings.redis)
'''
