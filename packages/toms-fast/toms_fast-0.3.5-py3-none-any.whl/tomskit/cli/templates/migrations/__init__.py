"""
Migrations templates module
Contains all database migration related file templates.
"""

from typing import Callable

from .init import TEMPLATE as MIGRATIONS_INIT_TEMPLATE
from .alembic_ini import TEMPLATE as ALEMBIC_INI_TEMPLATE
from .env import TEMPLATE as ENV_TEMPLATE
from .script_mako import TEMPLATE as SCRIPT_MAKO_TEMPLATE
from .versions_init import TEMPLATE as VERSIONS_INIT_TEMPLATE


def get_migrations_templates(project_name: str) -> dict[str, Callable[[], str]]:
    """Get migrations templates."""
    return {
        "migrations_init_py": lambda: MIGRATIONS_INIT_TEMPLATE,
        "alembic_ini": lambda: ALEMBIC_INI_TEMPLATE.format(project_name=project_name),
        "migrations_env_py": lambda: ENV_TEMPLATE.format(project_name=project_name),
        "migrations_script_py_mako": lambda: SCRIPT_MAKO_TEMPLATE,
        "migrations_versions_init_py": lambda: VERSIONS_INIT_TEMPLATE,
    }
