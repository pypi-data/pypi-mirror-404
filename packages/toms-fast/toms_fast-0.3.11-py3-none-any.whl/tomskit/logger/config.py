from pydantic import Field
from tomskit import TomsKitBaseSettings


class LoggerConfig(TomsKitBaseSettings):
    """
    日志配置类
    
    用于配置日志系统的各项参数，包括日志级别、格式、文件路径、轮转策略等。
    支持应用日志、访问日志、SQL 日志和 Celery 日志的独立配置。
    """
    # === 基础配置 ===
    LOG_PREFIX: str = Field(
        description="日志前缀，会添加到每条日志记录中",
        default="",
    )
    
    LOG_DIR: str = Field(
        description="日志文件存储目录",
        default="logs",
    )

    LOG_NAME: str = Field(
        description="应用日志文件名（不含扩展名）",
        default="apps",
    )

    LOG_LEVEL: str = Field(
        description="应用日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        default="INFO",
    )

    LOG_FORMAT: str = Field(
        description="应用日志格式，支持 %(trace_id)s 和 %(prefix)s 占位符",
        default="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    )

    LOG_USE_UTC: bool = Field(
        description="是否使用 UTC 时间",
        default=False,
    )

    LOG_DATE_FORMAT: str = Field(
        description="日志日期时间格式",
        default="%Y-%m-%d %H:%M:%S",
    )

    LOG_BACKUP_COUNT: int = Field(
        description="日志文件备份数量，0 表示不保留历史文件",
        default=0,
    )

    LOG_ROTATE_WHEN: str = Field(
        description="日志轮转时间单位 (midnight, D, H, M, S)",
        default="midnight",
    )

    LOG_ROTATE_USE_UTC: bool = Field(
        description="轮转是否按 UTC 零点计算；False 则按本地零点（跨日后立即切到新文件）",
        default=False,
    )

    # === 异步队列日志（AsyncQueueHandler）===
    LOG_ASYNC_ENABLED: bool = Field(
        description="是否使用异步队列写日志（内存队列 + 后台线程，解耦磁盘 I/O）",
        default=False,
    )

    LOG_ASYNC_QUEUE_SIZE: int = Field(
        description="异步日志队列最大长度，仅当 LOG_ASYNC_ENABLED=True 时生效",
        default=8192,
    )

    # === 访问日志配置 ===
    LOG_ACCESS_NAME: str = Field(
        description="访问日志文件名（不含扩展名）",
        default="access",
    )

    LOG_ACCESS_FORMAT: str = Field(
        description="访问日志格式（Apache Common Log Format）",
        default='%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"',
    )

    # === SQL 日志配置 ===
    LOG_SQL_ENABLED: bool = Field(
        description="是否启用独立的 SQL 日志文件",
        default=False,
    )

    LOG_SQL_NAME: str = Field(
        description="SQL 日志文件名（不含扩展名）",
        default="sql",
    )

    LOG_SQL_LEVEL: str = Field(
        description="SQL 日志级别",
        default="INFO",
    )

    # === Celery 日志配置 ===
    LOG_CELERY_ENABLED: bool = Field(
        description="是否启用独立的 Celery 日志文件",
        default=False,
    )

    LOG_CELERY_NAME: str = Field(
        description="Celery 日志文件名（不含扩展名）",
        default="celery",
    )

    LOG_CELERY_LEVEL: str = Field(
        description="Celery 日志级别",
        default="INFO",
    )

    LOG_CELERY_FORMAT: str = Field(
        description="Celery 默认日志格式，支持 %(task_id)s 和 %(prefix)s 占位符",
        default="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    )

    LOG_CELERY_TASKS_FORMAT: str = Field(
        description="tasks 目录下任务函数的日志格式，可单独配置（如仅含 task_id）",
        default="[%(asctime)s] [%(levelname)s] [%(task_id)s] %(message)s",
    )

    LOG_CELERY_SCHEDULE_FORMAT: str = Field(
        description="schedule 目录下任务函数的日志格式，可单独配置（如仅含 task_id）",
        default="[%(asctime)s] [%(levelname)s] [%(task_id)s] %(message)s",
    )

    LOG_CELERY_ROTATE_WHEN: str = Field(
        description="Celery 日志轮转时间单位 (midnight, D, H, M, S)",
        default="midnight",
    )

    LOG_CELERY_BACKUP_COUNT: int = Field(
        description="Celery 日志文件备份数量，0 表示不保留历史文件",
        default=0,
    )

    # === 第三方库日志配置 ===
    LOG_THIRD_PARTY_LEVEL: str = Field(
        description="第三方库日志级别（用于降噪）",
        default="WARNING",
    )

