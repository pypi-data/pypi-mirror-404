"""
Models init template
Template for generating app/models/__init__.py file.
"""

TEMPLATE = '''"""
数据库模型模块
导出所有模型和 Base
"""

from tomskit.sqlalchemy import SQLAlchemy

# 导入所有模型，确保它们被注册到 Base.metadata
from .user import User  # noqa: F401

# 导出 Base 供 Alembic 使用
Base = SQLAlchemy.Model
'''
