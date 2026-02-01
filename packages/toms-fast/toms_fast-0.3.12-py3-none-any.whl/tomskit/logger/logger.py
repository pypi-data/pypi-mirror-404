import logging
import queue
from abc import ABC, abstractmethod
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional

from logging.handlers import QueueHandler, QueueListener, TimedRotatingFileHandler

from tomskit.logger.config import LoggerConfig

AppType = Literal["fastapi", "celery", "alembic"]
NOISY_LOGGERS = ("httpx", "httpcore", "urllib3", "asyncio", "boto3", "botocore")


@dataclass(frozen=True)
class ContextField:
    """单个日志上下文字段：name + ContextVar + 默认值。"""
    name: str
    var: Optional[ContextVar] = None
    default: Any = ""


class ContextRegistry:
    """管理日志上下文字段，向 LogRecord 注入 ContextVar 值。"""

    def __init__(self, fields: Iterable[ContextField]):
        self._fields = list[ContextField](fields)

    def inject(self, record: logging.LogRecord) -> None:
        for field in self._fields:
            if field.var is None:
                value = field.default
            else:
                try:
                    value = field.var.get()
                except LookupError:
                    value = field.default
            setattr(record, field.name, value if value is not None else field.default)

    def defaults(self) -> Dict[str, Any]:
        return {f.name: f.default for f in self._fields}


class ContextFilter(logging.Filter):
    def __init__(self, registry: ContextRegistry):
        super().__init__()
        self.registry = registry

    def filter(self, record: logging.LogRecord) -> bool:
        self.registry.inject(record)
        return True


class SafeFormatter(logging.Formatter):
    def __init__(
        self, 
        fmt: str, 
        datefmt: Optional[str] = None, 
        defaults: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(fmt, datefmt)
        self._defaults = defaults or {}

    def format(self, record: logging.LogRecord) -> str:
        for key, default in self._defaults.items():
            if not hasattr(record, key):
                setattr(record, key, default)
        return super().format(record)

def create_timed_handler(
    filename: str,
    when: str,
    backup_count: int,
    utc: bool,
) -> TimedRotatingFileHandler:
    handler = TimedRotatingFileHandler(
        filename=filename,
        when=when,
        backupCount=backup_count,
        encoding="utf-8",
        utc=utc,
    )
    handler.suffix = "%Y-%m-%d"
    return handler


class AsyncQueueHandler(logging.Handler):
    """
    独立的可插拔异步日志处理器。

    特点：
    1. 内存队列缓冲，彻底解耦磁盘 I/O。
    2. 自动管理后台 Listener 线程。
    3. 支持多目的地输出（同时写文件和控制台）。

    文件落地复用 create_timed_handler，与同步 Handler 轮转策略一致。
    """

    def __init__(
        self,
        filename: Optional[str] = None,
        fmt: str = "%(message)s",
        datefmt: str = "%Y-%m-%d %H:%M:%S",
        defaults: Optional[dict[str, Any]] = None,
        queue_size: int = 10000,
        when: str = "midnight",
        backup_count: int = 30,
        utc: bool = False,
    ) -> None:
        super().__init__()
        self._queue: queue.Queue = queue.Queue(maxsize=queue_size)
        formatter = SafeFormatter(fmt, datefmt, defaults)

        handlers: List[logging.Handler] = []
        console_h = logging.StreamHandler()
        console_h.setFormatter(formatter)
        handlers.append(console_h)

        if filename:
            file_h = create_timed_handler(filename, when, backup_count, utc)
            file_h.setFormatter(formatter)
            handlers.append(file_h)

        self._q_handler = QueueHandler(self._queue)
        self._listener = QueueListener(
            self._queue, *handlers, respect_handler_level=True
        )
        self._listener.start()

    def emit(self, record: logging.LogRecord) -> None:
        self._q_handler.emit(record)

    def close(self) -> None:
        if self._listener:
            self._listener.stop()
        super().close()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} (queue_size={self._queue.maxsize})>"


def configure_third_party(level: str) -> None:
    lvl = getattr(logging, level.upper(), logging.WARNING)
    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(lvl)


class LoggingBase(ABC):
    def __init__(
        self,
        config: LoggerConfig,
        context_registry: ContextRegistry,
        fmt: Optional[str] = None,
    ):
        self.config = config
        self.registry = context_registry
        self.fmt = fmt
        Path(config.LOG_DIR).mkdir(parents=True, exist_ok=True)

    def setup(self) -> None:
        root = logging.getLogger()
        root.setLevel(self.config.LOG_LEVEL)
        root.handlers.clear()
        root.addFilter(ContextFilter(self.registry))
        self._setup_loggers()
        configure_third_party(self.config.LOG_THIRD_PARTY_LEVEL)

    @abstractmethod
    def _setup_loggers(self) -> None:
        ...

    def _file_logger(
        self,
        name: str,
        filename: str,
        fmt: str,
        level: str,
    ) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.setLevel(level)
        logger.propagate = False
        # logger.addFilter(ContextFilter(self.registry))

        filepath = f"{self.config.LOG_DIR}/{filename}.log"
        fmt_obj = SafeFormatter(
            fmt, 
            self.config.LOG_DATE_FORMAT, 
            self.registry.defaults(),
        )
        handler: logging.Handler

        if self.config.LOG_ASYNC_ENABLED:
            handler = AsyncQueueHandler(
                filename=filepath,
                fmt=fmt,
                datefmt=self.config.LOG_DATE_FORMAT,
                defaults=self.registry.defaults(),
                queue_size=self.config.LOG_ASYNC_QUEUE_SIZE,
                when=self.config.LOG_ROTATE_WHEN,
                backup_count=self.config.LOG_BACKUP_COUNT,
                utc=self.config.LOG_ROTATE_USE_UTC,
            )
        else:
            handler = create_timed_handler(
                filename=filepath,
                when=self.config.LOG_ROTATE_WHEN,
                backup_count=self.config.LOG_BACKUP_COUNT,
                utc=self.config.LOG_ROTATE_USE_UTC,
            )
            handler.setFormatter(fmt_obj)
        handler.addFilter(ContextFilter(self.registry))
        logger.addHandler(handler)
        return logger


class FastAPILogging(LoggingBase):
    def _setup_loggers(self) -> None:
        loggers = [
            (
                "", 
                self.config.LOG_NAME, 
                self.fmt or self.config.LOG_FORMAT, 
                self.config.LOG_LEVEL
            ),
            (
                "uvicorn", 
                self.config.LOG_ACCESS_NAME, 
                self.fmt or self.config.LOG_ACCESS_FORMAT, 
                "INFO"
            ),
        ]
        if self.config.LOG_SQL_ENABLED:
            loggers.append((
                "sqlalchemy",
                self.config.LOG_SQL_NAME,
                self.fmt or self.config.LOG_FORMAT,
                self.config.LOG_SQL_LEVEL,
            ))
        for name, filename, fmt, level in loggers:
            self._file_logger(name, filename, fmt, level)


class CeleryLogging(LoggingBase):
    """Celery 日志：有 tasks/schedule 时不配 root，celery 用默认格式，tasks/schedule 用独立格式。"""

    def _setup_loggers(self) -> None:
        default_fmt = self.fmt or self.config.LOG_CELERY_FORMAT
        loggers = [
            ("celery", self.config.LOG_CELERY_NAME, default_fmt, self.config.LOG_CELERY_LEVEL),
            ("tasks", self.config.LOG_CELERY_NAME, self.config.LOG_CELERY_TASKS_FORMAT, self.config.LOG_CELERY_LEVEL),
            ("schedule", self.config.LOG_CELERY_NAME, self.config.LOG_CELERY_SCHEDULE_FORMAT, self.config.LOG_CELERY_LEVEL),
        ]
        if self.config.LOG_SQL_ENABLED:
            loggers.append((
                "sqlalchemy",
                self.config.LOG_SQL_NAME,
                default_fmt,
                self.config.LOG_SQL_LEVEL,
            ))
        for name, filename, fmt, level in loggers:
            self._file_logger(name, filename, fmt, level)


class AlembicLogging(LoggingBase):
    def _setup_loggers(self) -> None:
        self._file_logger(
            "",
            "alembic",
            self.fmt or self.config.LOG_FORMAT,
            self.config.LOG_LEVEL,
        )


def configure_logging(
    settings: LoggerConfig,
    context_registry: Optional[Iterable[ContextField]] = None,
    app_type: AppType = "fastapi",
) -> None:
    """配置日志系统：按 app_type 调用 FastAPILogging / CeleryLogging / AlembicLogging。"""
    registry = (
        ContextRegistry(context_registry)
        if context_registry is not None
        else ContextRegistry([])
    )
    if app_type == "celery":
        CeleryLogging(settings, registry).setup()        
    elif app_type == "alembic":
        AlembicLogging(settings, registry).setup()
    else:
        FastAPILogging(settings, registry).setup()
