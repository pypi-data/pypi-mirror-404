import os
from typing import List, Optional
from pydantic import Field, field_validator
from tomskit import TomsKitBaseSettings


class BaseServerSettings(TomsKitBaseSettings):
    """
    Base configuration settings for ASGI/WSGI servers (Gunicorn, Hypercorn)
    Contains common configuration options shared by all servers.
    Uses SERVER_* prefix for environment variables by default.
    """

    BIND: str = Field(
        default="0.0.0.0:5001",
        alias="SERVER_BIND",
        description="Bind address and port to listen on"
    )

    PIDFILE: Optional[str] = Field(
        default=None,
        alias="SERVER_PIDFILE",
        description="File to write the PID of the main process"
    )

    WORKERS: int = Field(
        default=0,
        alias="SERVER_WORKERS",
        description="Number of workers to run (0 = auto by CPU cores)"
    )

    DAEMON: bool = Field(
        default=False,
        alias="SERVER_DAEMON",
        description="Run as a daemon"
    )

    @field_validator("WORKERS", mode="before")
    @classmethod
    def default_workers(cls, v):
        """Shared validator for workers count (0 = auto by CPU cores)"""
        if not v or int(v) <= 0:
            return os.cpu_count() or 1
        return int(v)

    @field_validator("PIDFILE", mode="after")
    @classmethod
    def ensure_pidfile_dir_exists(cls, v: Optional[str]):
        """Ensure PID file directory exists"""
        if not v:
            return None
        dir_path = os.path.dirname(v)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        return v


class GunicornSettings(BaseServerSettings):
    """
    Configuration settings for Gunicorn
    Inherits common settings (BIND, PIDFILE, WORKERS, DAEMON) from BaseServerSettings
    which use SERVER_* prefix for environment variables.
    Only Gunicorn-specific settings use GUNICORN_* prefix.
    """

    # Gunicorn 特有的配置项，使用 GUNICORN_* 前缀
    GUNICORN_PROC_NAME: Optional[str] = Field(
        default=None,
        description="Name of the process"
    )

    GUNICORN_CPU_AFFINITY: List[int] = Field(
        default_factory=list,
        description="List of CPU core IDs to bind workers to"
    )

    @field_validator("GUNICORN_CPU_AFFINITY", mode="before")
    @classmethod
    def parse_cpu_affinity(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return []
        if isinstance(v, str):
            try:
                return [int(x.strip()) for x in v.split(",") if x.strip()]
            except Exception as e:
                raise ValueError(f"Invalid CPU_AFFINITY string: {v}") from e
        if isinstance(v, list):
            return v
        return []


class HypercornSettings(BaseServerSettings):
    """
    Configuration settings for Hypercorn
    Inherits common settings (BIND, PIDFILE, WORKERS, DAEMON) from BaseServerSettings
    which use SERVER_* prefix for environment variables.
    Only Hypercorn-specific settings use HYPERCORN_* prefix.
    """

    # Hypercorn 特有的配置项，使用 HYPERCORN_* 前缀
    HYPERCORN_ACCESSLOG: Optional[str] = Field(
        default=None,
        description="Access log file path (None = disable access logging)"
    )

    HYPERCORN_ERRORLOG: Optional[str] = Field(
        default=None,
        description="Error log file path (None = stderr)"
    )

    HYPERCORN_LOG_LEVEL: str = Field(
        default="info",
        description="Log level (critical, error, warning, info, debug, trace)"
    )

    HYPERCORN_ACCESS_LOG_FORMAT: str = Field(
        default='%(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
        description="Access log format string"
    )

    @field_validator("HYPERCORN_LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["critical", "error", "warning", "info", "debug", "trace"]
        if v and v.lower() in valid_levels:
            return v.lower()
        return "info"
