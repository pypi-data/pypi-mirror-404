"""
App factory template
Template for generating app_factory.py file.
"""

TEMPLATE = '''"""
应用工厂函数
用于创建和初始化 FastAPI 应用
"""

import logging
import time
from contextlib import asynccontextmanager

from tomskit.redis import RedisClientWrapper
from tomskit.server import FastApp
from tomskit.sqlalchemy import db
from configs import app_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastApp):
    """
    应用生命周期管理
    
    管理应用的启动和关闭：
    - 启动时：扩展已在 create_app 中同步初始化
    - 关闭时：清理数据库连接池和 Redis 连接
    """
    # 启动阶段：扩展已在 create_app 中初始化，这里不需要额外操作
    yield
    # 关闭阶段：清理资源
    try:
        # 关闭数据库连接池
        await db.close_session_pool()
        logger.info("数据库连接池已关闭")
    except Exception as e:
        logger.error("关闭数据库连接池时出错: %s", e, exc_info=True)
    
    try:
        # 关闭 Redis 连接
        await RedisClientWrapper.shutdown()
        logger.info("Redis 连接已关闭")
    except Exception as e:
        logger.error("关闭 Redis 连接时出错: %s", e, exc_info=True)


def initialize_extensions(app: FastApp):
    """
    初始化所有扩展功能
    
    按 extensions 列表顺序初始化每个扩展，支持：
    - is_enabled() 检查扩展是否启用
    - init_app(app) 初始化扩展
    - 记录初始化时间
    
    Args:
        app: FastAPI 应用实例
    """
    from extensions import (
        ext_logger,
        ext_database,
        ext_redis,
        ext_celery,
        ext_modules,
        # 在这里导入更多扩展
        # ext_mail,
        # ext_storage,
        
    )
    
    # 扩展初始化顺序列表
    extensions = [
        ext_logger,
        ext_database,
        ext_redis,
        ext_celery,
        # 在这里添加更多扩展，按初始化顺序排列
        # ext_mail,
        # ext_storage,
        ext_modules
    ]
    
    for ext in extensions:
        short_name = ext.__name__.split(".")[-1]
        
        # 检查扩展是否启用
        is_enabled = ext.is_enabled() if hasattr(ext, "is_enabled") else True
        if not is_enabled:
            if app_settings.logger.LOG_LEVEL.upper() == "DEBUG":
                logger.info("Skipped %s", short_name)
            continue
        
        # 初始化扩展
        try:
            start_time = time.perf_counter()
            ext.init_app(app)
            end_time = time.perf_counter()
            if app_settings.logger.LOG_LEVEL.upper() == "DEBUG":
                logger.info("Loaded %s (%s ms)", short_name, round((end_time - start_time) * 1000, 2))
        except Exception as e:
            logger.error("Failed to load %s: %s", short_name, e, exc_info=True)
            raise


def create_app() -> FastApp:
    """
    创建并初始化 FastAPI 应用
    
    Returns:
        FastApp: 初始化完成的 FastAPI 应用实例
    """
    start_time = time.perf_counter()
    
    # 创建应用实例，传入 lifespan 管理生命周期
    app = FastApp(
        title=app_settings.project.name,
        description=app_settings.project.description,
        version=app_settings.project.version,
        lifespan=lifespan
    )
    
    # 设置应用根路径为 app_factory.py 所在的目录
    app.set_app_root_path(__file__)
    
    # 配置中间件
    # from app.middleware import setup_middleware
    # setup_middleware(app)
    
    # 初始化所有扩展
    initialize_extensions(app)
    
    end_time = time.perf_counter()
    if app_settings.logger.LOG_LEVEL.upper() == "DEBUG":
        logger.info("Finished create_app (%s ms)", round((end_time - start_time) * 1000, 2))
    
    return app

'''
