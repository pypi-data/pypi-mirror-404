# Logger 模块

基于 Python 标准库 `logging` 的日志配置与上下文注入，支持 FastAPI / Celery / Alembic 按类型一键配置、ContextVar 上下文字段、以及可选的异步队列写盘。

## 特性

- **按类型配置**：`app_type` 为 `fastapi` / `celery` / `alembic`，一键配置对应 logger（应用、访问、SQL、第三方降噪等）
- **上下文字段**：`ContextField` + `ContextRegistry`，用 ContextVar 向 LogRecord 注入 `request_id`、`prefix` 等，协程/线程安全
- **异步写盘**：可选 `AsyncQueueHandler`（内存队列 + 后台线程），解耦磁盘 I/O，由 `LOG_ASYNC_ENABLED` 控制
- **配置统一**：`LoggerConfig`（Pydantic Settings），支持环境变量与轮转、格式、级别等

## 快速开始

```python
from tomskit.logger import configure_logging, LoggerConfig

config = LoggerConfig(LOG_DIR="logs", LOG_LEVEL="INFO")
configure_logging(config, app_type="fastapi")

import logging
logger = logging.getLogger(__name__)
logger.info("hello")
```

## 安装与导入

```python
from tomskit.logger import (
    configure_logging,
    LoggerConfig,
    ContextField,
    ContextRegistry,
    AsyncQueueHandler,
    SafeFormatter,
    create_timed_handler,
    FastAPILogging,
    CeleryLogging,
    AlembicLogging,
    AppType,
)
```

## 配置类 LoggerConfig

继承自 Pydantic Settings，支持环境变量。常用字段：

| 分类     | 字段 | 说明 | 默认 |
|----------|------|------|------|
| 基础     | `LOG_DIR` | 日志目录 | `logs` |
|          | `LOG_NAME` | 应用日志文件名（无扩展名） | `apps` |
|          | `LOG_LEVEL` | 级别 | `INFO` |
|          | `LOG_FORMAT` | 格式，可用 `%(request_id)s`、`%(prefix)s` 等 | 见 config |
|          | `LOG_DATE_FORMAT` | 日期格式 | `%Y-%m-%d %H:%M:%S` |
|          | `LOG_BACKUP_COUNT` | 轮转保留份数，0 不保留 | `0` |
|          | `LOG_ROTATE_WHEN` | 轮转单位：`midnight` / D / H / M / S | `midnight` |
|          | `LOG_ROTATE_USE_UTC` | 轮转是否按 UTC 零点 | `False` |
| 异步队列 | `LOG_ASYNC_ENABLED` | 是否用 AsyncQueueHandler 写盘 | `False` |
|          | `LOG_ASYNC_QUEUE_SIZE` | 队列最大长度 | `8192` |
| 访问     | `LOG_ACCESS_NAME` / `LOG_ACCESS_FORMAT` | 访问日志 | `access` / Apache CLF |
| SQL      | `LOG_SQL_ENABLED` / `LOG_SQL_NAME` / `LOG_SQL_LEVEL` | SQL 独立文件 | 默认关 |
| Celery   | `LOG_CELERY_NAME` / `LOG_CELERY_FORMAT` / `LOG_CELERY_LEVEL` 等 | Celery 日志 | 见 config |
| 第三方   | `LOG_THIRD_PARTY_LEVEL` | 第三方库级别（降噪） | `WARNING` |

完整字段见 `tomskit.logger.config.LoggerConfig`。

## 入口函数 configure_logging

```python
def configure_logging(
    settings: LoggerConfig,
    context_registry: Optional[Iterable[ContextField]] = None,
    app_type: AppType = "fastapi",
) -> None
```

- **settings**：日志配置，一般来自环境或 `LoggerConfig()`。
- **context_registry**：上下文字段列表；为 `None` 时使用空 `ContextRegistry([])`，格式占位符缺字段时不会报错（SafeFormatter 兜底）。
- **app_type**：`"fastapi"` | `"celery"` | `"alembic"`  
  - `fastapi`：应用 + uvicorn.access + 可选 SQL，并配置第三方降噪  
  - `celery`：Celery 日志  
  - `alembic`：Alembic 日志  

## 上下文字段（ContextVar）

在请求/任务入口设置 ContextVar，通过 `ContextField` 注册后，每条日志会自动带上对应属性（如 `request_id`、`prefix`），供 `LOG_FORMAT` 中的 `%(request_id)s`、`%(prefix)s` 使用。

```python
from contextvars import ContextVar
from tomskit.logger import configure_logging, LoggerConfig, ContextField

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
prefix_var: ContextVar[str] = ContextVar("prefix", default="")

fields = [
    ContextField("request_id", request_id_var, "-"),
    ContextField("prefix", prefix_var, ""),
]
config = LoggerConfig(LOG_FORMAT="[%(asctime)s] [%(request_id)s] %(message)s")
configure_logging(config, context_registry=fields, app_type="fastapi")
```

在 FastAPI 中间件里设置：

```python
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request_id_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

app.add_middleware(RequestIdMiddleware)
```

## 异步队列写盘（AsyncQueueHandler）

当 `LOG_ASYNC_ENABLED=True` 时，`_file_logger` 会使用 `AsyncQueueHandler`：主线程只往内存队列写，后台线程负责落盘（并可选控制台），减少 I/O 对请求线程的影响。

- 队列大小由 `LOG_ASYNC_QUEUE_SIZE` 控制。
- 文件轮转与同步模式一致，复用 `create_timed_handler`（`LOG_ROTATE_WHEN` / `LOG_BACKUP_COUNT` / `LOG_ROTATE_USE_UTC`）。

也可单独使用：

```python
from tomskit.logger import AsyncQueueHandler, LoggerConfig

config = LoggerConfig()
handler = AsyncQueueHandler(
    filename=f"{config.LOG_DIR}/{config.LOG_NAME}.log",
    fmt=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    queue_size=config.LOG_ASYNC_QUEUE_SIZE,
    when=config.LOG_ROTATE_WHEN,
    backup_count=config.LOG_BACKUP_COUNT,
    utc=config.LOG_ROTATE_USE_UTC,
)
logging.getLogger("app").addHandler(handler)
```

## 按类型直接 setup

不需要统一入口时，可以按类型直接调用对应类：

```python
from tomskit.logger import (
    LoggerConfig,
    ContextRegistry,
    FastAPILogging,
    CeleryLogging,
    AlembicLogging,
)

config = LoggerConfig()
registry = ContextRegistry([...])  # 或 ContextRegistry([])

FastAPILogging(config, registry).setup()
# 或
CeleryLogging(config, registry).setup()
# 或
AlembicLogging(config, registry).setup()
```

## 扩展：自定义 Handler / Formatter

- **SafeFormatter**：格式时缺占位符不抛错，输出兜底信息。
- **create_timed_handler**：按时间轮转的文件 Handler，与当前轮转配置一致。
- **AsyncQueueHandler**：见上文；内部文件落地复用 `create_timed_handler`。

```python
from tomskit.logger import SafeFormatter, create_timed_handler, ContextFilter, ContextRegistry

fmt = SafeFormatter("%(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
handler = create_timed_handler("logs/app.log", "midnight", 30, False)
handler.setFormatter(fmt)
handler.addFilter(ContextFilter(registry))
logger.addHandler(handler)
```

## 环境变量

所有 `LoggerConfig` 字段均可通过环境变量覆盖，例如：

```bash
export LOG_DIR="logs"
export LOG_LEVEL="INFO"
export LOG_ASYNC_ENABLED="true"
export LOG_SQL_ENABLED="true"
```

```python
from tomskit.logger import configure_logging, LoggerConfig
config = LoggerConfig()  # 从环境读取
configure_logging(config, app_type="fastapi")
```

## 日志文件布局

典型目录结构（以默认名为例）：

```
logs/
├── apps.log          # 应用日志
├── access.log        # 访问日志（uvicorn）
├── sql.log           # SQL 日志（LOG_SQL_ENABLED=True 时）
├── celery.log        # Celery（app_type=celery 时）
└── alembic.log       # Alembic（app_type=alembic 时）
```

轮转后会有带日期的历史文件（如 `apps.log.2025-01-30`），由 `LOG_ROTATE_WHEN` / `LOG_BACKUP_COUNT` 控制。

## 注意事项

1. **先配置再打日志**：使用前需先调用 `configure_logging(...)` 或对应 `*Logging(...).setup()`。
2. **上下文需在入口设置**：request_id / prefix 等要在中间件或任务入口通过 ContextVar 设置，否则格式里对应占位符为默认值。
3. **格式占位符**：要在日志中看到上下文字段，`LOG_FORMAT` 里需包含对应占位符（如 `%(request_id)s`、`%(prefix)s`）。
4. **目录权限**：确保进程对 `LOG_DIR` 有写权限。
5. **异步队列**：`LOG_ASYNC_ENABLED=True` 时，关闭应用前队列会排空；若需严格顺序，可在 shutdown 时留短暂等待或使用 atexit 调用 handler.close()。

## 参考

- [Python logging](https://docs.python.org/3/library/logging.html)
- [logging.handlers — QueueHandler / QueueListener](https://docs.python.org/3/library/logging.handlers.html#queuehandler)
