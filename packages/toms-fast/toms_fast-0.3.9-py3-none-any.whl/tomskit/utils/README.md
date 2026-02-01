# Utils Module Guide

该模块提供了数据序列化、字段定义和响应处理等功能，支持异步数据源（如异步数据库查询）的数据序列化。

## 模块概述

Utils 模块基于 Flask-RESTful 的 `marshal` 函数改写的异步版本，适应 FastAPI 的异步环境，保持了相同的 API 设计和使用方式。主要特性包括：

- ⚡ **完全异步**：所有字段类和方法都支持异步操作，适配异步数据库查询
- 🔄 **灵活序列化**：支持单个对象、列表、元组和异步可迭代对象的序列化
- 🧩 **丰富字段类型**：提供多种字段类型，包括字符串、数字、日期时间、嵌套对象等
- 🎯 **装饰器支持**：提供装饰器自动序列化函数返回值
- 🔧 **属性映射**：支持字段的 `attribute` 属性映射，灵活处理数据源

**Import Path:**
```python
from tomskit.utils import (
    marshal,
    marshal_with,
    marshal_with_field,
    String,
    DateTime,
    Float,
    Integer,
    Nested,
    List,
    Raw,
    Boolean,
    FormattedString,
    Arbitrary,
    Fixed,
    Price,
    MarshallingException
)
```

## 核心类和函数

### marshal

数据序列化函数，根据字段定义序列化数据。支持单个对象、列表、元组和异步可迭代对象的序列化。

**注意:** 此函数是基于 Flask-RESTful 的 `marshal` 函数改写的异步版本，适应 FastAPI 的异步环境。

```python
async def marshal(
    data: Any,
    fields: dict[str, Any],
    envelope: str | None = None
) -> OrderedDict | list[OrderedDict]: ...
```

**参数说明:**
- `data`: 要序列化的数据对象，可以是单个对象、列表、元组或异步可迭代对象
- `fields`: 字段定义字典，键为输出字段名，值为字段类型或嵌套字段字典
- `envelope`: 可选的包装键，用于将序列化结果包裹在指定的键下

**返回值:**
- 如果 `envelope` 为 `None`，返回 `OrderedDict` 或 `list[OrderedDict]`
- 如果 `envelope` 不为 `None`，返回包裹在指定键下的 `OrderedDict`

**功能特性:**
- 支持嵌套字段序列化（通过字典类型的字段值）
- 支持列表和元组的批量序列化
- 支持异步可迭代对象的序列化（`AsyncIterable`）
- 自动处理 `None` 值
- 支持字段的 `attribute` 属性映射
- 所有字段的 `output` 方法支持异步调用（`await`）

**使用示例:**
```python
from tomskit.utils import marshal, String, Integer, DateTime

# 定义字段
user_fields = {
    'name': String(),
    'age': Integer(),
    'created_at': DateTime(dt_format='iso8601')
}

# 序列化单个对象
user_data = {
    'name': 'John',
    'age': 30,
    'created_at': datetime.now()
}
result = await marshal(user_data, user_fields)
# 输出: OrderedDict([('name', 'John'), ('age', 30), ('created_at', '2024-01-01T12:00:00')])

# 序列化列表
users = [user_data, {...}]
results = await marshal(users, user_fields)
# 输出: [OrderedDict(...), OrderedDict(...)]
```

### marshal_with

数据序列化装饰器，用于自动序列化函数返回值。基于 Flask-RESTful 的 `marshal_with` 装饰器改写的异步版本。

```python
class marshal_with:
    def __init__(
        self,
        fields: dict[str, Any],
        envelope: str | None = None
    ) -> None: ...
    
    fields: dict[str, Any]
    envelope: str | None
    
    def __call__(self, f: Callable) -> Callable: ...
```

**参数说明:**
- `fields`: 字段定义字典，键为输出字段名，值为字段类型或嵌套字段字典
- `envelope`: 可选的包装键，用于将序列化结果包裹在指定的键下

**使用场景:**
- 装饰 API 路由处理函数，自动序列化返回值
- 支持复杂的嵌套字段结构

**功能特性:**
- 自动处理函数返回的元组 `(data, status_code, headers)`
- 支持 `JSONResponse` 直接返回
- 自动将序列化结果包装为 `JSONResponse`
- 使用 `marshal` 函数进行实际序列化
- 支持异步函数装饰

**使用示例:**
```python
from fastapi import FastAPI
from tomskit.utils import marshal_with, String, Integer

app = FastAPI()

user_fields = {
    'name': String(),
    'age': Integer()
}

@app.get("/users/{user_id}")
@marshal_with(user_fields)
async def get_user(user_id: int):
    # 返回的数据会自动序列化
    return {'name': 'John', 'age': 30}
    # 或者返回元组 (data, status_code, headers)
    # return {'name': 'John', 'age': 30}, 200, {'X-Custom': 'value'}
```

### marshal_with_field

单字段序列化装饰器，用于使用单个字段类型序列化函数返回值。基于 Flask-RESTful 的 `marshal_with_field` 装饰器改写的异步版本。

```python
class marshal_with_field:
    def __init__(
        self,
        field: type[Raw] | Raw
    ) -> None: ...
    
    field: Raw
    
    def __call__(self, f: Callable) -> Callable: ...
```

**参数说明:**
- `field`: 字段类型或字段实例，可以是类型（如 `List(Integer)`）或实例（如 `List(Integer())`）

**使用场景:**
- 当只需要使用单个字段类型（如 `List`、`String` 等）序列化返回值时
- 适用于返回简单列表或单个值的函数

**功能特性:**
- 自动处理函数返回的元组 `(data, status_code, headers)`
- 支持 `JSONResponse` 直接返回
- 使用字段的 `format` 方法进行序列化
- 支持异步函数装饰

**使用示例:**
```python
from tomskit.utils import marshal_with_field, List, Integer

@app.get("/numbers")
@marshal_with_field(List(Integer))
async def get_numbers():
    return ['1', 2, 3.0]
    # 自动序列化为: [1, 2, 3]
```

## 字段类

### Raw

字段基类，所有字段类型都继承自此类。

```python
class Raw:
    def __init__(
        self,
        default: Any = None,
        attribute: str | None = None
    ) -> None: ...
    
    attribute: str | None
    default: Any
    
    async def format(self, value: Any) -> Any: ...
    
    async def output(self, key: str, obj: Any) -> Any: ...
```

**参数说明:**
- `default`: 字段的默认值，如果未指定值，则使用该值
- `attribute`: 如果公开字段名与内部属性名不同，使用此参数指定内部属性名

### String

字符串字段，将值转换为字符串。

```python
class String(Raw):
    async def format(self, value: Any) -> str: ...
```

**使用示例:**
```python
from tomskit.utils import String

field = String()
result = await field.format(123)
# 输出: "123"
```

### Integer

整数字段，将值转换为整数。

```python
class Integer(Raw):
    def __init__(self, default: int = 0, **kwargs: Any) -> None: ...
    
    async def format(self, value: Any) -> int: ...
```

**参数说明:**
- `default`: 默认值，默认为 `0`

**使用示例:**
```python
from tomskit.utils import Integer

field = Integer(default=0)
result = await field.format("123")
# 输出: 123
```

### Float

浮点数字段，将值转换为浮点数。

```python
class Float(Raw):
    async def format(self, value: Any) -> float: ...
```

### Boolean

布尔字段，将值转换为布尔值。空集合（如 `""`、`{}`、`[]` 等）将被转换为 `False`。

```python
class Boolean(Raw):
    async def format(self, value: Any) -> bool: ...
```

### DateTime

日期时间字段，支持 RFC 822 和 ISO 8601 格式。

```python
class DateTime(Raw):
    def __init__(
        self,
        dt_format: str = 'rfc822',
        **kwargs: Any
    ) -> None: ...
    
    dt_format: str
    
    async def format(self, value: Any) -> str: ...
```

**参数说明:**
- `dt_format`: 日期格式，可选值为 `'rfc822'` 或 `'iso8601'`，默认为 `'rfc822'`

**功能特性:**
- 支持 RFC 822 格式（如 "Sat, 01 Jan 2011 00:00:00 -0000"）
- 支持 ISO 8601 格式（如 "2012-01-01T00:00:00"）
- 自动转换为 UTC 时间

**使用示例:**
```python
from tomskit.utils import DateTime
from datetime import datetime

field = DateTime(dt_format='iso8601')
result = await field.format(datetime.now())
# 输出: "2024-01-01T12:00:00"
```

### Nested

嵌套字段，用于嵌套对象序列化。

```python
class Nested(Raw):
    def __init__(
        self,
        nested: dict[str, Any],
        allow_null: bool = False,
        **kwargs: Any
    ) -> None: ...
    
    nested: dict[str, Any]
    allow_null: bool
    
    async def output(self, key: str, obj: Any) -> dict[str, Any] | None: ...
```

**参数说明:**
- `nested`: 嵌套字段定义字典
- `allow_null`: 如果嵌套对象为 `None`，是否返回 `None` 而不是空字典

**使用示例:**
```python
from tomskit.utils import Nested, String, Integer

user_fields = {
    'name': String(),
    'age': Integer()
}

profile_fields = {
    'user': Nested(user_fields),
    'bio': String()
}
```

### List

列表字段，用于序列化列表数据。

```python
class List(Raw):
    def __init__(
        self,
        cls_or_instance: type[Raw] | Raw,
        **kwargs: Any
    ) -> None: ...
    
    container: Raw
    
    async def format(self, value: Any) -> list[Any] | None: ...
    
    async def output(self, key: str, data: Any) -> list[Any]: ...
```

**使用示例:**
```python
from tomskit.utils import List, Integer, String

# 整数列表
field = List(Integer)
result = await field.format(['1', 2, 3.0])
# 输出: [1, 2, 3]

# 嵌套列表
nested_fields = {
    'tags': List(String)
}
```

### FormattedString

格式化字符串字段，支持从响应中插入其他值。

```python
class FormattedString(Raw):
    def __init__(self, src_str: str) -> None: ...
    
    src_str: str
    
    async def output(self, key: str, obj: Any) -> str: ...
```

**使用示例:**
```python
from tomskit.utils import FormattedString, String

fields = {
    'name': String(),
    'greeting': FormattedString("Hello {name}")
}

data = {'name': 'John'}
result = await marshal(data, fields)
# 输出: OrderedDict([('name', 'John'), ('greeting', 'Hello John')])
```

### Arbitrary

任意精度浮点数字段，用于处理大数值。

```python
class Arbitrary(Raw):
    async def format(self, value: Any) -> str: ...
```

**功能特性:**
- 使用 `Decimal` 类型处理任意精度的浮点数
- 返回字符串格式的数值，避免精度丢失
- 适用于金融、科学计算等需要高精度的场景

**使用示例:**
```python
from tomskit.utils import Arbitrary

field = Arbitrary()
result = await field.format(634271127864378216478362784632784678324.23432)
# 输出: "634271127864378216478362784632784678324.23432"
```

### Fixed

固定精度数字字段，用于格式化小数位数。

```python
class Fixed(Raw):
    def __init__(
        self,
        decimals: int = 5,
        **kwargs: Any
    ) -> None: ...
    
    precision: Decimal
    
    async def format(self, value: Any) -> str: ...
```

**参数说明:**
- `decimals`: 小数位数，默认为 5

**功能特性:**
- 使用 `Decimal` 类型进行精确的数值计算
- 自动四舍五入到指定的小数位数
- 返回字符串格式的数值

**使用示例:**
```python
from tomskit.utils import Fixed

field = Fixed(decimals=2)
result = await field.format(3.14159)
# 输出: "3.14"
```

### Price

价格字段，`Fixed` 的别名，专门用于价格格式化。

```python
Price = Fixed
```

**使用场景:**
- 商品价格格式化
- 货币金额显示
- 需要固定小数位数的数值

**使用示例:**
```python
from tomskit.utils import Price

field = Price(decimals=2)
result = await field.format(99.999)
# 输出: "100.00"
```

### MarshallingException

序列化异常类，用于处理序列化过程中的错误。

```python
class MarshallingException(Exception):
    def __init__(self, underlying_exception: Exception) -> None: ...
```

## 完整使用示例

### 基础序列化

```python
from tomskit.utils import marshal, String, Integer, DateTime
from datetime import datetime

# 定义字段
user_fields = {
    'name': String(),
    'age': Integer(),
    'created_at': DateTime(dt_format='iso8601')
}

# 数据
user_data = {
    'name': 'John Doe',
    'age': 30,
    'created_at': datetime.now()
}

# 序列化
result = await marshal(user_data, user_fields)
print(result)
# 输出: OrderedDict([('name', 'John Doe'), ('age', 30), ('created_at', '2024-01-01T12:00:00')])
```

### 嵌套对象序列化

```python
from tomskit.utils import marshal, String, Integer, Nested, List

# 定义嵌套字段
address_fields = {
    'street': String(),
    'city': String(),
    'zipcode': String()
}

user_fields = {
    'name': String(),
    'age': Integer(),
    'address': Nested(address_fields),
    'tags': List(String)
}

# 数据
user_data = {
    'name': 'John',
    'age': 30,
    'address': {
        'street': '123 Main St',
        'city': 'New York',
        'zipcode': '10001'
    },
    'tags': ['developer', 'python']
}

# 序列化
result = await marshal(user_data, user_fields)
```

### 使用装饰器

```python
from fastapi import FastAPI
from tomskit.utils import marshal_with, String, Integer, Nested, List

app = FastAPI()

# 定义字段
user_fields = {
    'name': String(),
    'age': Integer(),
    'tags': List(String)
}

@app.get("/users/{user_id}")
@marshal_with(user_fields)
async def get_user(user_id: int):
    # 从数据库获取用户（异步）
    user = await db.session.get(User, user_id)
    return {
        'name': user.name,
        'age': user.age,
        'tags': user.tags  # 假设这是一个异步属性
    }
```

### 属性映射

```python
from tomskit.utils import marshal, String, Integer

# 使用 attribute 参数映射不同的属性名
fields = {
    'display_name': String(attribute='name'),  # 输出字段名为 display_name，但从 name 属性获取
    'years_old': Integer(attribute='age')      # 输出字段名为 years_old，但从 age 属性获取
}

class User:
    def __init__(self):
        self.name = 'John'
        self.age = 30

user = User()
result = await marshal(user, fields)
# 输出: OrderedDict([('display_name', 'John'), ('years_old', 30)])
```

### 异步数据源

```python
from tomskit.utils import marshal, String, Integer
from tomskit.sqlalchemy import db

# 定义字段
user_fields = {
    'name': String(),
    'age': Integer()
}

# 从异步数据库查询获取数据
async def get_users():
    result = await db.session.execute(db.select(User))
    users = result.scalars().all()
    return await marshal(users, user_fields)

# 或者使用异步可迭代对象
async def get_users_stream():
    async for user in db.session.stream(db.select(User)):
        yield user

# 序列化异步可迭代对象
async def serialize_users():
    users_stream = get_users_stream()
    return await marshal(users_stream, user_fields)
```

### 使用 envelope 包装

```python
from tomskit.utils import marshal, String, Integer

fields = {
    'name': String(),
    'age': Integer()
}

data = {'name': 'John', 'age': 30}

# 使用 envelope 包装结果
result = await marshal(data, fields, envelope='user')
# 输出: OrderedDict([('user', OrderedDict([('name', 'John'), ('age', 30)]))])
```

## 注意事项

1. **异步操作**：所有字段类的方法都是异步的，需要使用 `await` 关键字
2. **数据源支持**：支持从异步数据源（如异步数据库查询）获取数据，会自动处理协程对象
3. **None 值处理**：自动处理 `None` 值，可以使用 `default` 参数指定默认值
4. **属性映射**：使用 `attribute` 参数可以映射不同的属性名
5. **嵌套序列化**：支持多层嵌套的对象序列化
6. **性能考虑**：对于大量数据的序列化，建议使用异步可迭代对象以提高性能

## 相关文档

- [Utils Guide](../docs/specs/utils_guide.md) - 详细的工具模块使用指南
- [Flask-RESTful 文档](https://flask-restful.readthedocs.io/) - Flask-RESTful 原始实现参考
