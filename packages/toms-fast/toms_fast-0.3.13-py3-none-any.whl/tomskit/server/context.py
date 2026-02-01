"""
Server 上下文管理模块

负责管理服务器相关的上下文变量，如 request_id 等。
这些上下文变量可以在不同的执行上下文中（线程、协程）保持独立。
"""

from contextvars import ContextVar
from typing import Optional

from tomskit.logger.logger import ContextField

# === Request ID 上下文变量 ===
# HTTP 请求 ID，用于请求追踪
request_id_context_var: ContextVar[str] = ContextVar[str]("request_id", default="")

request_id_field: ContextField = ContextField("request_id", request_id_context_var)


def set_request_id(request_id: str) -> None:
    """
    设置当前请求的 Request ID
    
    Args:
        request_id: Request ID 字符串
    """
    request_id_context_var.set(request_id)


def get_request_id() -> str:
    """
    获取当前请求的 Request ID
    
    Returns:
        Request ID 字符串，如果未设置则返回空字符串
    """
    return request_id_context_var.get()


def reset_request_id() -> None:
    """
    重置当前请求的 Request ID
    """
    request_id_context_var.set("")


def get_request_id_via_getter() -> Optional[str]:
    """
    通过 ContextVar 获取当前的 request_id（用于 context_vars 配置）
    
    这个函数主要用于在 logger 配置的 context_vars 中使用。
    如果 request_id 为空字符串，返回 None，否则返回 request_id。
    
    Returns:
        request_id 字符串，如果未设置或为空则返回 None
    
    Example:
        from tomskit.server.context import get_request_id_via_getter
        
        context_vars = {
            "request_id": (None, get_request_id_via_getter),
        }
        configure_logging(logger_config, context_vars=context_vars)
    """
    request_id = request_id_context_var.get()
    if request_id:
        return request_id
    return None


def get_request_id_context_var() -> ContextVar[str]:
    """
    获取 request_id 的 ContextVar 实例
    
    Returns:
        request_id 的 ContextVar 实例
    
    Example:
        from tomskit.server.context import get_request_id_context_var
        
        context_vars = {
            "request_id": (get_request_id_context_var(), None),
        }
        configure_logging(logger_config, context_vars=context_vars)
    """
    return request_id_context_var
