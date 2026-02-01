"""
marshal 函数，支持异步数据序列化。

基于 flask-restful 的 marshal 实现，但所有操作都是异步的，以支持从异步数据源（如异步数据库查询）获取数据。
"""
import inspect
from collections import OrderedDict
from collections.abc import AsyncIterable
from functools import wraps

from fastapi.responses import JSONResponse

from tomskit.utils.response_utils import unpack


async def marshal(data, fields, envelope=None):
    """接受原始数据（以字典、列表、对象的形式）和输出字段的字典，
    并根据这些字段过滤数据。支持异步数据获取。

    :param data: 实际的数据对象（可以是单个对象或对象列表）
    :param fields: 包含输出字段的字典
    :param envelope: 可选的键，用于包裹序列化的响应
    """
    def make(cls):
        if isinstance(cls, type):
            return cls()
        return cls

    if data is None:
        return OrderedDict() if envelope is None else OrderedDict([(envelope, None)])
    
    # 处理列表和元组
    if isinstance(data, (list, tuple)):
        results = []
        for item in data:
            result = await marshal(item, fields)
            results.append(result)
        return OrderedDict([(envelope, results)]) if envelope else results

    # 处理异步可迭代对象
    elif isinstance(data, AsyncIterable):
        results = []
        async for item in data:
            result = await marshal(item, fields)
            results.append(result)
        return OrderedDict([(envelope, results)]) if envelope else results

    # 处理单个对象
    items = OrderedDict()
    for k, v in fields.items():
        if isinstance(v, dict):
            value = await marshal(data, v)
        else:
            field_instance = make(v)
            if hasattr(field_instance, 'output'):
                output = field_instance.output(k, data)
                if inspect.isawaitable(output):
                    value = await output
                else:
                    value = output
            else:
                raise ValueError(f"字段 '{k}' 不是有效的 Field 实例。")
        items[k] = value

    return OrderedDict([(envelope, items)]) if envelope else items


class marshal_with:
    """A decorator that apply marshalling to the return values of your methods.

    see :meth:`marshal_utils.marshal`
    """
    def __init__(self, fields, envelope=None):
        """
        :param fields: a dict of whose keys will make up the final
                       serialized response output
        :param envelope: optional key that will be used to envelop the serialized
                         response
        """
        self.fields = fields
        self.envelope = envelope

    def __call__(self, f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            resp = await f(*args, **kwargs)
            if isinstance(resp, tuple):
                data, code, headers = unpack(resp)
                content = await marshal(data, self.fields, self.envelope)
                return JSONResponse(content=content, status_code=code, headers=headers)
            elif isinstance(resp, JSONResponse):
                return resp
            else:
                content = await marshal(resp, self.fields, self.envelope)
                return JSONResponse(content=content)
        return wrapper


class marshal_with_field:
    """
    A decorator that formats the return values of your methods with a single field.

    >>> from tomskit.utils import marshal_utils, fields
    >>> @marshal_with_field(fields.List(fields.Integer))
    ... async def get():
    ...     return ['1', 2, 3.0]
    ...
    >>> await get()
    [1, 2, 3]

    see :meth:`marshal_utils.marshal_with`
    """
    def __init__(self, field):
        """
        :param field: a single field with which to marshal the output.
        """
        if isinstance(field, type):
            self.field = field()
        else:
            self.field = field

    def __call__(self, f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            resp = await f(*args, **kwargs)

            if isinstance(resp, tuple):
                data, code, headers = unpack(resp)
                content = await self.field.format(data)
                return JSONResponse(content=content, status_code=code, headers=headers)
            elif isinstance(resp, JSONResponse):
                return resp
            else:
                content = await self.field.format(resp)
                return JSONResponse(content=content)

        return wrapper
