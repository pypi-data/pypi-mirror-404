"""
Extension templates module
Contains all extension related file templates.
"""

from typing import Callable

from .ext_celery import TEMPLATE as EXT_CELERY_TEMPLATE
from .ext_database import TEMPLATE as EXT_DATABASE_TEMPLATE
from .ext_logger import TEMPLATE as EXT_LOGGER_TEMPLATE
from .ext_redis import TEMPLATE as EXT_REDIS_TEMPLATE
from .ext_warnings import TEMPLATE as EXT_WARNINGS_TEMPLATE
from .ext_modules import TEMPLATE as EXT_MODULES_TEMPLATE

def get_extension_templates(project_name: str, project_type: str = "full") -> dict[str, Callable[[], str]]:
    """Get extension templates."""
    def _get_extensions_init_py():
        return ""
    
    return {
        "extensions_init_py": _get_extensions_init_py,
        
        "extensions_logger_py": lambda: EXT_LOGGER_TEMPLATE,
        
        "extensions_warnings_py": lambda: EXT_WARNINGS_TEMPLATE,
        
        "extensions_database_py": lambda: EXT_DATABASE_TEMPLATE,
        
        "extensions_redis_py": lambda: EXT_REDIS_TEMPLATE,
        
        "extensions_celery_py": lambda: EXT_CELERY_TEMPLATE.format(project_name=project_name),
        
        "extensions_modules_py": lambda: EXT_MODULES_TEMPLATE,
    }
