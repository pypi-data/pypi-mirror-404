"""
FastAPI templates module
Contains all FastAPI related file templates.
"""

from typing import Callable

from .main import TEMPLATE as MAIN_TEMPLATE
from .app_factory import TEMPLATE as APP_FACTORY_TEMPLATE
from .app_init import TEMPLATE as APP_INIT_TEMPLATE
from .middleware_init import TEMPLATE as MIDDLEWARE_INIT_TEMPLATE
from .middleware_request_id import TEMPLATE as MIDDLEWARE_REQUEST_ID_TEMPLATE
from .middleware_resource_cleanup import TEMPLATE as MIDDLEWARE_RESOURCE_CLEANUP_TEMPLATE
from .controllers_init import TEMPLATE as CONTROLLERS_INIT_TEMPLATE
from .users_init import TEMPLATE as USERS_INIT_TEMPLATE
from .users_resources import TEMPLATE as USERS_RESOURCES_TEMPLATE
from .users_schemas import TEMPLATE as USERS_SCHEMAS_TEMPLATE
from .users_module import TEMPLATE as USERS_MODULE_TEMPLATE
from .models_init import TEMPLATE as MODELS_INIT_TEMPLATE
from .user_model import TEMPLATE as USER_MODEL_TEMPLATE
from .test_users import TEMPLATE as TEST_USERS_TEMPLATE


def get_fastapi_templates(project_name: str) -> dict[str, Callable[[], str]]:
    """Get FastAPI templates."""
    return {
        "main_py": lambda: MAIN_TEMPLATE.format(project_name=project_name),
        "app_factory_py": lambda: APP_FACTORY_TEMPLATE.format(project_name=project_name),
        "app_init_py": lambda: APP_INIT_TEMPLATE,
        "middleware_init_py": lambda: MIDDLEWARE_INIT_TEMPLATE,
        "middleware_request_id_py": lambda: MIDDLEWARE_REQUEST_ID_TEMPLATE,
        "middleware_resource_cleanup_py": lambda: MIDDLEWARE_RESOURCE_CLEANUP_TEMPLATE,
        "controllers_init_py": lambda: CONTROLLERS_INIT_TEMPLATE,
        "users_init_py": lambda: USERS_INIT_TEMPLATE,
        "users_resources_py": lambda: USERS_RESOURCES_TEMPLATE,
        "users_schemas_py": lambda: USERS_SCHEMAS_TEMPLATE,
        "users_module_py": lambda: USERS_MODULE_TEMPLATE,
        "models_init_py": lambda: MODELS_INIT_TEMPLATE,
        "user_model_py": lambda: USER_MODEL_TEMPLATE,
        "test_users_py": lambda: TEST_USERS_TEMPLATE,
    }
