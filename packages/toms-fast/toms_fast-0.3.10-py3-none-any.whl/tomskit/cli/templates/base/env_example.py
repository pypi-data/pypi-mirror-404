"""
Env example template
Template for generating .env.example file.
"""

TEMPLATE = '''# {project_name} 应用配置
# .env
# 环境变量配置文件示例
# 所有配置项都使用默认值，可以根据需要修改

# ============================================================================
# 服务器通用配置（Gunicorn 和 Hypercorn 共用）
# ============================================================================
SERVER_BIND=0.0.0.0:5001
SERVER_WORKERS=0
SERVER_DAEMON=False
# SERVER_PIDFILE=run/server.pid  # 可选，不设置则使用 None

# ============================================================================
# Gunicorn 特有配置
# ============================================================================
GUNICORN_CPU_AFFINITY=[]
# GUNICORN_PROC_NAME=fastone-master  # 可选，不设置则使用 None

# ============================================================================
# Hypercorn 特有配置
# ============================================================================
# HYPERCORN_ACCESSLOG=logs/access.log  # 可选，不设置则禁用访问日志
# HYPERCORN_ERRORLOG=logs/error.log   # 可选，不设置则输出到 stderr
HYPERCORN_LOG_LEVEL=info
HYPERCORN_ACCESS_LOG_FORMAT=%(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s

# ============================================================================
# Redis 配置
# ============================================================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=32
# REDIS_USERNAME=  # 可选，不设置则使用 None
# REDIS_PASSWORD=  # 可选，不设置则使用 None
REDIS_USE_SSL=False
REDIS_SSL_CERT_REQS=CERT_NONE
# REDIS_SSL_CA_CERTS=  # 可选，不设置则使用 None
# REDIS_SSL_CERTFILE=  # 可选，不设置则使用 None
# REDIS_SSL_KEYFILE=  # 可选，不设置则使用 None
REDIS_USE_SENTINEL=False
# REDIS_SENTINELS=  # 可选，不设置则使用 None
# REDIS_SENTINEL_SERVICE_NAME=  # 可选，不设置则使用 None
# REDIS_SENTINEL_USERNAME=  # 可选，不设置则使用 None
# REDIS_SENTINEL_PASSWORD=  # 可选，不设置则使用 None
REDIS_SENTINEL_SOCKET_TIMEOUT=0.1
REDIS_USE_CLUSTERS=False
# REDIS_CLUSTERS=  # 可选，不设置则使用 None
# REDIS_CLUSTERS_PASSWORD=  # 可选，不设置则使用 None

# ============================================================================
# 日志配置
# ============================================================================
LOG_PREFIX=
LOG_DIR=logs
LOG_NAME=apps
LOG_LEVEL=INFO
LOG_FORMAT=[%(asctime)s] [%(levelname)s] [%(name)s] [trace_id=%(trace_id)s] %(message)s
LOG_USE_UTC=False
LOG_DATE_FORMAT=%Y-%m-%d %H:%M:%S
LOG_BACKUP_COUNT=0
LOG_ROTATE_WHEN=midnight
LOG_ACCESS_NAME=access
LOG_ACCESS_FORMAT=%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"
LOG_SQL_ENABLED=False
LOG_SQL_NAME=sql
LOG_SQL_LEVEL=INFO
LOG_CELERY_ENABLED=False
LOG_CELERY_NAME=celery
LOG_CELERY_LEVEL=INFO
LOG_THIRD_PARTY_LEVEL=WARNING

# ============================================================================
# 数据库配置
# ============================================================================
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=
DB_PASSWORD=
DB_DATABASE=tomskitdb
DB_CHARSET=
DB_EXTRAS=
SQLALCHEMY_DATABASE_URI_SCHEME=mysql+aiomysql
SQLALCHEMY_DATABASE_SYNC_URI_SCHEME=mysql+pymysql
SQLALCHEMY_POOL_SIZE=300
SQLALCHEMY_MAX_OVERFLOW=10
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_POOL_PRE_PING=False
SQLALCHEMY_ECHO=False
SQLALCHEMY_POOL_ECHO=False

# ============================================================================
# Celery 配置
# ============================================================================

# Redis Broker 配置
CELERY_BROKER_REDIS_HOST=localhost
CELERY_BROKER_REDIS_PORT=6379
# CELERY_BROKER_REDIS_USERNAME=  # 可选，不设置则使用 None
# CELERY_BROKER_REDIS_PASSWORD=  # 可选，不设置则使用 None
CELERY_BROKER_REDIS_DB=0

# Result Backend 配置
CELERY_RESULT_BACKEND_TYPE=redis
CELERY_RESULT_BACKEND_REDIS_HOST=localhost
CELERY_RESULT_BACKEND_REDIS_PORT=6379
# CELERY_RESULT_BACKEND_REDIS_USERNAME=  # 可选，不设置则使用 None
# CELERY_RESULT_BACKEND_REDIS_PASSWORD=  # 可选，不设置则使用 None
CELERY_RESULT_BACKEND_REDIS_DB=1
CELERY_RESULT_BACKEND_DATABASE_URI_SCHEME=mysql

# Celery Task 配置
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=True
CELERY_TASK_TRACK_STARTED=True
# CELERY_TASK_TIME_LIMIT=  # 可选，不设置则使用 None
# CELERY_TASK_SOFT_TIME_LIMIT=  # 可选，不设置则使用 None
CELERY_TASK_IGNORE_RESULT=False
# CELERY_RESULT_EXPIRES=  # 可选，不设置则使用 None

# Celery 数据库配置（用于 worker 和结果后端）
CELERY_DB_HOST=localhost
CELERY_DB_PORT=5432
CELERY_DB_USERNAME=
CELERY_DB_PASSWORD=
CELERY_DB_DATABASE=tomskitdb
CELERY_DB_CHARSET=
CELERY_DB_EXTRAS=
CELERY_SQLALCHEMY_DATABASE_URI_SCHEME=mysql+aiomysql
CELERY_SQLALCHEMY_DATABASE_SYNC_URI_SCHEME=mysql+pymysql
CELERY_SQLALCHEMY_POOL_SIZE=300
CELERY_SQLALCHEMY_MAX_OVERFLOW=10
CELERY_SQLALCHEMY_POOL_RECYCLE=3600
CELERY_SQLALCHEMY_POOL_PRE_PING=False
CELERY_SQLALCHEMY_ECHO=False
CELERY_SQLALCHEMY_POOL_ECHO=False

# Celery Worker Redis 配置
CELERY_WORKER_REDIS_HOST=localhost
CELERY_WORKER_REDIS_PORT=6379
# CELERY_WORKER_REDIS_USERNAME=  # 可选，不设置则使用 None
# CELERY_WORKER_REDIS_PASSWORD=  # 可选，不设置则使用 None
CELERY_WORKER_REDIS_DB=0

'''
