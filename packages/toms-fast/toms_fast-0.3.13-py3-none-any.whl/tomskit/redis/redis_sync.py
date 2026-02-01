"""
Redis 扩展模块
"""
from typing import Union
from redis import Redis, Connection, ConnectionPool, Sentinel, SSLConnection, RedisCluster
from redis.cluster import ClusterNode

def redis_sync_client(config) -> Redis | None:
    """
    Redis 同步客户端
    """
    redis: Redis | None = None

    connection_class: type[Union[Connection, SSLConnection]] = Connection
    if config.get("REDIS_USE_SSL"):
        connection_class = SSLConnection

    redis_params = {
            "username": config.get("REDIS_USERNAME"),
            "password": config.get("REDIS_PASSWORD"),
            "db": config.get("REDIS_DB"),
            "encoding": "utf-8",
            "encoding_errors": "strict",
            "decode_responses": True,
            "max_connections": 1,
        }
    if config.get("REDIS_USE_SENTINEL"):
        sentinel_hosts = [
            (node.split(":")[0], int(node.split(":")[1])) for node in config.get("REDIS_SENTINELS").split(",")
        ]
        sentinel = Sentinel(
            sentinel_hosts,
            sentinel_kwargs={
                "socket_timeout": config.get("REDIS_SENTINEL_SOCKET_TIMEOUT", 0.1),
                "username": config.get("REDIS_SENTINEL_USERNAME"),
                "password": config.get("REDIS_SENTINEL_PASSWORD"),
            },
        )
        redis = sentinel.master_for(config.get("REDIS_SENTINEL_SERVICE_NAME"), **redis_params)
    elif config.get("REDIS_USE_CLUSTER"):
        nodes = [
            ClusterNode(host=node.split(":")[0], port=int(node.split(":")[1])) for node in config.get("REDIS_CLUSTERS").split(",")
        ]
        redis_params.update(
            {
                "password" : config.get("REDIS_CLUSTERS_PASSWORD"),
            }
        )
        redis = RedisCluster( # type: ignore
            startup_nodes=nodes,
            **redis_params
        )
    else:
        redis_params.update(
            {
                "host": config.get("REDIS_HOST"),
                "port": config.get("REDIS_PORT"),
                "max_connections": 1,
                "connection_class": connection_class,
            }
        )
        pool = ConnectionPool(**redis_params)
        redis = Redis(connection_pool=pool)

    return redis

