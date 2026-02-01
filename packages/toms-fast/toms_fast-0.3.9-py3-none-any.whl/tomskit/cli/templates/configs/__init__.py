"""
Config templates module
Contains all configuration related file templates.
"""

from typing import Callable

from .init import TEMPLATE as CONFIGS_INIT_TEMPLATE
from .pyproject import TEMPLATE as CONFIGS_PYPROJECT_TEMPLATE
from .settings import get_settings_template


def get_configs_templates(project_name: str, project_type: str = "full") -> dict[str, Callable[[], str]]:
    """Get config templates."""
    return {
        "configs_init_py": lambda: CONFIGS_INIT_TEMPLATE,
        "configs_settings_py": lambda: get_settings_template(project_name, project_type),
        "configs_pyproject_py": lambda: CONFIGS_PYPROJECT_TEMPLATE,
    }
