"""
日志模块：配置、上下文、异步队列与按应用类型的一键配置。

常用入口：
  - configure_logging(settings, context_registry=..., app_type="fastapi")
  - LoggerConfig（配置类）

扩展用：
  - ContextField / ContextRegistry（上下文字段）
  - AsyncQueueHandler / SafeFormatter / create_timed_handler（自定义 Handler）
  - FastAPILogging / CeleryLogging / AlembicLogging（按类型直接 setup）
"""

from tomskit.logger.config import LoggerConfig
from tomskit.logger.logger import (
    AppType,
    AsyncQueueHandler,
    CeleryLogging,
    ContextField,
    ContextFilter,
    ContextRegistry,
    FastAPILogging,
    AlembicLogging,
    LoggingBase,
    SafeFormatter,
    configure_logging,
    create_timed_handler,
)

__all__ = [
    # 配置
    "LoggerConfig",
    # 类型
    "AppType",
    # 上下文
    "ContextField",
    "ContextRegistry",
    "ContextFilter",
    # 格式化与 Handler
    "SafeFormatter",
    "create_timed_handler",
    "AsyncQueueHandler",
    # 按类型配置
    "LoggingBase",
    "FastAPILogging",
    "CeleryLogging",
    "AlembicLogging",
    # 入口
    "configure_logging",
]
