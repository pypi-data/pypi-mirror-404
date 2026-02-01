# FastAI Toolkit - Worker 模块

该模块提供了与 Redis 交互的功能，用于管理和监控 `uvicorn.workers.UvicornWorker` 的进程信息。以下是模块中可用的函数及其用途：

## 函数

### `worker_register_to_redis(redis: Redis, hostname: str, pid: int)`

- **描述**: 
  - 在 `gunicorn` 启动时，将 `uvicorn.workers.UvicornWorker` 的进程信息注册到 Redis。
  
- **参数**:
  - `redis`: Redis 客户端实例。
  - `hostname`: 主机名。
  - `pid`: 进程 ID。

- **功能**:
  - 将进程信息存储在 Redis 中，以便后续管理和监控。

### `worker_delete_from_redis(redis: Redis, hostname: str, pid: int)`

- **描述**: 
  - 在 `gunicorn` 关闭时，从 Redis 中删除 `uvicorn.workers.UvicornWorker` 的进程信息。
  
- **参数**:
  - `redis`: Redis 客户端实例。
  - `hostname`: 主机名。
  - `pid`: 进程 ID。

- **功能**:
  - 从 Redis 中移除进程信息，释放资源。

### `async worker_update_to_redis(hostname: str, pid: int, update_info: dict)`

- **描述**: 
  - 在 `uvicorn.workers.UvicornWorker` 中，更新进程信息到 Redis。
  
- **参数**:
  - `hostname`: 主机名。
  - `pid`: 进程 ID。
  - `update_info`: 包含更新信息的字典，例如请求计数、异常计数等。

- **功能**:
  - 更新 Redis 中的进程信息，保持数据的实时性。

### `async get_all_worker_info_from_redis(hostname: str) -> dict`

- **描述**: 
  - 从 Redis 中获取所有的进程信息，并返回一个字典。
  
- **参数**:
  - `hostname`: 主机名。

- **返回**:
  - 包含所有进程信息的字典。

- **功能**:
  - 提供对所有注册进程的全面监控。

## 注意事项

- 确保在使用这些函数前，已正确初始化 Redis 客户端。
- 这些函数主要用于管理和监控 `uvicorn` 工作进程，适用于需要实时更新和获取进程状态的场景。 
