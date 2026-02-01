"""
数据库扩展模块
"""

from contextvars import ContextVar, Token
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio.session import AsyncSession
from typing import Any, Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.sql import Select

from tomskit.sqlalchemy import Pagination, SelectPagination, SQLAlchemy
from tomskit.sqlalchemy.config import DatabaseConfig

class DatabaseSession(SQLAlchemy):
    database_session_ctx: ContextVar[Optional[AsyncSession]] = ContextVar('database_session', default=None)

    
    @property
    def session(self):
        s = self.database_session_ctx.get()
        if s is None:
            raise RuntimeError("Database session not initialized in this context.")
        return s
    
    @asynccontextmanager
    async def scope(self) -> AsyncGenerator[AsyncSession, None]:
        """
        通用的 Session 生命周期管理器（核心方案）。
        支持嵌套使用：即使一个请求开启多个 scope，reset(token) 也能保证上下文正确恢复。
        """
        session = self._SessionLocal() # type: ignore
        token = self.database_session_ctx.set(session)
        try:
            yield session
            # 注意：此处不自动 commit，遵循业务显式 commit 的习惯，或在外部 wrapper 统一处理
        finally:
            self.database_session_ctx.reset(token)
            await session.aclose()

    def create_session(self)-> AsyncSession:
        """
        创建一个新的会话并手动将其设置为ContextVar。
        """
        session = self._SessionLocal()  # type: ignore
        self.database_session_ctx.set(session)
        return session
    
    async def close_session(self, session):
        """
        Close the session and reset the context variable manually.
        """
        await session.aclose()
        self.database_session_ctx.set(None)

    def create_celery_session_token(self) -> tuple[AsyncSession, Token]:
        """为 Celery 提供的安全初始化方法"""
        session = self._SessionLocal() # type: ignore
        token = self.database_session_ctx.set(session)
        return session, token
    
    async def close_celery_session_token(self, session: AsyncSession, token: Token):
        """为 Celery 提供的安全关闭方法"""
        self.database_session_ctx.reset(token)
        await session.close()

    def initialize_session_pool(self, db_url: str, engine_options: Optional[dict[str, Any]] = None):
        """
        Initialize the database with the given database URL.
        Create the AsyncEngine and SessionLocal for database operations.
        """
        # Create the asynchronous engine
        default_options = {
            "pool_size": 10,        # 连接池大小 (Connection pool size) 默认10
            "max_overflow": 20,     # 允许的额外连接数 (Extra connections allowed) 默认20
            "pool_timeout": 20,     # 获取连接的超时时间 (Timeout for acquiring a connection) 默认30
            "pool_recycle": 1200,   # 空闲后回收连接的时间 (Recycle connections after being idle) 默认1200
            "pool_pre_ping": True,  # 极其重要：自动处理失效连接
            "echo": False,          # 调试时打印SQL查询 (Echo SQL queries for debugging) 默认False
            "echo_pool": False      # 调试时打印连接池信息 (Echo pool information for debugging) 默认False
        }
        
        engine_options = engine_options.copy() if engine_options else {}
        for key, default_val in default_options.items():
            if key not in engine_options:
                engine_options[key] = default_val

        self._engine = create_async_engine(db_url, **engine_options)

        # Create the session factory for AsyncSession
        self._SessionLocal = async_sessionmaker[AsyncSession](
            bind=self._engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )

    def create_session_pool_from_config(self, config: DatabaseConfig) -> None:
        """
        从 DatabaseConfig 配置创建数据库会话池
        
        使用配置中的 SQLALCHEMY_DATABASE_URI 和 SQLALCHEMY_ENGINE_OPTIONS
        来初始化数据库连接池。
        
        Args:
            config: 数据库配置对象，包含数据库连接信息和引擎选项
            
        Example:
            from tomskit.sqlalchemy.config import DatabaseConfig
            from tomskit.sqlalchemy.database import db
            
            config = DatabaseConfig()
            db.create_session_pool_from_config(config)
        """
        self.initialize_session_pool(
            db_url=config.SQLALCHEMY_DATABASE_URI,
            engine_options=config.SQLALCHEMY_ENGINE_OPTIONS
        )
    
    async def close_session_pool(self):
        if self._engine is not None:
            await self._engine.dispose()

    # Start of Selection
    def get_session_pool_info(self) -> dict:
        """
        获取当前数据库连接池的详细信息
        pool_size: 连接池大小
        pool_checkedin: 已检查入的连接数
        pool_checkedout: 已检查出的连接数
        pool_overflow: 溢出的连接数
        """
        if self._engine is None or self._engine.pool is None:
            return {"error": "数据库引擎未初始化"}
        
        return {
            "pool_size": self._engine.pool.size(),  # type: ignore
            "pool_checkedin": self._engine.pool.checkedin(), # type: ignore
            "pool_checkedout": self._engine.pool.checkedout(), # type: ignore
            "pool_overflow": self._engine.pool.overflow(), # type: ignore
        }


    

    def create_celery_session(self, config: DatabaseConfig) -> AsyncSession:
        """
        为 Celery worker 创建数据库会话
        
        使用 DatabaseConfig 配置初始化数据库连接池并创建会话。
        
        Args:
            config: 数据库配置对象
            
        Returns:
            AsyncSession: 数据库会话对象
            
        Example:
            from tomskit.sqlalchemy.config import DatabaseConfig
            from tomskit.sqlalchemy.database import db
            
            config = DatabaseConfig()
            session = db.create_celery_session(config)
        """
        self.initialize_session_pool(
            db_url=config.SQLALCHEMY_DATABASE_URI,
            engine_options=config.SQLALCHEMY_ENGINE_OPTIONS
        )
        session = self.create_session()
        return session

    async def close_celery_session(self, session):
        """
        关闭会话并手动重置上下文变量。
        """
        await session.aclose()
        self.database_session_ctx.set(None)
        if self._engine is not None:
            await self._engine.dispose()


    async def paginate(self,
        select: Select[Any],
        *,
        page: int | None = None,
        per_page: int | None = None,
        max_per_page: int | None = None,
        error_out: bool = True,
        count: bool = True,
    ) -> Pagination:
        """
        分页查询
        Args:
            select: 查询语句
            page: 页码
            per_page: 每页条数
            max_per_page: 最大每页条数
            error_out: 是否抛出错误
            count: 是否统计总数
        Returns:
        """
        return await SelectPagination(
            select=select,
            session=self.session,
            page=page,
            per_page=per_page,
            max_per_page=max_per_page,
            error_out=error_out,
            count=count,
        )  # type: ignore

db = DatabaseSession()
