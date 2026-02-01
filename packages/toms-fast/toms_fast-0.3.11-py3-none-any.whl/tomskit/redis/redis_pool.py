"""
Redis 扩展模块
"""
from typing import Any, Union, Optional, TypeVar, Generic
from redis.asyncio import Connection, ConnectionPool, Redis, Sentinel, SSLConnection, RedisCluster
from redis.asyncio.cluster import ClusterNode
from tomskit.redis.config import RedisConfig

T = TypeVar("T", bound=Redis)

class RedisClientWrapper(Generic[T]):
    _client: Optional[T] = None
    def __init__(self) -> None:
        self._client: Redis | None = None
    
    def __getattr__(self, item) -> Any:
        if self._client is None:
            raise RuntimeError("Redis client is not initialized. Call initialize first.")
        return getattr(self._client, item)

    def set_client(self, client: T) -> None:
        if self._client is None:
            self._client = client

    @staticmethod
    def initialize(settings: RedisConfig) -> None:
        global redis_client
        connection_class: type[Union[Connection, SSLConnection]] = Connection
        if settings.REDIS_USE_SSL:
            connection_class = SSLConnection

        redis_params: dict[str, Any] = {
            "username": settings.REDIS_USERNAME,
            "password": settings.REDIS_PASSWORD,
            "db": settings.REDIS_DB,
            "encoding": "utf-8",
            "encoding_errors": "strict",
            "decode_responses": True,
            "max_connections": settings.REDIS_MAX_CONNECTIONS,
        }
        
        if settings.REDIS_USE_SENTINEL:
            if not settings.REDIS_SENTINELS:
                raise ValueError("REDIS_SENTINELS must be set when REDIS_USE_SENTINEL is True")
            if not settings.REDIS_SENTINEL_SERVICE_NAME:
                raise ValueError("REDIS_SENTINEL_SERVICE_NAME must be set when REDIS_USE_SENTINEL is True")
            
            sentinel_hosts = [
                (node.split(":")[0], int(node.split(":")[1])) 
                for node in settings.REDIS_SENTINELS.split(",")
            ]
            sentinel = Sentinel(
                sentinel_hosts,
                sentinel_kwargs={
                    "socket_timeout": settings.REDIS_SENTINEL_SOCKET_TIMEOUT or 0.1,
                    "username": settings.REDIS_SENTINEL_USERNAME,
                    "password": settings.REDIS_SENTINEL_PASSWORD,
                },
            )
            master = sentinel.master_for(settings.REDIS_SENTINEL_SERVICE_NAME, **redis_params)
            redis_client.set_client(master)
        elif settings.REDIS_USE_CLUSTERS:
            if not settings.REDIS_CLUSTERS:
                raise ValueError("REDIS_CLUSTERS must be set when REDIS_USE_CLUSTERS is True")
            
            nodes = [
                ClusterNode(host=node.split(":")[0], port=int(node.split(":")[1])) 
                for node in settings.REDIS_CLUSTERS.split(",")
            ]
            redis_params.update(
                {
                    "password": settings.REDIS_CLUSTERS_PASSWORD,
                }
            )
            cluster = RedisCluster(
                startup_nodes=nodes,
                **redis_params
            )
            redis_client.set_client(cluster)  # type: ignore
        else:
            redis_params.update(
                {
                    "host": settings.REDIS_HOST,
                    "port": settings.REDIS_PORT,
                    "max_connections": settings.REDIS_MAX_CONNECTIONS,
                    "connection_class": connection_class,
                }
            )
            pool = ConnectionPool(**redis_params)
            redis_client.set_client(Redis(connection_pool=pool))

    @staticmethod
    async def shutdown() -> None:
        global redis_client
        if redis_client._client is not None:
            await redis_client._client.aclose()
            redis_client._client = None

redis_client: RedisClientWrapper[Redis] = RedisClientWrapper()
