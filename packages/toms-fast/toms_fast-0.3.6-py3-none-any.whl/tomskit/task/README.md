# AsyncTaskManager 使用指南

`AsyncTaskManager` 是一个基于 `asyncio.TaskGroup` 的简单异步任务管理器，支持批量和单次任务执行，并提供可选的数据库会话支持和丰富的日志功能。

## 功能概述

- **异步任务管理**：支持添加和并发执行多个异步任务。
- **数据库会话支持**：可选的数据库会话管理，适用于需要数据库交互的任务。
- **调试日志**：提供详细的任务执行日志，便于调试和性能分析。

## 类定义

### `AsyncTaskManager`

#### 初始化

```python
def __init__(self, task_name: str = __name__, db: bool = False, debug: bool = False)
```

- `task_name`：任务管理器的名称，用于日志记录。
- `db`：是否启用数据库会话。
- `debug`：是否启用调试日志。

#### 方法

- `add_task(target: TaskTarget, args: tuple = (), kwargs: Optional[dict[str, Any]] = None) -> None`
  - 添加一个异步任务。
  - `target`：异步任务函数。
  - `args`：传递给任务函数的位置参数。
  - `kwargs`：传递给任务函数的关键字参数。

- `add_tasks(targets: list[tuple[TaskTarget, tuple, Optional[dict[str, Any]]]]) -> None`
  - 批量添加多个异步任务。

- `async def run_all() -> None`
  - 并发执行所有添加的任务，捕获并收集异常。

- `async def run_task(target: TaskTarget, args: tuple = (), kwargs: Optional[dict[str, Any]] = None) -> Any`
  - 快捷单任务调用，执行单个任务并返回结果。

## 使用示例

```python
import asyncio

async def sample_task(x):
    await asyncio.sleep(1)
    return x * 2

async def main():
    manager = AsyncTaskManager(debug=True)
    manager.add_task(sample_task, args=(5,))
    await manager.run_all()
    print(manager.results)  # 输出: [10]

asyncio.run(main())
```

## 日志

- 启用 `debug` 模式后，任务的开始和结束时间将被记录。
- 异常将被记录并可供后续分析。

## 数据库支持

- 如果 `db` 参数为 `True`，任务执行时将自动创建和关闭数据库会话。 
