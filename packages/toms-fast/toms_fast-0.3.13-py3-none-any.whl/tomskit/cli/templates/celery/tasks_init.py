"""
Tasks init template
Template for generating tasks/__init__.py file.
"""

TEMPLATE = '''"""
Celery 任务模块
"""

# 导入所有任务，确保它们被注册到 Celery 应用
from . import example_task  # noqa: F401

__all__ = ["example_task"]
'''
