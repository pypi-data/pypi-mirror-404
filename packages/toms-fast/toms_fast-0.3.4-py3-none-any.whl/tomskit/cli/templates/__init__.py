"""
模板模块聚合
从各个子模块导入所有模板函数
"""

from typing import Callable

from . import base, extensions, fastapi, celery, migrations, configs


def get_all_templates(project_name: str, project_type: str = "full", description: str | None = None) -> dict[str, Callable[[], str]]:
    """
    获取所有模板函数
    
    Args:
        project_name: 项目名称
        project_type: 项目类型 (fastapi, celery, full)
        description: 项目描述（可选）
        
    Returns:
        模板函数字典
    """
    templates = {}
    
    # 基础模板（所有类型都需要）
    templates.update(base.get_base_templates(project_name, project_type, description))
    
    # 扩展模板（所有类型都需要）
    templates.update(extensions.get_extension_templates(project_name, project_type))
    
    # FastAPI 模板
    if project_type in ("fastapi", "full"):
        templates.update(fastapi.get_fastapi_templates(project_name))
    
    # Celery 模板
    if project_type in ("celery", "full"):
        templates.update(celery.get_celery_templates(project_name))
    
    # 数据库迁移模板（FastAPI 和 full 类型需要）
    if project_type in ("fastapi", "full"):
        templates.update(migrations.get_migrations_templates(project_name))
    
    # 配置模板（所有类型都需要）
    templates.update(configs.get_configs_templates(project_name, project_type))
    
    return templates
