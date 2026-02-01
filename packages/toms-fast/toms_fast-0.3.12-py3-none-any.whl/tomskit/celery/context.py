"""
Celery 上下文管理模块

负责管理 Celery 任务相关的上下文变量，如 task_id 等。
这些上下文变量可以在不同的执行上下文中（线程、协程）保持独立。
"""

from contextvars import ContextVar
from typing import Optional

# === Task ID 上下文变量 ===
# Celery 任务 ID，用于任务追踪和日志关联
task_id_context_var: ContextVar[Optional[str]] = ContextVar("celery_task_id", default=None)

def set_task_id(task_id: str) -> None:
    """
    设置当前任务的 Task ID
    
    Args:
        task_id: Task ID 字符串
    """
    task_id_context_var.set(task_id)


def get_task_id() -> Optional[str]:
    """
    获取当前任务的 Task ID
    
    Returns:
        Task ID 字符串，如果未设置则返回 None
    """
    return task_id_context_var.get()


def clear_task_id() -> None:
    """
    清除当前任务的 Task ID
    """
    task_id_context_var.set(None)
