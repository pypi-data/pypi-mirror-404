# AsyncSerializer 使用指南

## 概述

`AsyncSerializer` 是一个通用的异步序列化器，专为 Pydantic V2 设计，能够将 ORM 对象、字典或混合数据源转换为 Pydantic 模型。它支持异步属性、函数调用、嵌套模型、并发处理等高级特性。

**Import Path:**
```python
from tomskit.utils.serializers import AsyncSerializer
```

## 核心特性

### ✨ 主要功能

1. **多数据源支持**
   - ORM 对象（如 SQLAlchemy 模型）
   - 字典数据
   - 混合数据源（对象 + 字典）

2. **异步属性自动处理**
   - 自动识别并 `await` 异步属性（`@property async def`）
   - 自动调用函数/异步函数
   - 支持协程对象

3. **智能类型处理**
   - 自动处理嵌套 Pydantic 模型
   - 支持 `List`、`Dict`、`Set`、`Tuple` 等集合类型
   - 智能处理 `Union` 和 `Optional` 类型

4. **并发处理**
   - 列表序列化自动并发处理
   - 大列表自动分批处理（每批 100 项）
   - 嵌套列表/字典/集合也支持并发处理

5. **Pydantic V2 兼容**
   - 正确处理 `validation_alias`（支持字符串）
   - 支持字段默认值和 `default_factory`
   - 智能处理字段别名

6. **性能优化**
   - 字段元数据缓存，避免重复计算
   - 大列表分批处理，避免资源耗尽
   - 已实例化的模型直接返回，避免重复序列化

## 快速开始

### 基础用法

```python
from pydantic import BaseModel
from tomskit.utils.serializers import AsyncSerializer

# 定义 Pydantic 模型
class UserModel(BaseModel):
    id: int
    name: str
    email: str
    age: int = 0

# 从字典序列化
data = {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 25}
user = await AsyncSerializer.serialize(UserModel, data)
print(user.name)  # 输出: 张三

# 从 ORM 对象序列化
class UserORM:
    def __init__(self):
        self.id = 1
        self.name = "李四"
        self.email = "lisi@example.com"
        self.age = 30

orm_user = UserORM()
user = await AsyncSerializer.serialize(UserModel, orm_user)
print(user.name)  # 输出: 李四
```

## API 文档

### serialize

单对象序列化入口。

```python
@classmethod
async def serialize(
    cls, 
    model_cls: Type[T], 
    source_data: Any
) -> T | None
```

**参数：**
- `model_cls`: Pydantic 模型类
- `source_data`: 数据源（ORM 对象 / 字典 / 混合体）

**返回：**
- 序列化后的 Pydantic 模型实例
- 如果 `source_data` 为 `None`，返回 `None`
- 如果 `source_data` 已经是该模型的实例，直接返回（避免重复序列化）

**示例：**
```python
# 字典数据
data = {"id": 1, "name": "张三"}
user = await AsyncSerializer.serialize(UserModel, data)

# ORM 对象
orm_user = UserORM(id=1, name="张三")
user = await AsyncSerializer.serialize(UserModel, orm_user)

# None 值
result = await AsyncSerializer.serialize(UserModel, None)
assert result is None
```

### serialize_list

列表序列化入口（并发处理）。

```python
@classmethod
async def serialize_list(
    cls, 
    model_cls: Type[T], 
    items: Sequence[Any] | Iterable[Any]
) -> list[T]
```

**参数：**
- `model_cls`: Pydantic 模型类
- `items`: 待序列化的对象列表（支持任何可迭代对象）

**返回：**
- 序列化后的模型列表（自动过滤掉 `None` 值）

**特性：**
- 自动并发处理，提升性能
- 小列表（≤100 项）直接并发处理
- 大列表（>100 项）自动分批处理，每批 100 项

**示例：**
```python
items = [
    {"id": 1, "name": "张三"},
    {"id": 2, "name": "李四"},
    None,  # None 值会被自动过滤
    {"id": 3, "name": "王五"}
]

users = await AsyncSerializer.serialize_list(UserModel, items)
# 返回: [UserModel(id=1, name="张三"), UserModel(id=2, name="李四"), UserModel(id=3, name="王五")]
```

### serialize_pagination

分页对象序列化入口。

```python
@classmethod
async def serialize_pagination(
    cls, 
    pagination_obj: Any, 
    model_cls: Type[T]
) -> dict[str, Any]
```

**参数：**
- `pagination_obj`: 分页对象，需要具有以下属性之一：
  - `items`: 数据项列表
  - `page`: 当前页码
  - `per_page` 或 `limit`: 每页数量
  - `total`: 总记录数
- `model_cls`: 数据项的 Pydantic 模型类

**返回：**
包含以下字段的字典：
- `page`: 当前页码
- `limit`: 每页数量
- `total`: 总记录数
- `has_more`: 是否还有更多数据
- `data`: 序列化后的数据列表

**示例：**
```python
class MockPagination:
    def __init__(self):
        self.page = 1
        self.per_page = 10
        self.total = 25
        self.items = [
            {"id": i, "name": f"用户{i}"} 
            for i in range(1, 11)
        ]

pagination = MockPagination()
result = await AsyncSerializer.serialize_pagination(pagination, UserModel)

# 返回:
# {
#     "page": 1,
#     "limit": 10,
#     "total": 25,
#     "has_more": True,
#     "data": [UserModel(...), ...]
# }
```

## 高级功能

### 1. 异步属性支持

自动识别并 `await` 异步属性。

```python
class UserORM:
    def __init__(self, name: str):
        self.name = name
    
    @property
    async def full_name(self):
        await asyncio.sleep(0.01)  # 模拟异步操作
        return f"{self.name} (Full)"

class UserModel(BaseModel):
    name: str
    full_name: str | None = None

orm_user = UserORM("张三")
user = await AsyncSerializer.serialize(UserModel, orm_user)
print(user.full_name)  # 输出: 张三 (Full)
```

### 2. 函数自动调用

自动调用字典中的函数或对象属性中的函数。

```python
# 字典中的函数
data = {
    "name": "张三",
    "display_name": lambda: "员工-张三"  # 自动调用
}

# 字典中的异步函数（直接传递函数对象）
async def get_async_name():
    await asyncio.sleep(0.01)
    return "异步名称"

data = {
    "name": "张三",
    "display_name": get_async_name  # 传递函数对象，会自动调用并 await
}

user = await AsyncSerializer.serialize(UserModel, data)
```

### 3. 嵌套模型序列化

支持多层嵌套的 Pydantic 模型。

```python
class AddressModel(BaseModel):
    city: str
    street: str

class UserModel(BaseModel):
    name: str
    address: AddressModel  # 嵌套模型

data = {
    "name": "张三",
    "address": {
        "city": "北京",
        "street": "中关村大街"
    }
}

user = await AsyncSerializer.serialize(UserModel, data)
print(user.address.city)  # 输出: 北京
```

### 4. 列表嵌套序列化

支持列表中的嵌套模型，自动并发处理。

```python
class UserModel(BaseModel):
    name: str

class DepartmentModel(BaseModel):
    name: str
    users: list[UserModel]  # 列表嵌套

data = {
    "name": "技术部",
    "users": [
        {"name": "张三"},
        {"name": "李四"}
    ]
}

dept = await AsyncSerializer.serialize(DepartmentModel, data)
# users 列表会自动并发序列化
```

### 5. validation_alias 支持

正确处理 Pydantic V2 的字段别名。

```python
from pydantic import Field, BaseModel

class UserModel(BaseModel):
    user_id: int = Field(validation_alias="userId")
    user_name: str = Field(validation_alias="userName")

# 使用别名
data = {
    "userId": 1,
    "userName": "张三"
}

user = await AsyncSerializer.serialize(UserModel, data)
print(user.user_id)  # 输出: 1
print(user.user_name)  # 输出: 张三

# 也支持回退到字段名
data = {
    "user_id": 1,  # 使用字段名也可以
    "userName": "张三"
}

user = await AsyncSerializer.serialize(UserModel, data)
```

### 6. 默认值处理

智能处理字段默认值。

```python
class UserModel(BaseModel):
    name: str
    profile: dict = Field(default_factory=dict)  # 有默认值
    age: int | None = None  # 默认值是 None

# 如果字段有默认值且值为 None，会跳过让 Pydantic 使用默认值
data = {"name": "张三"}  # profile 会使用默认值 {}
user = await AsyncSerializer.serialize(UserModel, data)
print(user.profile)  # 输出: {}

# 如果默认值本身就是 None，会传递 None
data = {"name": "张三", "age": None}
user = await AsyncSerializer.serialize(UserModel, data)
print(user.age)  # 输出: None
```

### 7. 混合数据源

支持在同一数据源中混合使用对象和字典。

```python
class UserORM:
    def __init__(self):
        self.id = 1
        self.name = "张三"

# 字典中包含 ORM 对象
data = {
    "id": 1,
    "name": "张三",
    "profile": {"age": 25}  # 字典数据
}

# 或者对象中包含字典
orm_user = UserORM()
orm_user.profile = {"age": 25}

user = await AsyncSerializer.serialize(UserModel, data)
```

## 完整示例

### 3层嵌套示例

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from tomskit.utils.serializers import AsyncSerializer

# 第3层：员工
class EmployeeModel(BaseModel):
    id: int
    name: str
    email: str
    salary: float
    profile: Dict[str, Any] = Field(default_factory=dict)
    full_name: Optional[str] = None

# 第2层：部门
class DepartmentModel(BaseModel):
    id: int
    name: str
    budget: Optional[float] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    employees: List[EmployeeModel] = Field(default_factory=list)

# 第1层：公司
class CompanyModel(BaseModel):
    id: int
    name: str
    total_employees: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    departments: List[DepartmentModel] = Field(default_factory=list)

# ORM 对象（带异步属性）
class EmployeeORM:
    def __init__(self, id: int, name: str, email: str, salary: float):
        self.id = id
        self.name = name
        self.email = email
        self.salary = salary
    
    @property
    async def full_name(self):
        await asyncio.sleep(0.01)
        return f"{self.name} (ID: {self.id})"

class DepartmentORM:
    def __init__(self, id: int, name: str, employees: list):
        self.id = id
        self.name = name
        self._employees = employees
    
    @property
    async def budget(self):
        await asyncio.sleep(0.01)
        return 100000.0 + (self.id * 10000)
    
    @property
    def employees(self):
        return self._employees

class CompanyORM:
    def __init__(self, id: int, name: str, departments: list):
        self.id = id
        self.name = name
        self._departments = departments
    
    @property
    async def total_employees(self):
        await asyncio.sleep(0.01)
        count = 0
        for dept in self._departments:
            count += len(getattr(dept, 'employees', []))
        return count
    
    @property
    def departments(self):
        return self._departments

# 使用
employees = [
    EmployeeORM(id=1, name="张三", email="zhangsan@example.com", salary=5000.0),
    EmployeeORM(id=2, name="李四", email="lisi@example.com", salary=6000.0)
]

dept = DepartmentORM(
    id=1,
    name="技术部",
    employees=employees
)

company = CompanyORM(
    id=1,
    name="测试公司",
    departments=[dept]
)

# 序列化（自动处理所有异步属性）
result = await AsyncSerializer.serialize(CompanyModel, company)

# 验证结果
assert result.id == 1
assert result.name == "测试公司"
assert result.total_employees == 2  # 异步属性已 await
assert len(result.departments) == 1
assert result.departments[0].budget == 110000.0  # 异步属性已 await
assert len(result.departments[0].employees) == 2
assert result.departments[0].employees[0].full_name == "张三 (ID: 1)"  # 异步属性已 await
```

## 性能特性

### 并发处理

- **列表序列化**：自动使用 `asyncio.gather` 并发处理
- **嵌套列表**：嵌套列表中的模型也会并发序列化
- **大列表优化**：超过 100 项的列表自动分批处理，避免资源耗尽

### 缓存机制

- **字段键名缓存**：字段的 `validation_alias` 解析结果会被缓存
- **Pydantic 键名缓存**：传递给 Pydantic 的键名会被缓存
- **避免重复序列化**：如果源数据已经是目标模型的实例，直接返回

### 分批处理

对于大列表、大字典、大集合，自动分批处理：
- 列表：每批 100 项
- 字典：每批 100 个键
- 集合：每批 100 项

## 注意事项

### 1. 异步函数处理

序列化器**会自动调用**异步函数对象。应该直接传递函数对象，而不是协程：

```python
# ✅ 正确：传递函数对象（推荐）
data = {"name": async_func}  # 会自动调用并 await

# ❌ 不推荐：传递协程
data = {"name": async_func()}  # 虽然也能工作，但不推荐
```

**注意**：虽然传递协程也能工作（会被自动 await），但推荐传递函数对象，这样更一致且更清晰。

### 2. None 值处理

- 对于字典：如果键存在但值为 `None`，会返回 `None`（`None` 可能是有效值）
- 对于对象：如果属性存在但值为 `None`，会返回 `None`
- 对于字段默认值：如果字段有默认值且值为 `None`，会跳过让 Pydantic 使用默认值（除非默认值本身就是 `None`）

### 3. 大列表性能

对于非常大的列表（>10000 项），建议：
- 使用分批处理（已自动实现）
- 考虑使用生成器或流式处理
- 监控内存使用情况

### 4. 类型注解

虽然类型注解是可选的，但提供类型注解可以获得更好的类型推断和性能：
- 嵌套模型需要类型注解才能正确序列化
- Union 类型需要类型注解才能智能匹配

## 最佳实践

### 1. 定义清晰的 Pydantic 模型

```python
class UserModel(BaseModel):
    id: int
    name: str
    email: str
    profile: dict = Field(default_factory=dict)  # 使用 default_factory
    created_at: datetime | None = None  # Optional 类型
```

### 2. 使用类型注解

```python
class DepartmentModel(BaseModel):
    name: str
    users: list[UserModel]  # 明确指定嵌套类型
```

### 3. 处理异步属性

```python
class UserORM:
    @property
    async def full_name(self):
        # 异步属性会自动 await
        return await get_full_name(self.id)
```

### 4. 利用并发处理

```python
# 列表会自动并发处理，无需手动优化
users = await AsyncSerializer.serialize_list(UserModel, user_list)
```

## 常见问题

### Q: 如何处理字段别名？

A: 使用 Pydantic 的 `Field(validation_alias="...")`，序列化器会自动处理。

### Q: 大列表会内存溢出吗？

A: 不会。序列化器会自动分批处理大列表（每批 100 项），避免资源耗尽。

### Q: 支持哪些数据源？

A: 支持字典、ORM 对象、以及它们的混合体。只要数据可以通过字典键或对象属性访问即可。

### Q: 如何处理嵌套的异步属性？

A: 序列化器会自动递归处理嵌套模型，并自动 await 所有异步属性。

### Q: 性能如何？

A: 
- 小列表（≤100 项）：并发处理，性能优秀
- 大列表（>100 项）：分批并发处理，避免资源问题
- 字段元数据缓存：避免重复计算
- 已实例化模型：直接返回，零开销

## 技术细节

### 支持的集合类型

- `List[T]` / `list[T]`
- `Tuple[T, ...]` / `tuple[T, ...]`
- `Dict[str, T]` / `dict[str, T]`
- `Set[T]` / `set[T]`
- `Sequence[T]` / `Iterable[T]`

### 支持的 Union 类型

- `Union[A, B]`
- `Optional[T]` (等价于 `Union[T, None]`)
- 智能类型匹配：根据实际值类型选择最匹配的 Union 成员

### validation_alias 支持

- 字符串别名：`Field(validation_alias="userId")`
- AliasChoices：`Field(validation_alias=AliasChoices("userId", "user_id"))`
- AliasPath：`Field(validation_alias=AliasPath("user", "id"))`

## 版本要求

- Python >= 3.11
- Pydantic >= 2.0

## 相关文档

- [Pydantic V2 文档](https://docs.pydantic.dev/)
- [测试用例](../tests/test_serializers/test_async_serializer.py)
