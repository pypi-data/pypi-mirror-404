"""
Celery app template
Template for generating celery_app.py file.
"""

TEMPLATE = '''"""
{project_name} Celery 应用入口

此文件是 Celery worker 进程的入口点，用于创建和配置 Celery 应用实例。

注意：
- Celery worker 中使用的数据库连接池会在 worker 启动时自动创建，无需在此处创建
- 任务导入应在 ext_celery.py 的 init_worker() 函数中配置
- 此模块级别的 celery_app 实例会被 Celery worker 自动导入使用
"""

from tomskit.celery import AsyncCelery


def create_celery_app() -> AsyncCelery:
    """
    创建并初始化 Celery 应用实例

    初始化流程：
    1. 初始化日志系统（传入 task_id 上下文变量）
    2. 初始化 Celery 应用（worker 模式）

    Returns:
        AsyncCelery: 配置完成的 Celery 应用实例
    """
    # 先初始化日志系统，传入 task_id 的 getter 函数
    from extensions.ext_logger import init_app as init_logger
    from tomskit.celery.context import get_task_id_via_getter
    
    # 构建 context_vars，传入 task_id 的 getter
    context_vars = {{
        "task_id": (None, get_task_id_via_getter),
    }}
    init_logger(context_vars=context_vars)

    # 初始化 Celery 应用（worker 模式，app=None）
    from extensions.ext_celery import init_app as init_celery
    celery_app: AsyncCelery = init_celery()
    return celery_app


# Celery worker 会自动导入此模块级别的 celery_app 实例
celery_app = create_celery_app()

__all__ = ["celery_app"]
'''
