"""
Warnings Extension Template for tomskit CLI

This template file contains the template for generating ext_warnings.py file.
"""

TEMPLATE = '''"""
Warnings extension initialization
"""

from typing import Any
from tomskit.tools import enable_unawaited_warning


def is_enabled() -> bool:
    """Check if the extension is enabled."""
    return True


def init_app(app: Any = None):
    """
    Initialize unawaited coroutine warning handler.

    This should be called after logger initialization because
    it uses logger.critical to log warnings.

    Args:
        app: FastAPI application instance or None

    Returns:
        None
    """
    enable_unawaited_warning()
'''
