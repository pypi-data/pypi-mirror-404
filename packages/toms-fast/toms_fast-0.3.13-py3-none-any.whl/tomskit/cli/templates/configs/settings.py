"""
Configs settings template
Template for generating configs/settings.py file.
"""


def get_settings_template(project_name: str, project_type: str = "full") -> str:
    """Generate configs/settings.py file."""
    celery_field = ""
    if project_type in ("celery", "full"):
        celery_field = "    celery: CeleryConfig = Field(default_factory=CeleryConfig)\n"
    
    return f'''"""
Configuration settings module for {project_name} backend.

This module provides a unified configuration interface that loads all
sub-configurations (database, redis, logger, server, celery) from
environment variables or .env file.

Note: Server configuration (gunicorn) uses SERVER_* prefix for common
settings (BIND, PIDFILE, WORKERS, DAEMON) and GUNICORN_* prefix for
Gunicorn-specific settings.
"""

from pydantic import Field
from tomskit import TomsKitBaseSettings
from tomskit.celery.config import CeleryConfig
from tomskit.sqlalchemy.config import DatabaseConfig
from tomskit.redis.config import RedisConfig
from tomskit.logger.config import LoggerConfig
from tomskit.tools.config import GunicornSettings
from configs.pyproject import PyProjectConfig


class ConfigSettings(TomsKitBaseSettings):
    """
    Unified configuration settings class for {project_name} backend.
    
    This class aggregates all sub-configurations into a single settings object.
    By default, it reads from .env file in the project root directory.
    You can also specify a custom env file via environment variable:
    TOMSKIT_ENV_FILE=xxx.env
    
    Usage:
        from configs import app_settings
        
        # Access database configuration
        db_host = app_settings.database.DB_HOST
        
        # Access Redis configuration
        redis_port = app_settings.redis.REDIS_PORT
        
        # Access logger configuration
        log_level = app_settings.logger.LOG_LEVEL
        
        # Access server configuration (common settings use SERVER_* env vars)
        server_bind = app_settings.gunicorn.BIND
        server_workers = app_settings.gunicorn.WORKERS
    """

    project: PyProjectConfig = Field(default_factory=PyProjectConfig)

{celery_field}    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    logger: LoggerConfig = Field(default_factory=LoggerConfig)
    gunicorn: GunicornSettings = Field(default_factory=GunicornSettings)
'''
