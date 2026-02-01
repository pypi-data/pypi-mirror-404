# Celery Module Guide

该模块提供了基于 Celery 的异步任务执行框架，支持在 Celery 任务中运行异步函数，并自动管理数据库会话和资源。

## 模块概述

Celery 模块扩展了标准 Celery 应用，提供了完整的异步任务支持。主要特性包括：

- ⚡ **异步任务支持**：在 Celery 任务中运行异步函数
- 🔄 **自动会话管理**：自动创建和关闭数据库会话
- 🛠️ **配置管理**：使用 `CeleryConfig` 统一管理所有配置
- 🔧 **上下文管理**：使用 `ContextVar` 管理 Celery 应用上下文
- 📦 **自动资源初始化**：在 worker 启动时自动初始化数据库连接池和 Redis 客户端
- 🎯 **任务 ID 追踪**：自动在日志中注入任务 ID
- 🚀 **共享事件循环**：通过 `AsyncRuntime` 提供高效的事件循环管理
- 📝 **简化装饰器**：`async_shared_task` 装饰器简化异步任务定义

**Import Path:**
```python
from tomskit.celery import (
    AsyncCelery,
    AsyncRuntime,
    AsyncTaskRunner,
    CeleryConfig,
    async_shared_task,
    register_orjson_serializer
)
```

## 核心类和函数

### CeleryConfig

Celery 配置类，继承自 `TomsKitBaseSettings`，用于管理 Celery 应用的完整配置。支持 Redis 作为 broker 和 backend，以及将结果存储到数据库。

```python
class CeleryConfig(TomsKitBaseSettings):
    # Redis Broker 配置
    CELERY_BROKER_REDIS_HOST: str = "localhost"
    CELERY_BROKER_REDIS_PORT: PositiveInt = 6379
    CELERY_BROKER_REDIS_USERNAME: Optional[str] = None
    CELERY_BROKER_REDIS_PASSWORD: Optional[str] = None
    CELERY_BROKER_REDIS_DB: NonNegativeInt = 0
    
    # Result Backend 配置
    CELERY_RESULT_BACKEND_TYPE: str = "redis"  # 'redis' 或 'database'
    
    # Celery 任务配置
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    
    # 数据库配置（用于 worker 和结果存储）
    CELERY_DB_HOST: str = "localhost"
    CELERY_DB_PORT: PositiveInt = 5432
    CELERY_DB_USERNAME: str = ""
    CELERY_DB_PASSWORD: str = ""
    CELERY_DB_DATABASE: str = "tomskitdb"
    
    # Redis 配置（用于 worker）
    CELERY_WORKER_REDIS_HOST: str = "localhost"
    CELERY_WORKER_REDIS_PORT: PositiveInt = 6379
    
    # 计算属性
    @property
    def CELERY_BROKER_URL(self) -> str: ...
    @property
    def CELERY_RESULT_BACKEND(self) -> str: ...
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str: ...
```

**功能特性：**
- 支持 Redis 作为 broker 和 backend
- 支持数据库作为结果后端（将结果存储到数据库）
- 自动生成 broker 和 backend URL
- 支持通过环境变量配置
- 提供数据库和 Redis 配置（用于 worker）

### AsyncCelery

异步 Celery 应用类，继承自 `Celery`，提供自动资源管理和任务 ID 追踪。

```python
class AsyncCelery(Celery):
    def __init__(
        self,
        *args: Any,
        config: Optional[CeleryConfig] = None,
        database: Optional[DatabaseConfig] = None,
        redis: Optional[RedisConfig] = None,
        **kwargs: Any
    ) -> None: ...
    
    config: CeleryConfig
    db_config: DatabaseConfig
    redis_config: RedisConfig
    task_id_context: ContextVar[Optional[str]]
```

**功能特性：**
- 继承自标准 Celery 类，兼容所有 Celery 功能
- 使用 `ContextVar` 管理应用上下文，确保线程安全
- 自动设置 orjson 序列化器（如果可用）
- 自动设置任务 ID 支持（用于日志追踪）
- 自动设置 worker 初始化和关闭处理器
- 在 worker 启动时自动初始化数据库连接池和 Redis 客户端

**属性说明：**
- `config`: Celery 配置对象
- `db_config`: 数据库配置对象
- `redis_config`: Redis 配置对象
- `task_id_context`: 任务 ID 上下文变量（用于日志）

### AsyncRuntime

异步运行时环境，提供共享的事件循环用于 Celery workers。

```python
class AsyncRuntime:
    @classmethod
    def init(cls, celery_app: AsyncCelery) -> None: ...
    
    @classmethod
    def run(cls, coro: Coroutine) -> Any: ...
    
    @classmethod
    def shutdown(cls) -> None: ...
```

**功能特性：**
- 在后台线程中运行持久化的事件循环
- 支持跨线程异步协程执行
- 自动管理数据库会话创建和清理
- 在 worker 启动时自动初始化，在 worker 关闭时自动清理

**使用场景：**
- 在 Celery 任务中运行异步函数
- 需要共享事件循环的场景
- 需要自动会话管理的场景

### AsyncTaskRunner

异步任务运行器，用于在 Celery 任务中执行异步函数。

```python
class AsyncTaskRunner:
    def __init__(
        self,
        async_task: Callable[..., Awaitable[Any]],
        use_db: bool = True,
        use_redis: bool = False
    ) -> None: ...
    
    def run(self, *args: Any, **kwargs: Any) -> Any: ...
```

**功能特性：**
- 在 Celery 任务中运行异步函数
- 自动创建和关闭数据库会话（如果启用）
- 检查 Redis 客户端是否已初始化（如果启用）
- 使用 `asyncio.run` 执行异步任务
- 确保资源正确释放，即使发生异常

**参数说明：**
- `async_task`: 要执行的异步任务函数（必须是协程函数）
- `use_db`: 是否启用数据库 session 管理，默认为 `True`
- `use_redis`: 是否检查 Redis 客户端，默认为 `False`（仅检查，不管理）

### async_shared_task

装饰器，用于简化异步 Celery 任务的创建。

```python
@async_shared_task(name="my_task", queue="default")
async def my_async_task(arg1, arg2):
    return "result"

# 或者不带参数
@async_shared_task
async def my_simple_task():
    return "done"
```

**功能特性：**
- 自动使用 `AsyncRuntime` 运行异步函数
- 无需手动调用 `AsyncRuntime.run()`
- 支持所有 `shared_task` 的参数
- 支持带参数和不带参数两种用法

## 完整使用示例

### 基础使用：使用 CeleryConfig

```python
from tomskit.celery import AsyncCelery, CeleryConfig
from tomskit.sqlalchemy import DatabaseConfig
from tomskit.redis import RedisConfig

# 创建配置对象
celery_config = CeleryConfig(
    CELERY_BROKER_REDIS_HOST='localhost',
    CELERY_BROKER_REDIS_PORT=6379,
    CELERY_BROKER_REDIS_DB=0,
    CELERY_RESULT_BACKEND_TYPE='redis',
    CELERY_RESULT_BACKEND_REDIS_HOST='localhost',
    CELERY_RESULT_BACKEND_REDIS_PORT=6379,
    CELERY_RESULT_BACKEND_REDIS_DB=1,
    CELERY_TASK_SERIALIZER='json',
    CELERY_RESULT_SERIALIZER='json',
)

# 创建数据库和 Redis 配置
db_config = DatabaseConfig()
redis_config = RedisConfig()

# 创建 Celery 应用
celery_app = AsyncCelery(
    'myapp',
    config=celery_config,
    database=db_config,
    redis=redis_config
)

# 应用 Celery 配置
celery_app.config_from_object(celery_config)
```

### 使用 async_shared_task 定义任务（推荐）

```python
from tomskit.celery import async_shared_task
from tomskit.sqlalchemy.database import db
from tomskit.sqlalchemy import User

# 使用装饰器定义异步任务
@async_shared_task(name="create_user", queue="default")
async def create_user_task(name: str, email: str):
    """创建用户的异步任务"""
    new_user = User(name=name, email=email)
    try:
        db.session.add(new_user)
        await db.session.commit()
        await db.session.refresh(new_user)
        return {
            "success": True,
            "user_id": new_user.id,
            "message": f"User {name} created successfully"
        }
    except Exception as e:
        await db.session.rollback()
        return {
            "success": False,
            "error": str(e)
        }

# 调用任务
create_user_task.delay("John Doe", "john@example.com")
```

### 使用 AsyncRuntime.run() 定义任务

```python
from tomskit.celery import AsyncCelery, AsyncRuntime
from tomskit.sqlalchemy.database import db
from tomskit.sqlalchemy import User
from celery import shared_task

@shared_task(name="create_user", queue="default")
def create_user_task(name: str, email: str):
    """创建用户的 Celery 任务"""
    async def async_create_user():
        new_user = User(name=name, email=email)
        try:
            db.session.add(new_user)
            await db.session.commit()
            await db.session.refresh(new_user)
            return {
                "success": True,
                "user_id": new_user.id,
                "message": f"User {name} created successfully"
            }
        except Exception as e:
            await db.session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    return AsyncRuntime.run(async_create_user())

# 调用任务
create_user_task.delay("John Doe", "john@example.com")
```

### 使用 AsyncTaskRunner 定义任务

```python
from tomskit.celery import AsyncTaskRunner
from tomskit.sqlalchemy.database import db
from tomskit.sqlalchemy import User
from celery import shared_task

@shared_task(name="create_user", queue="default")
def create_user_task(name: str, email: str):
    """创建用户的 Celery 任务"""
    async def async_create_user():
        new_user = User(name=name, email=email)
        try:
            db.session.add(new_user)
            await db.session.commit()
            await db.session.refresh(new_user)
            return {
                "success": True,
                "user_id": new_user.id,
                "message": f"User {name} created successfully"
            }
        except Exception as e:
            await db.session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    task = AsyncTaskRunner(async_create_user)
    return task.run(name, email)

# 调用任务
create_user_task.delay("John Doe", "john@example.com")
```

### 使用 Redis 的任务

```python
from tomskit.celery import async_shared_task
from tomskit.redis.redis_pool import redis_client
from tomskit.sqlalchemy.database import db
from tomskit.sqlalchemy import User

@async_shared_task(name="cache_user_data", queue="cache")
async def cache_user_data_task(user_id: int):
    """缓存用户数据的异步任务"""
    # 从数据库获取用户
    user = await db.session.get(User, user_id)
    if user:
        # 缓存到 Redis
        await redis_client.setex(
            f"user:{user_id}",
            3600,  # 1 小时过期
            str(user.id)
        )
        return f"User {user_id} cached successfully"
    return f"User {user_id} not found"

# 调用任务
cache_user_data_task.delay(123)
```

### 不使用数据库的任务

```python
from tomskit.celery import async_shared_task
from tomskit.redis.redis_pool import redis_client

@async_shared_task(name="simple_task", queue="default")
async def simple_task(message: str):
    """简单的异步任务，不使用数据库"""
    # 只使用 Redis，不使用数据库
    await redis_client.set("message", message)
    return f"Message '{message}' stored"

# 调用任务
simple_task.delay("Hello World")
```

### 使用数据库作为结果后端

```python
from tomskit.celery import AsyncCelery, CeleryConfig
from tomskit.sqlalchemy import DatabaseConfig
from tomskit.redis import RedisConfig

# 创建配置，使用数据库作为结果后端
celery_config = CeleryConfig(
    CELERY_BROKER_REDIS_HOST='localhost',
    CELERY_BROKER_REDIS_PORT=6379,
    CELERY_BROKER_REDIS_DB=0,
    CELERY_RESULT_BACKEND_TYPE='database',  # 使用数据库
    CELERY_RESULT_BACKEND_DATABASE_URI_SCHEME='mysql',
    CELERY_DB_HOST='localhost',
    CELERY_DB_PORT=3306,
    CELERY_DB_USERNAME='user',
    CELERY_DB_PASSWORD='password',
    CELERY_DB_DATABASE='mydb',
)

db_config = DatabaseConfig()
redis_config = RedisConfig()

# 创建 Celery 应用
celery_app = AsyncCelery(
    'myapp',
    config=celery_config,
    database=db_config,
    redis=redis_config
)

# 应用配置
celery_app.config_from_object(celery_config)
```

### 使用环境变量配置

```python
import os
from tomskit.celery import AsyncCelery, CeleryConfig
from tomskit.sqlalchemy import DatabaseConfig
from tomskit.redis import RedisConfig

# 从环境变量加载配置
celery_config = CeleryConfig()  # 自动从环境变量读取
db_config = DatabaseConfig()     # 自动从环境变量读取
redis_config = RedisConfig()    # 自动从环境变量读取

# 创建 Celery 应用
celery_app = AsyncCelery(
    'myapp',
    config=celery_config,
    database=db_config,
    redis=redis_config
)

# 应用配置
celery_app.config_from_object(celery_config)
```

## 配置说明

### CeleryConfig 配置项

#### Redis Broker 配置

- `CELERY_BROKER_REDIS_HOST`: Redis broker 主机地址，默认 `"localhost"`
- `CELERY_BROKER_REDIS_PORT`: Redis broker 端口，默认 `6379`
- `CELERY_BROKER_REDIS_USERNAME`: Redis broker 用户名（可选）
- `CELERY_BROKER_REDIS_PASSWORD`: Redis broker 密码（可选）
- `CELERY_BROKER_REDIS_DB`: Redis broker 数据库编号，默认 `0`
- `CELERY_USE_SENTINEL`: 是否使用 Redis Sentinel，默认 `False`
- `CELERY_SENTINEL_MASTER_NAME`: Sentinel master 名称（使用 Sentinel 时）
- `CELERY_SENTINEL_PASSWORD`: Sentinel 密码（使用 Sentinel 时）
- `CELERY_SENTINEL_SOCKET_TIMEOUT`: Sentinel socket 超时时间（秒），默认 `0.1`

#### Result Backend 配置

- `CELERY_RESULT_BACKEND_TYPE`: 结果后端类型，`"redis"` 或 `"database"`，默认 `"redis"`

**Redis Backend 配置（当 `CELERY_RESULT_BACKEND_TYPE='redis'` 时）：**
- `CELERY_RESULT_BACKEND_REDIS_HOST`: Redis backend 主机地址，默认 `"localhost"`
- `CELERY_RESULT_BACKEND_REDIS_PORT`: Redis backend 端口，默认 `6379`
- `CELERY_RESULT_BACKEND_REDIS_USERNAME`: Redis backend 用户名（可选）
- `CELERY_RESULT_BACKEND_REDIS_PASSWORD`: Redis backend 密码（可选）
- `CELERY_RESULT_BACKEND_REDIS_DB`: Redis backend 数据库编号，默认 `1`

**Database Backend 配置（当 `CELERY_RESULT_BACKEND_TYPE='database'` 时）：**
- `CELERY_RESULT_BACKEND_DATABASE_URI_SCHEME`: 数据库 URI 协议，默认 `"mysql"`

#### Celery 任务配置

- `CELERY_TASK_SERIALIZER`: 任务序列化格式，支持 `"json"`、`"orjson"`，默认 `"json"`
- `CELERY_RESULT_SERIALIZER`: 结果序列化格式，支持 `"json"`、`"orjson"`，默认 `"json"`
- `CELERY_ACCEPT_CONTENT`: 接受的内容类型，默认 `["json"]`
- `CELERY_TIMEZONE`: 时区设置，默认 `"UTC"`
- `CELERY_ENABLE_UTC`: 是否启用 UTC，默认 `True`
- `CELERY_TASK_TRACK_STARTED`: 是否跟踪任务开始，默认 `True`
- `CELERY_TASK_TIME_LIMIT`: 任务硬时间限制（秒），默认 `None`
- `CELERY_TASK_SOFT_TIME_LIMIT`: 任务软时间限制（秒），默认 `None`
- `CELERY_TASK_IGNORE_RESULT`: 是否忽略任务结果，默认 `False`
- `CELERY_RESULT_EXPIRES`: 结果过期时间（秒），默认 `None`

#### 数据库配置（用于 worker 和结果存储）

- `CELERY_DB_HOST`: 数据库主机地址，默认 `"localhost"`
- `CELERY_DB_PORT`: 数据库端口，默认 `5432`
- `CELERY_DB_USERNAME`: 数据库用户名，默认 `""`
- `CELERY_DB_PASSWORD`: 数据库密码，默认 `""`
- `CELERY_DB_DATABASE`: 数据库名称，默认 `"tomskitdb"`
- `CELERY_DB_CHARSET`: 数据库字符集，默认 `""`
- `CELERY_DB_EXTRAS`: 数据库额外参数，默认 `""`
- `CELERY_SQLALCHEMY_DATABASE_URI_SCHEME`: SQLAlchemy 异步数据库 URI 协议，默认 `"mysql+aiomysql"`
- `CELERY_SQLALCHEMY_DATABASE_SYNC_URI_SCHEME`: SQLAlchemy 同步数据库 URI 协议，默认 `"mysql+pymysql"`
- `CELERY_SQLALCHEMY_POOL_SIZE`: SQLAlchemy 连接池大小，默认 `300`
- `CELERY_SQLALCHEMY_MAX_OVERFLOW`: SQLAlchemy 最大溢出连接数，默认 `10`
- `CELERY_SQLALCHEMY_POOL_RECYCLE`: SQLAlchemy 连接池回收时间（秒），默认 `3600`
- `CELERY_SQLALCHEMY_POOL_PRE_PING`: 启用 SQLAlchemy 连接池预检查，默认 `False`
- `CELERY_SQLALCHEMY_ECHO`: 启用 SQLAlchemy SQL 回显，默认 `False`
- `CELERY_SQLALCHEMY_POOL_ECHO`: 启用 SQLAlchemy 连接池回显，默认 `False`

#### Redis 配置（用于 worker）

- `CELERY_WORKER_REDIS_HOST`: Redis 主机地址，默认 `"localhost"`
- `CELERY_WORKER_REDIS_PORT`: Redis 端口，默认 `6379`
- `CELERY_WORKER_REDIS_USERNAME`: Redis 用户名（可选）
- `CELERY_WORKER_REDIS_PASSWORD`: Redis 密码（可选）
- `CELERY_WORKER_REDIS_DB`: Redis 数据库编号，默认 `0`

#### 计算属性

- `CELERY_BROKER_URL`: 自动生成的 Redis broker URL
- `CELERY_RESULT_BACKEND`: 自动生成的结果后端 URL
- `SQLALCHEMY_DATABASE_URI`: 自动生成的 SQLAlchemy 异步数据库 URI
- `SQLALCHEMY_DATABASE_SYNC_URI`: 自动生成的 SQLAlchemy 同步数据库 URI
- `SQLALCHEMY_ENGINE_OPTIONS`: 自动生成的 SQLAlchemy 引擎选项字典

## Orjson 序列化器支持

该模块支持使用 `orjson` 作为高性能的 JSON 序列化器。`orjson` 是一个快速、正确的 JSON 库，比标准 `json` 库性能更好，并且支持更多数据类型（如 numpy 数组、dataclass 等）。

### 启用 Orjson

1. **安装依赖**：需要安装 `orjson` 包：
   ```bash
   pip install orjson
   ```

2. **配置序列化器**：在创建 `CeleryConfig` 时，将序列化器配置为 `'orjson'`：

```python
from tomskit.celery import AsyncCelery, CeleryConfig

# 使用 orjson 序列化器
config = CeleryConfig(
    CELERY_TASK_SERIALIZER='orjson',
    CELERY_RESULT_SERIALIZER='orjson',
    CELERY_ACCEPT_CONTENT=['orjson'],
)

celery_app = AsyncCelery('myapp', config=config)
celery_app.config_from_object(config)
```

### Orjson 的优势

- **性能提升**：比标准 `json` 库快 2-3 倍
- **更多类型支持**：自动支持 numpy 数组、dataclass、datetime 等类型
- **向后兼容**：生成的 JSON 与标准库完全兼容

### 注意事项

- 如果未安装 `orjson`，系统会自动回退到标准 `json` 序列化器
- 所有 worker 和客户端必须使用相同的序列化器配置
- `CELERY_ACCEPT_CONTENT` 必须包含 `'orjson'` 才能接收使用 orjson 序列化的消息

## 任务 ID 追踪

`AsyncCelery` 自动在日志中注入任务 ID，方便追踪和调试。

### 日志格式

日志记录会自动包含 `task_id` 字段：

```python
import logging

logger = logging.getLogger("celery.task")

@async_shared_task(name="my_task")
async def my_task():
    logger.info("Task started")  # 日志会自动包含 task_id
```

### 日志输出示例

```
[2024-01-01 10:00:00] INFO celery.task: Task started [task_id=abc123-def456-...]
```

### 自定义日志格式

可以在日志配置中使用 `task_id` 字段：

```python
import logging

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s [task_id=%(task_id)s]',
    level=logging.INFO
)
```

## 注意事项

1. **资源自动初始化**：
   - 数据库连接池和 Redis 客户端在 worker 启动时自动初始化
   - 使用 `worker_process_init` 信号处理器自动初始化资源
   - 在 worker 关闭时自动清理资源

2. **会话管理**：
   - `AsyncRuntime` 和 `AsyncTaskRunner` 会自动创建和关闭数据库会话
   - 在异步函数中直接使用 `db.session`，不需要手动创建会话
   - 会话会在任务完成后自动关闭，即使发生异常也会正确清理

3. **异步函数要求**：
   - `async_shared_task` 装饰的函数必须是协程函数（使用 `async def` 定义）
   - `AsyncTaskRunner` 的 `async_task` 参数必须是协程函数
   - 在异步函数中必须使用 `await` 调用异步操作

4. **上下文管理**：
   - `AsyncCelery` 使用 `ContextVar` 管理应用上下文
   - 确保在创建任务之前已经初始化了 `AsyncCelery` 实例
   - `celery_context` 用于在运行时获取当前的 Celery 应用实例

5. **性能考虑**：
   - `AsyncRuntime` 使用共享的事件循环，性能更好
   - `AsyncTaskRunner` 使用 `asyncio.run()` 执行异步任务，每个任务都会创建新的事件循环
   - 数据库连接池在 worker 启动时创建，所有任务共享连接池

6. **错误处理**：
   - 如果 Celery 应用未初始化，会抛出 `RuntimeError`
   - 如果数据库连接池未初始化，会抛出 `RuntimeError`
   - 如果 Redis 客户端未初始化且 `use_redis=True`，会抛出 `RuntimeError`
   - 建议在任务函数中捕获和处理异常，返回错误信息而不是抛出异常

7. **配置管理**：
   - 使用 `CeleryConfig` 统一管理所有配置
   - 支持通过环境变量配置
   - 配置对象会自动生成 broker 和 backend URL

8. **Redis 使用**：
   - Redis 客户端在 worker 启动时自动初始化
   - 在异步函数中直接使用 `redis_client` 进行操作
   - `use_redis` 参数仅用于检查 Redis 客户端是否已初始化

9. **数据库结果后端**：
   - 使用数据库作为结果后端时，Celery 会自动创建 `celery_taskmeta` 表
   - 确保数据库用户有创建表的权限
   - 数据库结果后端适合需要持久化任务结果的场景

## 工作流程

1. **应用启动**：创建 `AsyncCelery` 实例并传入配置对象
2. **Worker 启动**：`AsyncRuntime.init()` 自动在 `worker_process_init` 信号中调用，初始化数据库连接池和 Redis 客户端
3. **任务执行**：
   - 使用 `async_shared_task` 装饰器定义任务（推荐）
   - 或使用 `AsyncRuntime.run()` 在任务中运行异步函数
   - 或使用 `AsyncTaskRunner` 运行异步函数
4. **资源管理**：`AsyncRuntime` 或 `AsyncTaskRunner` 自动创建数据库会话，执行异步函数，然后关闭会话
5. **Worker 关闭**：`AsyncRuntime.shutdown()` 自动在 `worker_shutting_down` 信号中调用，清理资源

## 相关文档

- [Async Task Guide](../../docs/specs/async_task_guide.md) - 详细的异步任务使用指南
- [Celery 官方文档](https://docs.celeryq.dev/) - Celery 官方文档
- [Database Guide](../../docs/specs/database_guide.md) - 数据库使用指南
- [Redis Guide](../../docs/specs/redis_guide.md) - Redis 使用指南
