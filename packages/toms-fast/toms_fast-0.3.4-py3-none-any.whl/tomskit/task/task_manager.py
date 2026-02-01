import asyncio
import logging
import time
import uuid
from typing import Any, Awaitable, Callable, Optional
from tomskit.sqlalchemy.database import db as db_instance

logger = logging.getLogger(__name__)

# 异步任务目标类型
TaskTarget = Callable[..., Awaitable[Any]]

class AsyncTaskManager:
    """
    基于 asyncio.TaskGroup 的简单异步任务管理器，支持批量/单次任务执行，
    可选 db 会话，丰富日志
    """
    def __init__(
        self,
        task_name: str = __name__,
        db: bool = False,
        debug: bool = False,
    ):
        self.task_name = task_name
        self.db = db
        self.debug = debug
        # 存放任务生成器
        self.tasks: list[Callable[[], Awaitable[Any]]] = []
        # 存放结果和异常
        self.results: list[Any] = []
        self.exceptions: list[Exception] = []

    def add_task(
        self,
        target: TaskTarget,
        args: tuple = (),
        kwargs: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        添加一个异步任务，参数同 target 函数签名
        """
        if kwargs is None:
            kwargs = {}
        func_name = getattr(target, '__name__', repr(target))
        task_id = uuid.uuid4().hex[:8]

        async def wrapper() -> Any:
            session = None
            try:
                # 建会话
                if self.db:
                    session = db_instance.create_session()
                    logger.debug(f"[{self.task_name}] db session connected, task {task_id}")

                # 调试日志: 开始
                if self.debug:
                    logger.info(f"[{self.task_name}] Start {func_name}({task_id})")
                    start = time.perf_counter()

                # 执行目标协程
                result = await target(*args, **kwargs)
                self.results.append(result)

                # 调试日志: 完成
                if self.debug:
                    elapsed = time.perf_counter() - start
                    logger.info(f"[{self.task_name}] Finish {func_name}({task_id}) in {elapsed:.3f}s")

            except Exception:
                # 只日志，不立即收集，留给外层 TaskGroup 收集
                logger.exception(f"[{self.task_name}] Error in {func_name}({task_id})")
                raise

            finally:
                # 关闭会话
                if self.db and session is not None:
                    await db_instance.close_session(session)
                    logger.debug(f"[{self.task_name}] db session closed, task {task_id}")

        self.tasks.append(wrapper)

    def add_tasks(
        self,
        targets: list[tuple[TaskTarget, tuple, Optional[dict[str, Any]]]]
    ) -> None:
        """
        批量添加任务: [(func, args, kwargs), ...]
        """
        for target, args, kwargs in targets:
            self.add_task(target, args=args, kwargs=kwargs)

    async def run_all(self) -> None:
        """
        并发执行所有添加的任务，使用 asyncio.TaskGroup，
        捕获异常并收集，不向外抛出。
        """
        self.results.clear()
        self.exceptions.clear()
        try:
            async with asyncio.TaskGroup() as tg:
                for wrapper in self.tasks:
                    tg.create_task(wrapper())  # type: ignore
        except* Exception as eg:
            for e in eg.exceptions:
                if not isinstance(e, asyncio.CancelledError):
                    self.exceptions.append(e)

    async def run_task(
        self,
        target: TaskTarget,
        args: tuple = (),
        kwargs: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        快捷单任务调用
        """
        self.tasks.clear()
        self.results.clear()
        self.exceptions.clear()
        self.add_task(target, args=args, kwargs=kwargs)
        await self.run_all()
        if self.exceptions:
            raise self.exceptions[0]
        return self.results[0]
