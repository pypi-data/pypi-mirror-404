"""
Migrations env template
Template for generating migrations/env.py file.
"""

TEMPLATE = '''"""
Alembic {project_name} 环境配置文件, 用于数据库迁移
"""

import sys
import logging
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy import create_engine

from alembic import context

# 添加项目根目录到 Python 路径
# migrations 在 backend/migrations，backend 在项目根目录下
project_root = Path(__file__).parent.parent  # backend 目录
sys.path.insert(0, str(project_root))


# 导入应用配置
try:
    from configs import app_settings
except ImportError:
    print("⚠️  警告: 未找到 app_settings 配置")

# 导入数据库配置和模型
try:
    from app.models import Base  # 导入所有模型
    target_metadata = Base.metadata
except ImportError:
    # 如果模型还没有定义，创建一个空的 metadata
    from sqlalchemy import MetaData
    target_metadata = MetaData()
    print("⚠️  警告: 未找到 app.models，使用空的 metadata")

#

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

def setup_logging():
    """配置日志系统：确保日志目录存在，并设置日志输出到文件和屏幕"""
    # 确保 logs 目录存在（相对于 backend 目录）
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # 设置日志文件路径
    log_file_path = project_root / "logs" / "dberr.log"
    
    # Interpret the config file for Python logging.
    # This line sets up loggers basically.
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)
        
        # 创建文件处理器，用于将日志输出到文件
        file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.NOTSET)
        
        # 使用与控制台相同的格式化器
        formatter = logging.Formatter(
            fmt='%(levelname)-5.5s [%(name)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 为所有相关日志记录器添加文件处理器（同时保留控制台输出）
        for logger_name in ['', 'sqlalchemy.engine', 'alembic']:
            logger = logging.getLogger(logger_name)
            # 检查是否已经有相同的文件处理器（避免重复添加）
            has_file_handler = any(
                isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file_path.absolute())
                for h in logger.handlers
            )
            if not has_file_handler:
                logger.addHandler(file_handler)


# 初始化日志配置
setup_logging()

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():

    if app_settings is None:
        raise ValueError("app_settings 配置不可用")
    return app_settings.database.SQLALCHEMY_DATABASE_SYNC_URI


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_url()
    
    # 使用同步引擎（Alembic 需要同步连接）
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
