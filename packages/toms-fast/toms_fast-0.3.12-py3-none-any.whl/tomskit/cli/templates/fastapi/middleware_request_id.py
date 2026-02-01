"""
Middleware request_id template
Template for generating app/middleware/request_id.py file.
"""

TEMPLATE = '''"""
请求 ID 追踪中间件
"""

from tomskit.server import FastApp, RequestIDMiddleware


def setup(app: FastApp):
    """
    配置请求 ID 追踪中间件
    
    功能：
    - 自动处理 X-Request-ID 请求头
    - 如果请求中没有 X-Request-ID，自动生成 UUID
    - 将请求 ID 设置到日志上下文中，用于分布式追踪
    - 在响应头中添加 X-Request-ID
    """
    app.add_middleware(RequestIDMiddleware)
'''
