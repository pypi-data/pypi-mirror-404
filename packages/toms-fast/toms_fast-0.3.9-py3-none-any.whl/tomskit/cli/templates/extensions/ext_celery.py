"""
Celery Extension Template for tomskit CLI

This template file contains the template for generating ext_celery.py file.
The template uses {project_name} as a placeholder that will be replaced
when generating the actual file.
"""

TEMPLATE = '''"""
Celery Extension Initialization
"""
import ssl
from typing import Any

from celery.schedules import crontab  # noqa: E402, F401, F403
from tomskit.celery import AsyncCelery
from tomskit.server import FastApp

from configs import app_settings


def is_enabled() -> bool:
    return True


def _get_celery_ssl_options() -> dict[str, Any] | None:
    """Get SSL configuration for Celery broker/backend connections."""
    if not app_settings.redis.REDIS_USE_SSL:
        return None

    broker_is_redis = app_settings.celery.CELERY_BROKER_URL and (
        app_settings.celery.CELERY_BROKER_URL.startswith("redis://") or
        app_settings.celery.CELERY_BROKER_URL.startswith("rediss://")
    )

    if not broker_is_redis:
        return None

    cert_reqs_map = {{
        "CERT_NONE": ssl.CERT_NONE,
        "CERT_OPTIONAL": ssl.CERT_OPTIONAL,
        "CERT_REQUIRED": ssl.CERT_REQUIRED,
    }}

    ssl_cert_reqs = cert_reqs_map.get(
        app_settings.redis.REDIS_SSL_CERT_REQS,
        ssl.CERT_NONE
    )

    return {{
        "ssl_cert_reqs": ssl_cert_reqs,
        "ssl_ca_certs": app_settings.redis.REDIS_SSL_CA_CERTS,
        "ssl_certfile": app_settings.redis.REDIS_SSL_CERTFILE,
        "ssl_keyfile": app_settings.redis.REDIS_SSL_KEYFILE,
    }}


def _create_celery_app() -> AsyncCelery:
    """Create Celery application instance with basic configuration."""
    broker_transport_options = {{}}

    if app_settings.celery.CELERY_USE_SENTINEL:
        broker_transport_options = {{
            "master_name": app_settings.celery.CELERY_SENTINEL_MASTER_NAME,
            "sentinel_kwargs": {{
                "socket_timeout": app_settings.celery.CELERY_SENTINEL_SOCKET_TIMEOUT,
                "password": app_settings.celery.CELERY_SENTINEL_PASSWORD,
            }},
        }}

    app = AsyncCelery(
        '{project_name}',
        broker=app_settings.celery.CELERY_BROKER_URL,
        backend=app_settings.celery.CELERY_RESULT_BACKEND,
        broker_transport_options=broker_transport_options,
    )

    ssl_options = _get_celery_ssl_options()
    if ssl_options:
        app.conf.update(
            broker_use_ssl=ssl_options,
            redis_backend_use_ssl=ssl_options if app_settings.celery.CELERY_RESULT_BACKEND == "redis" else None,
        )

    return app


def init_client(app: FastApp | None = None) -> AsyncCelery:
    """
    Initialize Celery client for FastAPI application.

    Client only needs basic broker/backend configuration for sending tasks.
    No worker-specific configuration (logging, task registration, etc.) is needed.

    Args:
        app: FastAPI application instance (required, for storing in app.state)

    Returns:
        AsyncCelery: Celery application instance
    """
    if app is None:
        raise ValueError("FastAPI app instance is required for init_client()")

    if not hasattr(app, 'state'):
        raise ValueError("App instance must have 'state' attribute (FastAPI app)")

    if hasattr(app.state, 'celery_app'):
        celery_app_from_state = getattr(app.state, 'celery_app', None)
        if celery_app_from_state is not None and isinstance(celery_app_from_state, AsyncCelery):
            return celery_app_from_state

    celery_app = _create_celery_app()
    celery_app.conf.update(
        task_ignore_result=True,
    )

    app.state.celery_app = celery_app
    return celery_app


def init_worker() -> AsyncCelery:
    """
    Initialize Celery worker for worker processes.

    Worker needs complete configuration including:
    - Logging configuration (log_level, worker_hijack_root_logger)
    - Worker-specific configuration (broker_connection_retry_on_startup)
    - Task registration (tasks should be imported after calling this function)

    Returns:
        AsyncCelery: Celery application instance
    """
    celery_app = _create_celery_app()

    # Note: log_level should match LOG_CELERY_LEVEL from configure_logging().
    # Since worker_hijack_root_logger=False, Celery uses the Python logging
    # system configured by configure_logging(), so log formats are controlled
    # by the formatters set up in configure_logging().
    celery_app.conf.update(
        broker_connection_retry_on_startup=True,
        log_level=app_settings.logger.LOG_CELERY_LEVEL,
        worker_hijack_root_logger=False,
        task_ignore_result=True,
    )

    celery_app.set_default()

    # Template: Configure task imports and periodic task schedule
    # Uncomment and modify the following code to register tasks and configure beat schedule
    #
    # # Import regular tasks (tasks that wait for requests)
    # imports = [
    #     "tasks.example_task",
    #     "tasks.example_task2",
    #     "tasks.example_task3",
    # ]
    #
    # # Configure periodic tasks (beat schedule)
    # beat_schedule = {{
    #     "periodic-task-name": {{
    #         "task": "tasks.periodic_tasks.my_periodic_task",
    #         "schedule": crontab(minute="*/15"),  # Every 15 minutes
    #         # Other schedule options:
    #         # - crontab(hour=2, minute=0)  # Daily at 2:00 AM
    #         # - crontab(minute=0)  # Every hour
    #         # - 60.0  # Every 60 seconds
    #     }},
    # }}
    #
    # celery_app.conf.update(beat_schedule=beat_schedule, imports=imports)

    return celery_app


def init_app(app: FastApp | None = None) -> AsyncCelery:
    """
    Initialize Celery application (backward compatible).

    Automatically determines context:
    - If app is None, initializes worker (for worker processes)
    - Otherwise, initializes client (for FastAPI application)

    Args:
        app: Application instance (FastApp or None)

    Returns:
        AsyncCelery: Celery application instance
    """
    if app is None:
        return init_worker()

    if not hasattr(app, 'state'):
        raise ValueError("App instance must have 'state' attribute (FastAPI app)")

    if hasattr(app.state, 'celery_app'):
        celery_app_from_state = getattr(app.state, 'celery_app', None)
        if celery_app_from_state is not None and isinstance(celery_app_from_state, AsyncCelery):
            return celery_app_from_state

    celery_app = init_client(app)
    app.state.celery_app = celery_app
    return celery_app
'''
