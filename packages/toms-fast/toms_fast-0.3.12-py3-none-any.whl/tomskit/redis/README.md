# Redis Module Guide

该模块提供了异步和同步 Redis 客户端支持，支持单机、Sentinel 和 Cluster 模式，适用于 FastAPI 异步环境。

## 模块概述

Redis 模块基于 `redis.asyncio` 和 `redis` 库，提供了完整的异步和同步 Redis 客户端支持。主要特性包括：

- ⚡ **完全异步**：基于 `redis.asyncio` 实现异步 Redis 客户端
- 🔄 **多种模式**：支持单机、Sentinel 和 Cluster 模式
- 🔒 **SSL 支持**：支持 SSL/TLS 加密连接
- 🛠️ **配置管理**：基于 Pydantic Settings 的配置类
- 🔧 **连接池管理**：自动管理连接池，支持高并发场景
- 📦 **类型安全**：使用泛型提供类型安全的客户端访问

**Import Path:**
```python
from tomskit.redis import (
    RedisClientWrapper,
    redis_client,
    RedisConfig,
    redis_sync_client
)
```

## 核心类和函数

### RedisConfig

Redis 配置类，继承自 `pydantic_settings.BaseSettings`，用于管理 Redis 连接配置。

```python
class RedisConfig(BaseSettings):
    REDIS_HOST: str = Field(default="localhost", ...)
    REDIS_PORT: PositiveInt = Field(default=6379, ...)
    REDIS_USERNAME: Optional[str] = Field(default=None, ...)
    REDIS_PASSWORD: Optional[str] = Field(default=None, ...)
    REDIS_DB: NonNegativeInt = Field(default=0, ...)
    REDIS_USE_SSL: bool = Field(default=False, ...)
    REDIS_USE_SENTINEL: Optional[bool] = Field(default=False, ...)
    REDIS_SENTINELS: Optional[str] = Field(default=None, ...)
    REDIS_SENTINEL_SERVICE_NAME: Optional[str] = Field(default=None, ...)
    REDIS_SENTINEL_USERNAME: Optional[str] = Field(default=None, ...)
    REDIS_SENTINEL_PASSWORD: Optional[str] = Field(default=None, ...)
    REDIS_SENTINEL_SOCKET_TIMEOUT: Optional[PositiveFloat] = Field(default=0.1, ...)
    REDIS_USE_CLUSTERS: bool = Field(default=False, ...)
    REDIS_CLUSTERS: Optional[str] = Field(default=None, ...)
    REDIS_CLUSTERS_PASSWORD: Optional[str] = Field(default=None, ...)
```

**配置属性说明：**
- `REDIS_HOST`: Redis 服务器主机地址，默认为 `localhost`
- `REDIS_PORT`: Redis 服务器端口，默认为 `6379`，必须为正整数
- `REDIS_USERNAME`: Redis 认证用户名（如果需要），默认为 `None`
- `REDIS_PASSWORD`: Redis 认证密码（如果需要），默认为 `None`
- `REDIS_DB`: Redis 数据库编号（0-15），默认为 `0`
- `REDIS_USE_SSL`: 是否启用 SSL/TLS 加密连接，默认为 `False`
- `REDIS_USE_SENTINEL`: 是否启用 Redis Sentinel 模式，默认为 `False`
- `REDIS_SENTINELS`: Sentinel 节点列表，格式为逗号分隔的 `host:port`，例如 `"127.0.0.1:26379,127.0.0.1:26380"`
- `REDIS_SENTINEL_SERVICE_NAME`: Sentinel 服务名称，默认为 `None`
- `REDIS_SENTINEL_USERNAME`: Sentinel 认证用户名，默认为 `None`
- `REDIS_SENTINEL_PASSWORD`: Sentinel 认证密码，默认为 `None`
- `REDIS_SENTINEL_SOCKET_TIMEOUT`: Sentinel 连接超时时间（秒），默认为 `0.1`
- `REDIS_USE_CLUSTERS`: 是否启用 Redis Cluster 模式，默认为 `False`
- `REDIS_CLUSTERS`: Cluster 节点列表，格式为逗号分隔的 `host:port`，例如 `"127.0.0.1:7000,127.0.0.1:7001"`
- `REDIS_CLUSTERS_PASSWORD`: Cluster 认证密码，默认为 `None`

**使用示例：**
```python
from tomskit.redis.config import RedisConfig

# 单机模式配置
config = RedisConfig(
    REDIS_HOST='localhost',
    REDIS_PORT=6379,
    REDIS_PASSWORD='your_password',
    REDIS_DB=0
)

# Sentinel 模式配置
sentinel_config = RedisConfig(
    REDIS_USE_SENTINEL=True,
    REDIS_SENTINELS='127.0.0.1:26379,127.0.0.1:26380',
    REDIS_SENTINEL_SERVICE_NAME='mymaster',
    REDIS_PASSWORD='your_password'
)

# Cluster 模式配置
cluster_config = RedisConfig(
    REDIS_USE_CLUSTERS=True,
    REDIS_CLUSTERS='127.0.0.1:7000,127.0.0.1:7001,127.0.0.1:7002',
    REDIS_CLUSTERS_PASSWORD='your_password'
)
```

### RedisClientWrapper

Redis 客户端包装器，提供类型安全的 Redis 客户端访问。支持异步操作和连接池管理。

```python
class RedisClientWrapper(Generic[T]):
    _client: Optional[T]
    
    def __init__(self) -> None: ...
    
    def __getattr__(self, item: str) -> Any: ...
    
    def set_client(self, client: T) -> None: ...
    
    @staticmethod
    def initialize(config: dict[str, Any]) -> None: ...
    
    @staticmethod
    async def shutdown() -> None: ...
```

**功能特性：**
- 提供类型安全的 Redis 客户端访问
- 自动代理所有 Redis 客户端方法
- 支持连接池管理（默认最大连接数为 128）
- 支持异步操作
- 提供优雅关闭方法

**方法说明：**
- `initialize(config)`: 静态方法，初始化 Redis 客户端。根据配置自动选择单机、Sentinel 或 Cluster 模式
- `shutdown()`: 静态异步方法，关闭 Redis 客户端连接
- `set_client(client)`: 设置 Redis 客户端实例
- `__getattr__(item)`: 代理所有 Redis 客户端方法，如 `get`, `set`, `hget`, `hset` 等

### redis_client

全局异步 Redis 客户端实例，类型为 `RedisClientWrapper[Redis]`。

```python
redis_client: RedisClientWrapper[Redis] = RedisClientWrapper()
```

**使用场景：**
在需要异步 Redis 操作的地方使用 `redis_client` 实例。

### redis_sync_client

创建同步 Redis 客户端函数，返回同步的 Redis 客户端实例。

```python
def redis_sync_client(config: dict[str, Any]) -> Redis | None: ...
```

**参数说明：**
- `config`: 配置字典，包含 Redis 连接参数

**返回值：**
- 返回 `Redis` 客户端实例，如果配置错误则返回 `None`

**功能特性：**
- 支持单机、Sentinel 和 Cluster 模式
- 支持 SSL/TLS 加密连接
- 同步操作，适用于非异步场景

## 完整使用示例

### 初始化异步客户端

```python
from tomskit.redis import RedisClientWrapper, redis_client, RedisConfig

# 创建配置
config = RedisConfig(
    REDIS_HOST='localhost',
    REDIS_PORT=6379,
    REDIS_PASSWORD='your_password',
    REDIS_DB=0
)

# 将配置转换为字典
config_dict = config.model_dump()

# 初始化客户端
RedisClientWrapper.initialize(config_dict)

# 现在可以使用 redis_client 进行操作
await redis_client.set('key', 'value')
value = await redis_client.get('key')
print(value)  # 输出: value
```

### 基础操作

```python
from tomskit.redis import redis_client

# 字符串操作
await redis_client.set('name', 'John')
name = await redis_client.get('name')
print(name)  # 输出: John

# 设置过期时间
await redis_client.setex('token', 3600, 'abc123')

# 检查键是否存在
exists = await redis_client.exists('name')
print(exists)  # 输出: 1

# 删除键
await redis_client.delete('name')

# 设置多个键值对
await redis_client.mset({'key1': 'value1', 'key2': 'value2'})

# 获取多个键的值
values = await redis_client.mget(['key1', 'key2'])
print(values)  # 输出: ['value1', 'value2']
```

### Hash 操作

```python
from tomskit.redis import redis_client

# 设置 Hash 字段
await redis_client.hset('user:1', mapping={
    'name': 'John',
    'age': '30',
    'email': 'john@example.com'
})

# 获取 Hash 字段
name = await redis_client.hget('user:1', 'name')
print(name)  # 输出: John

# 获取所有 Hash 字段
user_data = await redis_client.hgetall('user:1')
print(user_data)  # 输出: {'name': 'John', 'age': '30', 'email': 'john@example.com'}

# 删除 Hash 字段
await redis_client.hdel('user:1', 'email')

# 检查 Hash 字段是否存在
exists = await redis_client.hexists('user:1', 'name')
print(exists)  # 输出: True
```

### List 操作

```python
from tomskit.redis import redis_client

# 从左侧推入
await redis_client.lpush('tasks', 'task1', 'task2', 'task3')

# 从右侧推入
await redis_client.rpush('tasks', 'task4')

# 获取列表长度
length = await redis_client.llen('tasks')
print(length)  # 输出: 4

# 获取列表元素
tasks = await redis_client.lrange('tasks', 0, -1)
print(tasks)  # 输出: ['task3', 'task2', 'task1', 'task4']

# 从左侧弹出
task = await redis_client.lpop('tasks')
print(task)  # 输出: task3
```

### Set 操作

```python
from tomskit.redis import redis_client

# 添加元素
await redis_client.sadd('tags', 'python', 'redis', 'fastapi')

# 获取所有元素
tags = await redis_client.smembers('tags')
print(tags)  # 输出: {'python', 'redis', 'fastapi'}

# 检查元素是否存在
is_member = await redis_client.sismember('tags', 'python')
print(is_member)  # 输出: True

# 获取集合大小
size = await redis_client.scard('tags')
print(size)  # 输出: 3

# 移除元素
await redis_client.srem('tags', 'redis')
```

### 有序集合（Sorted Set）操作

```python
from tomskit.redis import redis_client

# 添加元素（带分数）
await redis_client.zadd('leaderboard', {'player1': 100, 'player2': 200, 'player3': 150})

# 获取排名（按分数从高到低）
top_players = await redis_client.zrevrange('leaderboard', 0, 2, withscores=True)
print(top_players)  # 输出: [('player2', 200.0), ('player3', 150.0), ('player1', 100.0)]

# 获取元素分数
score = await redis_client.zscore('leaderboard', 'player1')
print(score)  # 输出: 100.0

# 增加元素分数
new_score = await redis_client.zincrby('leaderboard', 50, 'player1')
print(new_score)  # 输出: 150.0
```

### 在 FastAPI 中使用

```python
from fastapi import FastAPI
from tomskit.redis import RedisClientWrapper, redis_client, RedisConfig
from contextlib import asynccontextmanager

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化 Redis
    config = RedisConfig()
    RedisClientWrapper.initialize(config.model_dump())
    yield
    # 关闭时清理 Redis 连接
    await RedisClientWrapper.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/cache/{key}")
async def get_cache(key: str):
    value = await redis_client.get(key)
    if value is None:
        return {"error": "Key not found"}
    return {"key": key, "value": value}

@app.post("/cache/{key}")
async def set_cache(key: str, value: str):
    await redis_client.set(key, value)
    return {"key": key, "value": value, "status": "set"}
```

### 使用 Sentinel 模式

```python
from tomskit.redis import RedisClientWrapper, redis_client, RedisConfig

# Sentinel 模式配置
config = RedisConfig(
    REDIS_USE_SENTINEL=True,
    REDIS_SENTINELS='127.0.0.1:26379,127.0.0.1:26380,127.0.0.1:26381',
    REDIS_SENTINEL_SERVICE_NAME='mymaster',
    REDIS_PASSWORD='your_password',
    REDIS_DB=0
)

# 初始化客户端
RedisClientWrapper.initialize(config.model_dump())

# 使用方式与单机模式相同
await redis_client.set('key', 'value')
value = await redis_client.get('key')
```

### 使用 Cluster 模式

```python
from tomskit.redis import RedisClientWrapper, redis_client, RedisConfig

# Cluster 模式配置
config = RedisConfig(
    REDIS_USE_CLUSTERS=True,
    REDIS_CLUSTERS='127.0.0.1:7000,127.0.0.1:7001,127.0.0.1:7002',
    REDIS_CLUSTERS_PASSWORD='your_password'
)

# 初始化客户端
RedisClientWrapper.initialize(config.model_dump())

# 使用方式与单机模式相同
await redis_client.set('key', 'value')
value = await redis_client.get('key')
```

### 使用同步客户端

```python
from tomskit.redis import redis_sync_client, RedisConfig

# 创建配置
config = RedisConfig(
    REDIS_HOST='localhost',
    REDIS_PORT=6379,
    REDIS_PASSWORD='your_password'
)

# 转换为字典
config_dict = config.model_dump()

# 创建同步客户端
redis = redis_sync_client(config_dict)

if redis:
    # 同步操作
    redis.set('key', 'value')
    value = redis.get('key')
    print(value)  # 输出: value
    
    # 关闭连接
    redis.close()
```

### 优雅关闭

```python
from tomskit.redis import RedisClientWrapper

# 在应用关闭时调用
async def cleanup():
    await RedisClientWrapper.shutdown()
```

## 环境变量配置

Redis 模块支持通过环境变量进行配置：

- `REDIS_HOST`: Redis 服务器主机地址
- `REDIS_PORT`: Redis 服务器端口
- `REDIS_USERNAME`: Redis 认证用户名
- `REDIS_PASSWORD`: Redis 认证密码
- `REDIS_DB`: Redis 数据库编号
- `REDIS_USE_SSL`: 是否启用 SSL/TLS
- `REDIS_USE_SENTINEL`: 是否启用 Sentinel 模式
- `REDIS_SENTINELS`: Sentinel 节点列表
- `REDIS_SENTINEL_SERVICE_NAME`: Sentinel 服务名称
- `REDIS_SENTINEL_USERNAME`: Sentinel 认证用户名
- `REDIS_SENTINEL_PASSWORD`: Sentinel 认证密码
- `REDIS_SENTINEL_SOCKET_TIMEOUT`: Sentinel 连接超时时间
- `REDIS_USE_CLUSTERS`: 是否启用 Cluster 模式
- `REDIS_CLUSTERS`: Cluster 节点列表
- `REDIS_CLUSTERS_PASSWORD`: Cluster 认证密码

**注意：** 在代码中使用 `REDIS_USE_CLUSTER`（单数）来检查配置，但配置类中定义的是 `REDIS_USE_CLUSTERS`（复数）。初始化时需要确保配置字典中的键名正确。

## 注意事项

1. **异步操作**：`redis_client` 的所有操作都是异步的，需要使用 `await` 关键字
2. **连接池管理**：异步客户端默认最大连接数为 128，可根据实际需求调整
3. **初始化顺序**：在使用 `redis_client` 之前必须先调用 `RedisClientWrapper.initialize()`
4. **优雅关闭**：应用关闭时应该调用 `RedisClientWrapper.shutdown()` 来关闭连接
5. **配置转换**：使用 `RedisConfig` 时，需要先转换为字典再传递给 `initialize()` 方法
6. **Sentinel 和 Cluster**：使用 Sentinel 或 Cluster 模式时，需要确保相应的配置项都已正确设置
7. **SSL 连接**：启用 SSL 时需要确保 Redis 服务器支持 SSL/TLS
8. **同步客户端**：同步客户端主要用于非异步场景，如 Celery 任务等

## 相关文档

- [Redis Guide](../docs/specs/redis_guide.md) - 详细的 Redis 使用指南
- [Redis 官方文档](https://redis.io/docs/) - Redis 官方文档
- [redis-py 文档](https://redis.readthedocs.io/) - redis-py 库文档
