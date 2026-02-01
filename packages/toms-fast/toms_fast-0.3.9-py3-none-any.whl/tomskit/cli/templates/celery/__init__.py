"""
Celery templates module
Contains all Celery related file templates.
"""

from typing import Callable

from .celery_app import TEMPLATE as CELERY_APP_TEMPLATE
from .tasks_init import TEMPLATE as TASKS_INIT_TEMPLATE
from .example_task import TEMPLATE as EXAMPLE_TASK_TEMPLATE


def get_celery_templates(project_name: str) -> dict[str, Callable[[], str]]:
    """Get Celery templates."""
    return {
        "celery_py": lambda: CELERY_APP_TEMPLATE.format(project_name=project_name),
        "tasks_init_py": lambda: TASKS_INIT_TEMPLATE,
        "example_task_py": lambda: EXAMPLE_TASK_TEMPLATE.format(project_name=project_name),
    }
