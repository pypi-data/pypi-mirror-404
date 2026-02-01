from __future__ import annotations

import os
import asyncio
import logging
import threading
import typing as t
from contextvars import ContextVar
from functools import wraps

from celery import Celery, shared_task
from celery.signals import task_prerun, task_postrun, worker_process_init, worker_process_shutdown

from tomskit.celery.config import CeleryConfig
from tomskit.celery.orjson_serializer import register_orjson_serializer
from tomskit.redis.redis_pool import RedisConfig, redis_client
from tomskit.sqlalchemy import DatabaseConfig
from tomskit.sqlalchemy.database import db

# from tomskit.celery.context import task_id_context_var

celery_context: ContextVar["AsyncCelery" | None] = ContextVar(
    "tomskit_celery_context_runtime", default=None
)

logger = logging.getLogger(__name__)

class AsyncRuntime:
    """
    Async runtime environment providing a shared event loop for Celery workers.
    
    Features:
    - Runs a persistent event loop in a background thread
    - Supports cross-thread async coroutine execution
    - Automatically manages database session creation and cleanup
    
    Usage:
        from tomskit.celery import AsyncCelery
        
        celery_app = AsyncCelery('myapp', ...)
        
        @celery_app.task
        def my_task():
            async def async_work():
                return "result"
            return AsyncRuntime.run(async_work())
    """
    _loop: t.Optional[asyncio.AbstractEventLoop] = None
    _initialized: bool = False
    _celery_app: t.Optional["AsyncCelery"] = None
    _thread: t.Optional[threading.Thread] = None
    _lock = threading.Lock()

    @classmethod
    def init(cls, celery_app: "AsyncCelery"):
        """
        Initialize the async runtime environment.
        
        Args:
            celery_app: Celery application instance
        """
        with cls._lock:
            if cls._initialized:
                return
            cls._celery_app = celery_app

            loop_ready = threading.Event()
            cls._loop = asyncio.new_event_loop()

            assert cls._loop is not None

            def loop_runner():
                asyncio.set_event_loop(cls._loop)
                loop_ready.set()
                try:
                    cls._loop.run_forever()
                except Exception:
                    import traceback
                    traceback.print_exc()
                finally:
                    pass

            cls._thread = threading.Thread(
                target=loop_runner,
                name="async-runtime-loop",
                daemon=True,
            )

            cls._thread.start()

            if not loop_ready.wait(timeout=5):
                if cls._thread and not cls._thread.is_alive():
                    raise RuntimeError("event loop thread start fail.")
                else:
                    raise RuntimeError("event loop initialization timeout")

            if cls._thread and not cls._thread.is_alive():
                raise RuntimeError("event loop thread is not alive.")

            async def init_resources():
                await asyncio.sleep(0.01)
                db.create_session_pool_from_config(celery_app.db_config)
                redis_client.initialize(celery_app.redis_config)
            
            future = asyncio.run_coroutine_threadsafe(
                init_resources(),
                cls._loop
            )
            future.result(timeout=5)

            cls._initialized = True

    @classmethod
    def run(cls, coro):
        """
        Run a coroutine in the shared event loop.
        
        Args:
            coro: Coroutine to run
            
        Returns:
            Result of the coroutine
            
        Raises:
            RuntimeError: If AsyncRuntime is not initialized or event loop is closed
        """
        # 延迟初始化：如果 worker_process_init 信号丢失，在这里自动初始化
        if not cls._initialized or not cls._loop:
            celery_app = celery_context.get()
            if celery_app is None:
                raise RuntimeError(
                    "AsyncRuntime not initialized and celery_context is not set. "
                    "Please ensure AsyncCelery is created first."
                )
            # 尝试自动初始化（使用锁确保线程安全）
            with cls._lock:
                # 双重检查：可能在获取锁的过程中其他线程已经初始化了
                if not cls._initialized or not cls._loop:
                    logger.warning(
                        f"AsyncRuntime not initialized when run() called (pid: {os.getpid()}). "
                        "Auto-initializing now. This may happen if worker_process_init signal was missed."
                    )
                    cls.init(celery_app)
        
        if cls._loop.is_closed():
            raise RuntimeError("Event loop is closed")

        async def run_coro():
            
            session = None
            token = None

            session, token = db.create_celery_session_token()
            try:
                result = await coro
                return result
            finally:
                if session and token:
                    await db.close_celery_session_token(session, token)

        future = asyncio.run_coroutine_threadsafe(run_coro(), cls._loop)
        result = future.result(timeout=1800)  # 任务最长 30 分钟超时
        return result 

    @classmethod
    def shutdown(cls):
        """
        Shutdown the async runtime environment and cleanup resources.
        """
        with cls._lock:
            if not cls._initialized or not cls._loop:
                return

            async def _shutdown():
                try:
                    await db.close_session_pool()
                except Exception :
                    pass
                try:
                    await redis_client.shutdown()
                except Exception:
                    pass
                cls._loop.stop()
        
            try:
                if not cls._loop.is_closed():
                    asyncio.run_coroutine_threadsafe(_shutdown(), cls._loop).result(timeout=10)
            except Exception:
                pass
            
            if cls._thread and cls._thread.is_alive():
                cls._thread.join(timeout=5)
            
            cls._loop = None
            cls._thread = None
            cls._initialized = False


class AsyncCelery(Celery):
    """
    Async Celery application with task ID support and automatic worker initialization.
    """
        
    def __init__(
        self, 
        *args: t.Any, 
        config: t.Optional[CeleryConfig] = None,
        database: t.Optional[DatabaseConfig] = None,
        redis: t.Optional[RedisConfig] = None,
        **kwargs: t.Any
    ) -> None:
        """
        Initialize async Celery application.
        
        Args:
            *args: Positional arguments passed to Celery
            config: Celery configuration object, uses default if not provided
            database: Database configuration object, uses default if not provided
            redis: Redis configuration object, uses default if not provided
            **kwargs: Keyword arguments passed to Celery
        """
        super().__init__(*args, **kwargs)
        self.config: CeleryConfig = config if config is not None else CeleryConfig()
        self.db_config: DatabaseConfig = database if database is not None else DatabaseConfig()
        self.redis_config: RedisConfig = redis if redis is not None else RedisConfig()
        self._worker_init_handlers: list[t.Callable] = []
        self._worker_shutdown_handlers: list[t.Callable] = []
        self._task_prerun_handlers: list[t.Callable] = []
        self._task_postrun_handlers: list[t.Callable] = []
        celery_context.set(self)
        
        self._setup_orjson_serializer()
        self._setup_worker_init_and_shutdown()
        self._setup_task_prerun_and_postrun()

    def register_worker_init_handler(self, handler: t.Callable) -> None:
        self._worker_init_handlers.append(handler)

    def register_worker_shutdown_handler(self, handler: t.Callable) -> None:
        self._worker_shutdown_handlers.append(handler)

    def register_task_prerun_handler(self, handler: t.Callable) -> None:
        self._task_prerun_handlers.append(handler)

    def register_task_postrun_handler(self, handler: t.Callable) -> None:
        self._task_postrun_handlers.append(handler)

    def _setup_orjson_serializer(self) -> None:
        """
        Setup orjson serializer support.
        
        Registers orjson serializer with Kombu if orjson is available.
        This allows using 'orjson' as a serializer option in Celery configuration.
        """
        try:
            register_orjson_serializer()
        except ImportError:
            # orjson is optional, so we silently ignore if it's not installed
            # Users can still use other serializers like 'json'
            pass

    def _setup_worker_init_and_shutdown(self) -> None:
        """
        Setup worker initialization and shutdown handlers.
        """

        def on_worker_process_init(**kwargs):
            """Worker process initialization handler."""
            for handler in self._worker_init_handlers:
                handler(**kwargs)
        
        def on_worker_shutting_down(**kwargs):
            """Worker shutdown handler."""
            for handler in self._worker_shutdown_handlers:
                handler(**kwargs)

        worker_process_init.connect(on_worker_process_init, weak=False)
        worker_process_shutdown.connect(on_worker_shutting_down, weak=False)

    def _setup_task_prerun_and_postrun(self) -> None:
        """
        Setup task prerun and postrun handlers.
        """
        def on_task_prerun(**kwargs):
            """Task prerun handler."""
            for handler in self._task_prerun_handlers:
                handler(**kwargs)

        def on_task_postrun(**kwargs):
            """Task postrun handler."""
            for handler in self._task_postrun_handlers:
                handler(**kwargs)

        task_prerun.connect(on_task_prerun, weak=False)
        task_postrun.connect(on_task_postrun, weak=False)


def async_shared_task(*task_args, **task_kwargs):
    """
    Decorator for async Celery tasks that simplifies async task creation.
    
    Automatically uses AsyncRuntime to run async functions without manually
    calling AsyncRuntime.run().
    
    Supports both usage patterns:
    - @async_shared_task (no arguments)
    - @async_shared_task(name="my_task", queue="default") (with arguments)
    
    Args:
        *task_args: Positional arguments passed to shared_task
        **task_kwargs: Keyword arguments passed to shared_task
    
    Returns:
        Decorator function or decorated function (if called without arguments)
    
    Example:
        ```python
        from tomskit.celery import async_shared_task
        
        # With arguments
        @async_shared_task(name="my_task", queue="default")
        async def my_async_task(arg1, arg2):
            return "result"
        
        # Without arguments
        @async_shared_task
        async def my_simple_task():
            return "done"
        
        my_async_task.delay(arg1, arg2)
        my_simple_task.delay()
        ```
    """

    task_kwargs.setdefault("bind", True)

    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                f"{func.__name__} must be an async function (coroutine function)"
            )

        @wraps(func)
        def wrapper(task_instance, *args, **kwargs):
            coro = func(*args, **kwargs)
            return AsyncRuntime.run(coro)
        
        return shared_task(*task_args, **task_kwargs)(wrapper)
    
    # 处理不带参数调用 @async_shared_task 的情况
    if len(task_args) == 1 and callable(task_args[0]) and not task_kwargs:
        return decorator(task_args[0])
    
    return decorator
