"""
Middleware init template
Template for generating app/middleware/__init__.py file.
"""

TEMPLATE = '''"""
中间件统一注册
"""

from tomskit.server import FastApp

from . import request_id, resource_cleanup
# 在这里导入更多中间件模块
# from . import cors, auth, rate_limit


def setup_middleware(app: FastApp):
    """
    统一注册所有中间件
    
    中间件执行顺序（从外到内，按注册顺序）：
    1. request_id - 请求 ID 追踪（最外层）
    2. resource_cleanup - 资源清理（最内层）
    
    注意：中间件的注册顺序很重要，后注册的中间件会更靠近应用核心
    """
    # 按顺序注册中间件
    request_id.setup(app)
    resource_cleanup.setup(app)
    
    # 注册更多中间件
    # cors.setup(app)
    # auth.setup(app)
    # rate_limit.setup(app)
'''
