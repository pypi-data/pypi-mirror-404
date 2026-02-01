from typing import Any, Optional
from urllib.parse import quote_plus

from pydantic import Field, NonNegativeInt, PositiveInt, PositiveFloat, computed_field
from tomskit import TomsKitBaseSettings


class CeleryConfig(TomsKitBaseSettings):
    """
    Celery 配置类
    
    所有配置项统一以 CELERY_ 开头，便于管理和识别。
    支持：
    - Redis 作为 broker 和 backend
    - 数据库作为结果后端
    - 所有标准 Celery 配置选项
    """

    # ========== Redis Broker Configuration ==========
    CELERY_BROKER_REDIS_HOST: str = Field(
        description="Redis host for Celery broker",
        default="localhost",
    )

    CELERY_BROKER_REDIS_PORT: PositiveInt = Field(
        description="Redis port for Celery broker",
        default=6379,
    )

    CELERY_BROKER_REDIS_USERNAME: Optional[str] = Field(
        description="Redis username for Celery broker (if required)",
        default=None,
    )

    CELERY_BROKER_REDIS_PASSWORD: Optional[str] = Field(
        description="Redis password for Celery broker (if required)",
        default=None,
    )

    CELERY_BROKER_REDIS_DB: NonNegativeInt = Field(
        description="Redis database number for Celery broker",
        default=0,
    )

    CELERY_USE_SENTINEL: bool | None = Field(
        description="Whether to use Redis Sentinel for high availability.",
        default=False,
    )

    CELERY_SENTINEL_MASTER_NAME: str | None = Field(
        description="Name of the Redis Sentinel master.",
        default=None,
    )

    CELERY_SENTINEL_PASSWORD: str | None = Field(
        description="Password of the Redis Sentinel master.",
        default=None,
    )
    CELERY_SENTINEL_SOCKET_TIMEOUT: PositiveFloat | None = Field(
        description="Timeout for Redis Sentinel socket operations in seconds.",
        default=0.1,
    )

    # ========== Result Backend Configuration ==========
    CELERY_RESULT_BACKEND_TYPE: str = Field(
        description="Result backend type: 'redis' or 'database'",
        default="redis",
    )

    # Redis Backend Configuration (if CELERY_RESULT_BACKEND_TYPE='redis')
    CELERY_RESULT_BACKEND_REDIS_HOST: str = Field(
        description="Redis host for Celery result backend",
        default="localhost",
    )

    CELERY_RESULT_BACKEND_REDIS_PORT: PositiveInt = Field(
        description="Redis port for Celery result backend",
        default=6379,
    )

    CELERY_RESULT_BACKEND_REDIS_USERNAME: Optional[str] = Field(
        description="Redis username for Celery result backend (if required)",
        default=None,
    )

    CELERY_RESULT_BACKEND_REDIS_PASSWORD: Optional[str] = Field(
        description="Redis password for Celery result backend (if required)",
        default=None,
    )

    CELERY_RESULT_BACKEND_REDIS_DB: NonNegativeInt = Field(
        description="Redis database number for Celery result backend",
        default=1,  # Different from broker DB by default
    )

    # Database Backend Configuration (if CELERY_RESULT_BACKEND_TYPE='database')
    # Uses the same database config as SQLAlchemy
    CELERY_RESULT_BACKEND_DATABASE_URI_SCHEME: str = Field(
        description="Database URI scheme for Celery result backend (e.g., 'mysql', 'postgresql')",
        default="mysql",
    )

    # ========== Celery Task Configuration ==========
    CELERY_TASK_SERIALIZER: str = Field(
        description="Task serialization format. Supported formats: 'json', 'orjson' (requires orjson package)",
        default="json",
    )

    CELERY_RESULT_SERIALIZER: str = Field(
        description="Result serialization format. Supported formats: 'json', 'orjson' (requires orjson package)",
        default="json",
    )

    CELERY_ACCEPT_CONTENT: list[str] = Field(
        description="Accepted content types. Supported formats: 'json', 'orjson' (requires orjson package)",
        default=["json"],
    )

    CELERY_TIMEZONE: str = Field(
        description="Celery timezone",
        default="UTC",
    )

    CELERY_ENABLE_UTC: bool = Field(
        description="Enable UTC timezone",
        default=True,
    )

    CELERY_TASK_TRACK_STARTED: bool = Field(
        description="Track task started state",
        default=True,
    )

    CELERY_TASK_TIME_LIMIT: Optional[NonNegativeInt] = Field(
        description="Hard time limit for tasks in seconds",
        default=None,
    )

    CELERY_TASK_SOFT_TIME_LIMIT: Optional[NonNegativeInt] = Field(
        description="Soft time limit for tasks in seconds",
        default=None,
    )

    CELERY_TASK_IGNORE_RESULT: bool = Field(
        description="Ignore task results by default",
        default=False,
    )

    CELERY_RESULT_EXPIRES: Optional[NonNegativeInt] = Field(
        description="Result expiration time in seconds",
        default=None,
    )

    # ========== Database Configuration (for worker and result backend) ==========
    CELERY_DB_HOST: str = Field(
        description="数据库主机地址（用于 worker 和结果后端）",
        default="localhost",
    )

    CELERY_DB_PORT: PositiveInt = Field(
        description="数据库端口（用于 worker 和结果后端）",
        default=5432,
    )

    CELERY_DB_USERNAME: str = Field(
        description="数据库用户名（用于 worker 和结果后端）",
        default="",
    )

    CELERY_DB_PASSWORD: str = Field(
        description="数据库密码（用于 worker 和结果后端）",
        default="",
    )

    CELERY_DB_DATABASE: str = Field(
        description="数据库名称（用于 worker 和结果后端）",
        default="tomskitdb",
    )

    CELERY_DB_CHARSET: str = Field(
        description="数据库字符集（用于 worker 和结果后端）",
        default="",
    )

    CELERY_DB_EXTRAS: str = Field(
        description="数据库额外参数（用于 worker 和结果后端）。示例: keepalives_idle=60&keepalives=1",
        default="",
    )

    CELERY_SQLALCHEMY_DATABASE_URI_SCHEME: str = Field(
        description="SQLAlchemy 异步数据库 URI 协议（用于 worker）",
        default="mysql+aiomysql",
    )

    CELERY_SQLALCHEMY_DATABASE_SYNC_URI_SCHEME: str = Field(
        description="SQLAlchemy 同步数据库 URI 协议（用于 worker）",
        default="mysql+pymysql",
    )

    CELERY_SQLALCHEMY_POOL_SIZE: NonNegativeInt = Field(
        description="SQLAlchemy 连接池大小（用于 worker）",
        default=300,
    )

    CELERY_SQLALCHEMY_MAX_OVERFLOW: NonNegativeInt = Field(
        description="SQLAlchemy 最大溢出连接数（用于 worker）",
        default=10,
    )

    CELERY_SQLALCHEMY_POOL_RECYCLE: NonNegativeInt = Field(
        description="SQLAlchemy 连接池回收时间（秒，用于 worker）",
        default=3600,
    )

    CELERY_SQLALCHEMY_POOL_PRE_PING: bool = Field(
        description="启用 SQLAlchemy 连接池预检查（用于 worker）",
        default=False,
    )

    CELERY_SQLALCHEMY_ECHO: bool = Field(
        description="启用 SQLAlchemy SQL 回显（用于 worker）",
        default=False,
    )

    CELERY_SQLALCHEMY_POOL_ECHO: bool = Field(
        description="启用 SQLAlchemy 连接池回显（用于 worker）",
        default=False,
    )

    # ========== Redis Configuration (for worker) ==========
    CELERY_WORKER_REDIS_HOST: str = Field(
        description="Redis 主机地址（用于 worker）",
        default="localhost",
    )

    CELERY_WORKER_REDIS_PORT: PositiveInt = Field(
        description="Redis 端口（用于 worker）",
        default=6379,
    )

    CELERY_WORKER_REDIS_USERNAME: Optional[str] = Field(
        description="Redis 用户名（用于 worker，可选）",
        default=None,
    )

    CELERY_WORKER_REDIS_PASSWORD: Optional[str] = Field(
        description="Redis 密码（用于 worker，可选）",
        default=None,
    )

    CELERY_WORKER_REDIS_DB: NonNegativeInt = Field(
        description="Redis 数据库编号（用于 worker）",
        default=0,
    )

    # ========== Computed Properties ==========

    @computed_field  # type: ignore
    @property
    def CELERY_BROKER_URL(self) -> str:
        """Generate Redis broker URL"""
        auth = ""
        if self.CELERY_BROKER_REDIS_USERNAME or self.CELERY_BROKER_REDIS_PASSWORD:
            username = quote_plus(self.CELERY_BROKER_REDIS_USERNAME or "")
            password = quote_plus(self.CELERY_BROKER_REDIS_PASSWORD or "")
            auth = f"{username}:{password}@"
        return f"redis://{auth}{self.CELERY_BROKER_REDIS_HOST}:{self.CELERY_BROKER_REDIS_PORT}/{self.CELERY_BROKER_REDIS_DB}"

    @computed_field  # type: ignore
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """生成结果后端 URL"""
        if self.CELERY_RESULT_BACKEND_TYPE == "database":
            # 数据库后端
            db_extras = (
                f"{self.CELERY_DB_EXTRAS}&client_encoding={self.CELERY_DB_CHARSET}"
                if self.CELERY_DB_CHARSET
                else self.CELERY_DB_EXTRAS
            ).strip("&")
            db_extras = f"?{db_extras}" if db_extras else ""
            
            username = quote_plus(self.CELERY_DB_USERNAME)
            password = quote_plus(self.CELERY_DB_PASSWORD)
            return (
                f"db+{self.CELERY_RESULT_BACKEND_DATABASE_URI_SCHEME}://"
                f"{username}:{password}@{self.CELERY_DB_HOST}:{self.CELERY_DB_PORT}/{self.CELERY_DB_DATABASE}"
                f"{db_extras}"
            )
        else:
            # Redis backend
            auth = ""
            if (
                self.CELERY_RESULT_BACKEND_REDIS_USERNAME
                or self.CELERY_RESULT_BACKEND_REDIS_PASSWORD
            ):
                username = quote_plus(
                    self.CELERY_RESULT_BACKEND_REDIS_USERNAME or ""
                )
                password = quote_plus(
                    self.CELERY_RESULT_BACKEND_REDIS_PASSWORD or ""
                )
                auth = f"{username}:{password}@"
            return (
                f"redis://{auth}{self.CELERY_RESULT_BACKEND_REDIS_HOST}:"
                f"{self.CELERY_RESULT_BACKEND_REDIS_PORT}/{self.CELERY_RESULT_BACKEND_REDIS_DB}"
            )

    @computed_field  # type: ignore
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """生成 SQLAlchemy 异步数据库 URI"""
        db_extras = (
            f"{self.CELERY_DB_EXTRAS}&client_encoding={self.CELERY_DB_CHARSET}"
            if self.CELERY_DB_CHARSET
            else self.CELERY_DB_EXTRAS
        ).strip("&")
        db_extras = f"?{db_extras}" if db_extras else ""
        username = quote_plus(self.CELERY_DB_USERNAME)
        password = quote_plus(self.CELERY_DB_PASSWORD)
        return (
            f"{self.CELERY_SQLALCHEMY_DATABASE_URI_SCHEME}://"
            f"{username}:{password}@{self.CELERY_DB_HOST}:{self.CELERY_DB_PORT}/{self.CELERY_DB_DATABASE}"
            f"{db_extras}"
        )

    @computed_field  # type: ignore
    @property
    def SQLALCHEMY_DATABASE_SYNC_URI(self) -> str:
        """生成 SQLAlchemy 同步数据库 URI"""
        db_extras = (
            f"{self.CELERY_DB_EXTRAS}&client_encoding={self.CELERY_DB_CHARSET}"
            if self.CELERY_DB_CHARSET
            else self.CELERY_DB_EXTRAS
        ).strip("&")
        db_extras = f"?{db_extras}" if db_extras else ""
        username = quote_plus(self.CELERY_DB_USERNAME)
        password = quote_plus(self.CELERY_DB_PASSWORD)
        return (
            f"{self.CELERY_SQLALCHEMY_DATABASE_SYNC_URI_SCHEME}://"
            f"{username}:{password}@{self.CELERY_DB_HOST}:{self.CELERY_DB_PORT}/{self.CELERY_DB_DATABASE}"
            f"{db_extras}"
        )

    @computed_field  # type: ignore
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self) -> dict[str, Any]:
        """生成 SQLAlchemy 引擎选项"""
        return {
            "pool_size": self.CELERY_SQLALCHEMY_POOL_SIZE,
            "max_overflow": self.CELERY_SQLALCHEMY_MAX_OVERFLOW,
            "pool_recycle": self.CELERY_SQLALCHEMY_POOL_RECYCLE,
            "pool_pre_ping": self.CELERY_SQLALCHEMY_POOL_PRE_PING,
            "echo": self.CELERY_SQLALCHEMY_ECHO,
            "echo_pool": self.CELERY_SQLALCHEMY_POOL_ECHO,
        }

    
