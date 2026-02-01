# SQLAlchemy Module Guide

该模块提供了一组用于与 SQLAlchemy 进行交互的实用工具和扩展，支持异步数据库操作、会话管理、分页等功能。

## 模块概述

SQLAlchemy 模块基于 SQLAlchemy 2.x 异步 API，提供了完整的异步数据库操作支持。主要特性包括：

- ⚡ **完全异步**：基于 `AsyncSession` 和 `async_sessionmaker` 实现
- 🔄 **会话管理**：使用 `ContextVar` 管理数据库会话上下文
- 📄 **分页支持**：提供灵活的分页查询功能
- 🛠️ **配置管理**：基于 Pydantic Settings 的配置类
- 🔧 **类型支持**：自定义 UUID 类型和工具函数

**Import Path:**
```python
from tomskit.sqlalchemy import (
    SQLAlchemy,
    DatabaseSession,
    db,
    DatabaseConfig,
    Pagination,
    SelectPagination,
    StringUUID,
    uuid_generate_v4,
    cached_async_property
)
```

## 核心类和函数

### DatabaseConfig

数据库配置类，继承自 `pydantic_settings.BaseSettings`，用于管理数据库连接配置。

```python
class DatabaseConfig(BaseSettings):
    DB_HOST: str = Field(default="localhost", ...)
    DB_PORT: PositiveInt = Field(default=5432, ...)
    DB_USERNAME: str = Field(default="", ...)
    DB_PASSWORD: str = Field(default="", ...)
    DB_DATABASE: str = Field(default="tomskitdb", ...)
    DB_CHARSET: str = Field(default="", ...)
    DB_EXTRAS: str = Field(default="", ...)
    SQLALCHEMY_DATABASE_URI_SCHEME: str = Field(default="mysql+aiomysql", ...)
    SQLALCHEMY_DATABASE_SYNC_URI_SCHEME: str = Field(default="mysql+pymysql", ...)
    SQLALCHEMY_POOL_SIZE: NonNegativeInt = Field(default=300, ...)
    SQLALCHEMY_MAX_OVERFLOW: NonNegativeInt = Field(default=10, ...)
    SQLALCHEMY_POOL_RECYCLE: NonNegativeInt = Field(default=3600, ...)
    SQLALCHEMY_POOL_PRE_PING: bool = Field(default=False, ...)
    SQLALCHEMY_ECHO: bool = Field(default=False, ...)
    SQLALCHEMY_POOL_ECHO: bool = Field(default=False, ...)
    
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str: ...
    
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_SYNC_URI(self) -> str: ...
    
    @computed_field
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self) -> dict[str, Any]: ...
```

**配置属性说明：**
- `DB_HOST`: 数据库主机地址，默认为 `localhost`
- `DB_PORT`: 数据库端口，默认为 `5432`，必须为正整数
- `DB_USERNAME`: 数据库用户名，默认为空字符串
- `DB_PASSWORD`: 数据库密码，默认为空字符串
- `DB_DATABASE`: 数据库名称，默认为 `tomskitdb`
- `DB_CHARSET`: 数据库字符集，默认为空字符串
- `DB_EXTRAS`: 数据库额外选项，例如 `keepalives_idle=60&keepalives=1`
- `SQLALCHEMY_DATABASE_URI_SCHEME`: 异步数据库 URI 协议，默认为 `mysql+aiomysql`
- `SQLALCHEMY_DATABASE_SYNC_URI_SCHEME`: 同步数据库 URI 协议，默认为 `mysql+pymysql`
- `SQLALCHEMY_POOL_SIZE`: SQLAlchemy 连接池大小，默认为 `300`
- `SQLALCHEMY_MAX_OVERFLOW`: SQLAlchemy 最大溢出连接数，默认为 `10`
- `SQLALCHEMY_POOL_RECYCLE`: SQLAlchemy 连接池回收时间，默认为 `3600` 秒
- `SQLALCHEMY_POOL_PRE_PING`: 是否启用连接池预检，默认为 `False`
- `SQLALCHEMY_ECHO`: 是否启用 SQLAlchemy 的回显，默认为 `False`
- `SQLALCHEMY_POOL_ECHO`: 是否启用连接池的回显，默认为 `False`

**使用示例：**
```python
from tomskit.sqlalchemy.config import DatabaseConfig

config = DatabaseConfig(
    DB_USERNAME='user',
    DB_PASSWORD='password',
    DB_HOST='localhost',
    DB_PORT=5432,
    DB_DATABASE='mydb'
)

print(config.SQLALCHEMY_DATABASE_URI)
# 输出: mysql+aiomysql://user:password@localhost:5432/mydb
```

### SQLAlchemy

SQLAlchemy 抽象基类，提供模型定义和常用 SQLAlchemy 构造。

```python
class SQLAlchemy(ABC):
    class Model(AsyncAttrs, DeclarativeBase): ...
    
    # SQLAlchemy 类型和函数
    Column = sa_Column
    CHAR = sa_CHAR
    BigInteger = sa_BigInteger
    Boolean = sa_Boolean
    DateTime = sa_DateTime
    Float = sa_Float
    Integer = sa_Integer
    JSON = sa_JSON
    LargeBinary = sa_LargeBinary
    Numeric = sa_Numeric
    PickleType = sa_PickleType
    Sequence = sa_Sequence
    String = sa_String
    Text = sa_Text
    uuid = sa_CHAR(36)
    ForeignKey = sa_ForeignKey
    Index = sa_Index
    PrimaryKeyConstraint = sa_PrimaryKeyConstraint
    UniqueConstraint = sa_UniqueConstraint
    
    # SQLAlchemy 函数
    text = staticmethod(sa_text)
    select = staticmethod(sa_select)
    delete = staticmethod(sa_delete)
    update = staticmethod(sa_update)
    insert = staticmethod(sa_insert)
    func = sa_func
    relationship = staticmethod(sa_relationship)
    and_ = staticmethod(sa_and_)
    
    @abstractmethod
    async def paginate(
        self,
        select: Select[Any],
        *,
        page: int | None = None,
        per_page: int | None = None,
        max_per_page: int | None = None,
        error_out: bool = True,
        count: bool = True
    ) -> Pagination: ...
    
    @property
    @abstractmethod
    def session(self) -> AsyncSession: ...
    
    @abstractmethod
    def create_session(self) -> AsyncSession: ...
    
    @abstractmethod
    async def close_session(self, session: AsyncSession) -> None: ...
    
    @abstractmethod
    def initialize_session_pool(self, db_url: str, engine_options: Optional[dict[str, Any]] = None) -> None: ...
    
    @abstractmethod
    async def close_session_pool(self) -> None: ...
```

### DatabaseSession

数据库会话管理类，继承自 `SQLAlchemy`，使用 `ContextVar` 管理会话上下文，确保线程安全和异步安全。

```python
class DatabaseSession(SQLAlchemy):
    database_session_ctx: ContextVar[Optional[AsyncSession]] = ContextVar('database_session', default=None)
    
    async def paginate(
        self,
        select: Select[Any],
        *,
        page: int | None = None,
        per_page: int | None = None,
        max_per_page: int | None = None,
        error_out: bool = True,
        count: bool = True,
    ) -> Pagination: ...
    
    @property
    def session(self) -> Optional[AsyncSession]: ...
    
    def create_session(self) -> AsyncSession: ...
    
    async def close_session(self, session: AsyncSession) -> None: ...
    
    def initialize_session_pool(
        self,
        db_url: str,
        engine_options: Optional[dict[str, Any]] = None
    ) -> None: ...
    
    async def close_session_pool(self) -> None: ...
    
    def get_session_pool_info(self) -> dict: ...
    
    def create_celery_session(self, config: dict[str, Any]) -> AsyncSession: ...
    
    async def close_celery_session(self, session: AsyncSession) -> None: ...
```

**功能特性：**
- 提供与数据库的连接管理
- 支持事务的开始、提交和回滚
- 确保会话的线程安全和异步安全（使用 ContextVar）
- 支持连接池管理和监控
- 支持 Celery 任务的数据库会话管理

**使用场景：**
在需要与数据库进行交互的任何地方使用 `DatabaseSession` 来确保会话的正确管理。

### db

`db` 是一个全局的 `DatabaseSession` 实例，提供对数据库的直接访问。

**功能：**
- 提供全局的数据库连接
- 支持直接执行 SQL 查询
- 支持异步数据库操作

**使用场景：**
在需要直接访问数据库的地方使用 `db` 实例。

**使用示例：**
```python
from tomskit.sqlalchemy.database import db

# 获取单个对象
dataset = await db.session.get(Dataset, dataset_document.dataset_id)

# 执行删除操作
await db.session.execute(
    db.delete(Dataset).filter(Dataset.tenant_id == dest_tenant_id)
)

# 添加对象
db.session.add(dataset)
await db.session.commit()
await db.session.refresh(dataset)

# 删除对象
await db.session.delete(user)

# 执行更新操作
await db.session.execute(
    db.update(DocumentSegment).where(
        DocumentSegment.document_id == dataset_document.id,
        DocumentSegment.dataset_id == dataset.id,
        DocumentSegment.index_node_id.in_(document_ids),
        DocumentSegment.status == "indexing"
    ).values({
        DocumentSegment.status: "completed",
        DocumentSegment.enabled: True,
        DocumentSegment.completed_at: datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    })
)
```

### Pagination

分页基类，提供分页查询功能。

```python
class Pagination:
    def __init__(
        self,
        page: int | None = None,
        per_page: int | None = None,
        max_per_page: int | None = 100,
        error_out: bool = True,
        count: bool = True,
        **kwargs: Any,
    ) -> None: ...
    
    async def initialize(self) -> "Pagination": ...
    
    # 属性
    page: int
    per_page: int
    max_per_page: int | None
    items: list[Any]
    total: int | None
    
    @property
    def first(self) -> int: ...
    
    @property
    def last(self) -> int: ...
    
    @property
    def pages(self) -> int: ...
    
    @property
    def has_prev(self) -> bool: ...
    
    @property
    def prev_num(self) -> int | None: ...
    
    @property
    def has_next(self) -> bool: ...
    
    @property
    def next_num(self) -> int | None: ...
    
    async def prev(self, *, error_out: bool = False) -> "Pagination": ...
    
    async def next(self, *, error_out: bool = False) -> "Pagination": ...
    
    def iter_pages(
        self,
        *,
        left_edge: int = 2,
        left_current: int = 2,
        right_current: int = 4,
        right_edge: int = 2,
    ) -> Iterator[int | None]: ...
    
    def __iter__(self) -> Iterator[Any]: ...
```

**参数说明：**
- `page`: 当前页码，用于计算偏移量。默认为请求中的 `page` 查询参数，或 1
- `per_page`: 每页最大项目数，用于计算偏移量和限制。默认为请求中的 `per_page` 查询参数，或 20
- `max_per_page`: `per_page` 的最大允许值，用于限制用户提供的值。使用 `None` 表示无限制。默认为 100
- `error_out`: 如果没有返回项目且 `page` 不是 1，或者 `page` 或 `per_page` 小于 1，或者两者都不是整数，则中止并返回 `404 Not Found` 错误
- `count`: 通过发出额外的计数查询来计算值的总数。对于非常复杂的查询，这可能不准确或缓慢，因此可以在必要时禁用手动设置

**属性说明：**
- `page`: 当前页码
- `per_page`: 每页项目数
- `max_per_page`: 每页最大项目数
- `items`: 当前页的项目列表
- `total`: 总项目数（如果 `count=True`）
- `first`: 第一页的页码
- `last`: 最后一页的页码
- `pages`: 总页数
- `has_prev`: 是否有上一页
- `prev_num`: 上一页的页码
- `has_next`: 是否有下一页
- `next_num`: 下一页的页码

### SelectPagination

基于 Select 语句的分页实现，继承自 `Pagination`。

```python
class SelectPagination(Pagination):
    async def initialize(self) -> "SelectPagination": ...
    
    async def _query_items(self) -> list[Any]: ...
    
    async def _query_count(self) -> int: ...
```

**使用示例：**
```python
from tomskit.sqlalchemy import db, SelectPagination

# 创建查询
select_stmt = db.select(User).where(User.status == "active")

# 执行分页查询
pagination = await db.paginate(
    select_stmt,
    page=1,
    per_page=20,
    max_per_page=100
)

# 访问分页结果
for user in pagination.items:
    print(user.name)

# 访问分页信息
print(f"当前页: {pagination.page}")
print(f"总页数: {pagination.pages}")
print(f"总记录数: {pagination.total}")
print(f"是否有上一页: {pagination.has_prev}")
print(f"是否有下一页: {pagination.has_next}")
```

### StringUUID

自定义的 UUID 字符串类型，用于在数据库中存储 UUID 字符串。

```python
class StringUUID(TypeDecorator):
    impl = CHAR
    cache_ok = True
    
    def process_bind_param(self, value: Any, dialect: Any) -> str | None: ...
    
    def load_dialect_impl(self, dialect: Any) -> Any: ...
    
    def process_result_value(self, value: Any, dialect: Any) -> str | None: ...
```

**使用示例：**
```python
from tomskit.sqlalchemy import db, StringUUID

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(StringUUID, primary_key=True, default=uuid_generate_v4)
    name = db.Column(db.String(100))
```

### uuid_generate_v4

生成 UUID v4 的十六进制字符串。

```python
def uuid_generate_v4() -> str: ...
```

**使用示例：**
```python
from tomskit.sqlalchemy import uuid_generate_v4

user_id = uuid_generate_v4()
# 输出: "550e8400-e29b-41d4-a716-446655440000"
```

### cached_async_property

异步属性缓存装饰器，用于缓存异步属性的计算结果。

```python
class cached_async_property:
    def __init__(self, func: Callable) -> None: ...
    
    def __get__(self, instance: Any, owner: type) -> Awaitable[Any]: ...
```

**使用示例：**
```python
from tomskit.sqlalchemy import cached_async_property

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(StringUUID, primary_key=True)
    name = db.Column(db.String(100))
    
    @cached_async_property
    async def profile(self):
        # 第一次访问时会执行查询并缓存结果
        return await db.session.get(Profile, self.id)
```

## 完整使用示例

### 初始化数据库

```python
from tomskit.sqlalchemy import db, DatabaseConfig

# 创建配置
config = DatabaseConfig(
    DB_USERNAME='user',
    DB_PASSWORD='password',
    DB_HOST='localhost',
    DB_PORT=3306,
    DB_DATABASE='mydb'
)

# 初始化数据库连接池
db.initialize_session_pool(
    config.SQLALCHEMY_DATABASE_URI,
    config.SQLALCHEMY_ENGINE_OPTIONS
)
```

### 定义模型

```python
from tomskit.sqlalchemy import db, StringUUID, uuid_generate_v4

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(StringUUID, primary_key=True, default=uuid_generate_v4)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
```

### 数据库操作

```python
from tomskit.sqlalchemy import db

# 创建会话
session = db.create_session()

try:
    # 查询单个对象
    user = await session.get(User, user_id)
    
    # 查询多个对象
    users = await session.execute(
        db.select(User).where(User.status == "active")
    ).scalars().all()
    
    # 创建新对象
    new_user = User(name="John", email="john@example.com")
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    # 更新对象
    user.name = "Jane"
    await session.commit()
    
    # 删除对象
    await session.delete(user)
    await session.commit()
    
finally:
    # 关闭会话
    await db.close_session(session)
```

### 分页查询

```python
from tomskit.sqlalchemy import db

# 创建查询
select_stmt = db.select(User).where(User.status == "active")

# 执行分页查询
pagination = await db.paginate(
    select_stmt,
    page=1,
    per_page=20,
    max_per_page=100
)

# 访问结果
for user in pagination.items:
    print(user.name)

# 访问分页信息
print(f"总记录数: {pagination.total}")
print(f"总页数: {pagination.pages}")
print(f"当前页: {pagination.page}")
```

## 环境变量配置

数据库模块支持通过环境变量进行配置：

- `DB_HOST`: 数据库主机地址
- `DB_PORT`: 数据库端口
- `DB_USERNAME`: 数据库用户名
- `DB_PASSWORD`: 数据库密码
- `DB_DATABASE`: 数据库名称
- `DB_CHARSET`: 数据库字符集
- `DB_EXTRAS`: 数据库额外选项
- `SQLALCHEMY_DATABASE_URI_SCHEME`: 异步数据库 URI 协议
- `SQLALCHEMY_DATABASE_SYNC_URI_SCHEME`: 同步数据库 URI 协议
- `SQLALCHEMY_POOL_SIZE`: 连接池大小
- `SQLALCHEMY_MAX_OVERFLOW`: 最大溢出连接数
- `SQLALCHEMY_POOL_RECYCLE`: 连接池回收时间（秒）
- `SQLALCHEMY_POOL_PRE_PING`: 是否启用连接池预检
- `SQLALCHEMY_ECHO`: 是否回显 SQL 语句
- `SQLALCHEMY_POOL_ECHO`: 是否回显连接池调试日志

## 注意事项

1. **会话管理**：使用 `ContextVar` 管理会话上下文，确保在异步环境中正确工作
2. **连接池**：默认连接池大小为 300，最大溢出为 10，可根据实际需求调整
3. **异步操作**：所有数据库操作都是异步的，需要使用 `await` 关键字
4. **事务管理**：使用 `session.commit()` 提交事务，`session.rollback()` 回滚事务
5. **资源清理**：使用完毕后务必关闭会话，避免连接泄漏

## 相关文档

- [Database Guide](../docs/specs/database_guide.md) - 详细的数据库使用指南
- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/) - SQLAlchemy 官方文档
