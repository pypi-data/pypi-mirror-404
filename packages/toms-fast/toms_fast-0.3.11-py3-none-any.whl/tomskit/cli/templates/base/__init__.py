"""
Base templates module
Contains all base file templates required for all project types.
"""

from typing import Callable, Optional

from .readme import get_readme_content, get_backend_readme_content
from .env_example import TEMPLATE as ENV_EXAMPLE_TEMPLATE
from .gitignore import TEMPLATE as GITIGNORE_TEMPLATE
from .pyproject_toml import TEMPLATE as PYPROJECT_TOML_TEMPLATE


def get_base_templates(project_name: str, project_type: str = "full", description: Optional[str] = None) -> dict[str, Callable[[], str]]:
    """Get base templates."""
    return {
        "env_example": lambda: ENV_EXAMPLE_TEMPLATE.format(project_name=project_name),
        "gitignore": lambda: GITIGNORE_TEMPLATE,
        "pyproject_toml": lambda: PYPROJECT_TOML_TEMPLATE.format(
            project_name=project_name,
            description=description if description else "基于 toms-fast 的 FastAPI 应用"
        ),
        "readme_md": lambda: get_readme_content(project_name, project_type),
        "backend_readme_md": lambda: get_backend_readme_content(project_name, project_type),
        "tests_init_py": lambda: "",
    }
