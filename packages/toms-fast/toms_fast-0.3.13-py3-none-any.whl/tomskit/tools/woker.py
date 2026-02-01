
from datetime import datetime
from redis import Redis
from tomskit.redis import redis_client

def worker_register_to_redis(redis: Redis, hostname: str, pid: int):
    """
    gunicorn 启动时，把 uvicorn.workers.UvicornWorker 注册进程到 redis
    """
    process_info: dict = {
        "pid": str(pid),
        "start_at": int(datetime.now().timestamp()),
        "uptime": 0,
        "request_count": 0,
        "exception_count": 0,
        "server_error_count": 0,
        "status": "starting",
        "last_update_by" : "gunicorn",
        "last_update_at": int(datetime.now().timestamp()),
    }
    redis.sadd(f"{hostname}:workers", str(pid))
    redis.hset(f"{hostname}:worker:{str(pid)}", mapping=process_info)


def worker_delete_from_redis(redis: Redis, hostname: str, pid: int):
    """
    gunicorn 关闭时，把 uvicorn.workers.UvicornWorker 从 redis 中删除
    """
    redis.srem(f"{hostname}:workers", str(pid))
    redis.delete(f"{hostname}:worker:{str(pid)}")


async def worker_update_to_redis(hostname: str, pid: int, update_info: dict):
    """
    在 uvicorn.workers.UvicornWorker 中，更新进程信息到 redis
    update_info: dict = {
        "request_count": int,
        "exception_count": int,
        "server_error_count": int,
    }
    """

    redis = redis_client._client
    if redis is None:
        raise RuntimeError("Redis client is not initialized. Call initialize first.")

    worker_key = f"{hostname}:worker:{str(pid)}"
    
    # 获取当前进程信息
    current_info = await redis.hgetall(worker_key) # type: ignore
    
    # 更新进程信息
    if current_info:
        current_info["uptime"] = int(datetime.now().timestamp()) - int(current_info["start_at"])
        current_info["last_update_at"] = int(datetime.now().timestamp())
        current_info["status"] = "running"
        current_info["last_update_by"] = "uvicorn.tomskit"
        current_info.update(update_info)
        # 更新到 redis
        await redis.hset(worker_key, mapping=current_info) # type: ignore


async def get_all_worker_info_from_redis(hostname: str) -> dict:
    """
    从 redis 中获取所有的进程信息，返回 dict
    """
    redis = redis_client._client
    if redis is None:
        raise RuntimeError("Redis client is not initialized. Call initialize first.")

    # 获取所有的 worker pids
    worker_pids = await redis.smembers(f"{hostname}:workers") # type: ignore

    all_process_info = {}
    for pid in worker_pids:
        worker_key = f"{hostname}:worker:{pid}"
        process_info = await redis.hgetall(worker_key) # type: ignore
        if process_info:
            all_process_info[pid] = {k: v for k, v in process_info.items()}

    return all_process_info
