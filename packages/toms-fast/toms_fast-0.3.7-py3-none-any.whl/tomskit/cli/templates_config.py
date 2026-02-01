"""
脚手架模板配置文件
定义项目目录结构和文件模板

注意：模板内容已迁移到 templates/ 目录下的模块化文件中：
- templates/base.py - 基础模板
- templates/extensions.py - 扩展模板
- templates/fastapi.py - FastAPI 模板
- templates/celery.py - Celery 模板
"""

from typing import Callable

from .templates import get_all_templates


# 基础目录结构（所有类型都需要）
BASE_DIRECTORIES = {
    "extensions": True,  # 扩展功能初始化目录
    "tests": True,
    "logs": False,
    "run": False,
    "configs": True,  # 配置目录
}

# FastAPI 相关目录
FASTAPI_DIRECTORIES = {
    "app/controllers": True,  # controllers 目录（__init__.py 为空）
    "app/controllers/users": True,
    "app/middleware": True,  # 中间件目录
    "app/models": True, # 数据库模型目录
    "app/schemas": True, # 数据模型验证目录
    "app/services": True, # 业务逻辑目录
    "app/utils": True, # 工具函数目录
    "migrations": True,  # 数据库迁移目录
    "migrations/versions": True,  # 迁移版本目录
}

# Celery 相关目录
CELERY_DIRECTORIES = {
    "tasks": True,
}


def get_directory_structure(project_type: str) -> dict[str, bool]:
    """根据项目类型返回目录结构"""
    directories = BASE_DIRECTORIES.copy()
    
    if project_type in ("fastapi", "full"):
        directories.update(FASTAPI_DIRECTORIES)
    
    if project_type in ("celery", "full"):
        directories.update(CELERY_DIRECTORIES)
    
    return directories


# 基础文件模板（所有类型都需要）
BASE_FILES = {
    "env.example": "env_example",
    ".gitignore": "gitignore",
    "pyproject.toml": "pyproject_toml",
    "README.md": "readme_md",  # 项目根目录的 README（简化版），backend 目录的 README 在 scaffold.py 中单独处理
    "extensions/__init__.py": "extensions_init_py",
    "extensions/ext_logger.py": "extensions_logger_py",
    "extensions/ext_warnings.py": "extensions_warnings_py",
    "extensions/ext_modules.py": "extensions_modules_py",
    "extensions/ext_celery.py": "extensions_celery_py",
    "extensions/ext_database.py": "extensions_database_py",
    "extensions/ext_redis.py": "extensions_redis_py",
    "tests/__init__.py": "tests_init_py",
    "configs/__init__.py": "configs_init_py",
    "configs/pyproject.py": "configs_pyproject_py",
    "configs/settings.py": "configs_settings_py",
}

# FastAPI 相关文件（按目录顺序排列）
FASTAPI_FILES = {
    # 根目录
    "main.py": "main_py",
    "app_factory.py": "app_factory_py",
    # app/ 目录
    "app/__init__.py": "app_init_py",
    # app/middleware/ 目录
    "app/middleware/__init__.py": "middleware_init_py",
    "app/middleware/request_id.py": "middleware_request_id_py",
    "app/middleware/resource_cleanup.py": "middleware_resource_cleanup_py",
    # app/controllers/ 目录
    "app/controllers/__init__.py": "controllers_init_py",
    # app/controllers/users/ 目录
    "app/controllers/users/__init__.py": "users_init_py",
    "app/controllers/users/resources.py": "users_resources_py",
    "app/controllers/users/schemas.py": "users_schemas_py",
    "app/controllers/users/module.py": "users_module_py",
    # app/models/ 目录
    "app/models/__init__.py": "models_init_py",
    "app/models/user.py": "user_model_py",
    # tests/ 目录
    "tests/test_users.py": "test_users_py",
    # migrations/ 目录
    "migrations/__init__.py": "migrations_init_py",
    "migrations/alembic.ini": "alembic_ini",
    "migrations/env.py": "migrations_env_py",
    "migrations/script.py.mako": "migrations_script_py_mako",
    "migrations/versions/__init__.py": "migrations_versions_init_py",
}

# Celery 相关文件
CELERY_FILES = {
    "celery_app.py": "celery_py",
    "extensions/ext_celery.py": "extensions_celery_py",
    "tasks/__init__.py": "tasks_init_py",
    "tasks/example_task.py": "example_task_py",
}


def get_file_templates(project_type: str) -> dict[str, str]:
    """根据项目类型返回文件模板映射"""
    files = BASE_FILES.copy()
    
    if project_type in ("fastapi", "full"):
        files.update(FASTAPI_FILES)
    
    if project_type in ("celery", "full"):
        files.update(CELERY_FILES)
    
    return files


# 文件模板内容生成函数
def get_template_functions(project_name: str, project_type: str = "full", description: str | None = None) -> dict[str, Callable[[], str]]:
    """
    根据项目类型返回所有模板函数
    
    注意：模板内容已迁移到 templates/ 模块中，此函数现在只是转发调用
    """
    return get_all_templates(project_name, project_type, description)
