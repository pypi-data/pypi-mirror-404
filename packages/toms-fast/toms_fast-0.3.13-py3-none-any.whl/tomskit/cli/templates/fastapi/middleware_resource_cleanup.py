"""
Middleware resource_cleanup template
Template for generating app/middleware/resource_cleanup.py file.
"""

TEMPLATE = '''"""
资源清理中间件
"""

from tomskit.server import FastApp, ResourceCleanupMiddleware
from tomskit.sqlalchemy.database import DatabaseCleanupStrategy
from tomskit.redis.redis_pool import RedisCleanupStrategy


def setup(app: FastApp):
    """
    配置资源清理中间件
    
    功能：
    - 自动清理数据库会话，防止资源泄漏
    - 自动清理 Redis 连接，防止资源泄漏
    - 在请求完成后自动执行清理，即使发生异常也会清理
    """
    app.add_middleware(
        ResourceCleanupMiddleware,
        strategies=[
            DatabaseCleanupStrategy(),
            RedisCleanupStrategy(),
        ]
    )
'''
