"""
Logger Extension Template for tomskit CLI

This template file contains the template for generating ext_logger.py file.
"""

TEMPLATE = '''"""
Logger extension initialization
"""
from typing import Any, Optional, Dict, Tuple
from contextvars import ContextVar

from tomskit.logger import configure_logging

from configs import app_settings


def is_enabled() -> bool:
    """Check if the extension is enabled."""
    return True


def init_app(
    app: Any = None,
    context_vars: Optional[Dict[str, Tuple[Optional[ContextVar], Optional[Any]]]] = None,
    app_type: Optional[str] = None,
):
    """
    Initialize the logger system from app settings.

    Args:
        app: FastAPI application instance (optional, for future use)
        context_vars: 上下文变量映射，格式为 {{字段名: (ContextVar | None, getter函数 | None)}}
            例如: {{"task_id": (None, lambda: get_task_id())}}
            如果不提供，则不注入任何上下文变量
            在 Celery worker 中，应该传入 task_id 的 getter
        app_type: 应用类型，可选值：
            - "fastapi": 仅配置 FastAPI 相关的 logger（access, framework, sql）
            - "celery": 仅配置 Celery 相关的 logger
            - None: 自动检测（如果 app 不为 None 则为 "fastapi"，否则为 "celery"）

    Returns:
        None
    """
    # 自动检测应用类型
    if app_type is None:
        app_type = "fastapi" if app is not None else "celery"
    
    configure_logging(app_settings.logger, context_vars=context_vars, app_type=app_type)
'''
