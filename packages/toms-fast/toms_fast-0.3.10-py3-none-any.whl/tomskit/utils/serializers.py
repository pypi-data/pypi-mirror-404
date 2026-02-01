import asyncio
import inspect
from collections.abc import Sequence, Iterable
from typing import Any, Type, TypeVar, get_origin, get_args
from pydantic import BaseModel
from pydantic.fields import FieldInfo

T = TypeVar("T", bound=BaseModel)


class AsyncSerializer:
    """通用异步序列化器 (Pydantic V2 版本)
    
    功能：
    1. 将 ORM 对象 (SQLAlchemy) 或 字典 转换为 Pydantic 模型
    2. 自动识别并 await 异步属性 (Async Properties)
    3. 自动调用函数/异步函数：如果字典值或对象属性是 callable，会自动调用并 await（如果是异步）
    4. 并发处理 List 类型的嵌套字段
    5. 支持混合数据源 (Object + Dict)
    6. 正确处理 Pydantic V2 的 validation_alias (支持 AliasChoices, AliasPath)
    
    使用示例：
        # 字典中的函数
        data = {"name": lambda: "John", "age": async_func}
        result = await AsyncSerializer.serialize(UserModel, data)
        
        # 对象属性是异步函数
        class User:
            @property
            async def full_name(self):
                return f"{self.first} {self.last}"
    """
    
    # 字段元数据缓存
    _field_keys_cache: dict[tuple[Type, str], list[str]] = {}
    _pydantic_keys_cache: dict[tuple[Type, str], str] = {}
    
    # 批处理大小常量
    BATCH_SIZE = 100

    @classmethod
    async def serialize(cls, model_cls: Type[T], source_data: Any) -> T | None:
        """
        单对象序列化入口
        
        Args:
            model_cls: Pydantic 模型类
            source_data: 数据源 (ORM 对象 / 字典 / 混合体)
            
        Returns:
            序列化后的 Pydantic 模型实例，如果 source_data 为 None 则返回 None
        """
        if source_data is None:
            return None

        # 优化：如果源数据本身就是该模型的实例，直接返回 (避免重复序列化)
        if isinstance(source_data, model_cls):
            return source_data

        data: dict[str, Any] = {}

        for field_name, field_info in model_cls.model_fields.items():
            keys = cls._get_cached_keys(model_cls, field_name, field_info)
            raw_value = await cls._get_value(source_data, keys)
            resolved_value = await cls._resolve_value(raw_value, field_info.annotation)

            # 处理默认值：如果字段有默认值且值为 None，跳过让 Pydantic 使用默认值
            # 但如果默认值本身就是 None，则传递 None
            if resolved_value is None:
                has_default = field_info.default is not ...
                has_default_factory = field_info.default_factory is not None
                if (has_default or has_default_factory) and not (has_default and field_info.default is None):
                    continue

            pydantic_key = cls._get_cached_pydantic_key(model_cls, field_name, field_info)
            data[pydantic_key] = resolved_value

        return model_cls(**data)

    @classmethod
    async def serialize_list(cls, model_cls: Type[T], items: Sequence[Any] | Iterable[Any]) -> list[T]:
        """列表序列化入口（并发处理）
        
        Args:
            model_cls: Pydantic 模型类
            items: 待序列化的对象列表
            
        Returns:
            序列化后的模型列表（过滤掉 None 值）
        """
        if not items:
            return []

        # 优化：避免不必要的类型检查和转换
        if isinstance(items, list):
            items_list = items
        else:
            items_list = list(items)
        
        if not items_list:
            return []

        if len(items_list) <= cls.BATCH_SIZE:
            results = await asyncio.gather(*(
                cls.serialize(model_cls, item) for item in items_list
            ))
            return [item for item in results if item is not None]
        else:
            results = []
            for i in range(0, len(items_list), cls.BATCH_SIZE):
                batch = items_list[i:i + cls.BATCH_SIZE]
                batch_results = await asyncio.gather(*(
                    cls.serialize(model_cls, item) for item in batch
                ))
                results.extend(batch_results)
        return [item for item in results if item is not None]

    @classmethod
    async def serialize_pagination(
        cls, 
        pagination_obj: Any, 
        model_cls: Type[T]
    ) -> dict[str, Any]:
        """分页对象序列化入口
        
        假设 pagination_obj 具有 items, page, per_page(或 limit), total 属性
        
        Args:
            pagination_obj: 分页对象，支持不同分页库的属性命名
            model_cls: 数据项的 Pydantic 模型类
            
        Returns:
            包含 page, limit, total, has_more, data 的字典
        """
        limit = getattr(pagination_obj, 'per_page', None) or getattr(pagination_obj, 'limit', 10)
        limit = int(limit) if limit else 10
        page = getattr(pagination_obj, 'page', 1)
        total = getattr(pagination_obj, 'total', 0)
        items = getattr(pagination_obj, 'items', [])
        serialized_items = await cls.serialize_list(model_cls, items)

        return {
            "page": page,
            "limit": limit,
            "total": total,
            "has_more": (page * limit) < total,
            "data": serialized_items
        }

    @classmethod
    def _get_cached_keys(cls, model_cls: Type, field_name: str, field_info: FieldInfo) -> list[str]:
        """获取缓存的字段键名列表（用于从源数据中取值）"""
        cache_key = (model_cls, field_name)
        if cache_key not in cls._field_keys_cache:
            cls._field_keys_cache[cache_key] = cls._extract_keys_from_alias(field_info, field_name)
        return cls._field_keys_cache[cache_key]

    @classmethod
    def _get_cached_pydantic_key(cls, model_cls: Type, field_name: str, field_info: FieldInfo) -> str:
        """获取缓存的 Pydantic 键名（用于传递给 Pydantic）"""
        cache_key = (model_cls, field_name)
        if cache_key not in cls._pydantic_keys_cache:
            cls._pydantic_keys_cache[cache_key] = cls._get_pydantic_key(field_info, field_name)
        return cls._pydantic_keys_cache[cache_key]

    @staticmethod
    def _extract_keys_from_alias(field_info: FieldInfo, field_name: str) -> list[str]:
        """从 FieldInfo 中提取可能的键名列表（用于从源数据中取值）"""
        validation_alias = field_info.validation_alias
        
        if validation_alias is None:
            return [field_name]
        
        if isinstance(validation_alias, str):
            return [validation_alias, field_name]
        
        if isinstance(validation_alias, tuple):
            keys = [str(k) for k in validation_alias if isinstance(k, str)]
            if keys:
                keys.append(field_name)
                return keys
            return [field_name]
        
        try:
            return [str(validation_alias), field_name]
        except Exception:
            return [field_name]

    @staticmethod
    def _get_pydantic_key(field_info: FieldInfo, field_name: str) -> str:
        """获取传递给 Pydantic 的键名"""
        validation_alias = field_info.validation_alias
        
        if validation_alias is None:
            return field_name
        
        if isinstance(validation_alias, str):
            return validation_alias
        
        if isinstance(validation_alias, tuple):
            keys = [str(k) for k in validation_alias if isinstance(k, str)]
            if keys:
                return keys[0]
            return field_name
        
        try:
            return str(validation_alias)
        except Exception:
            return field_name

    @staticmethod
    async def _get_value(source: Any, keys: list[str]) -> Any:
        """智能取值：支持字典 Key 和对象 Attribute
        
        按 keys 列表的顺序尝试取值。对于字典，区分"键不存在"和"键存在但值为 None"。
        如果获取到异步属性（协程），会立即 await。
        
        Args:
            source: 数据源（字典或对象）
            keys: 可能的键名列表，按优先级排序
            
        Returns:
            找到的值，如果所有键都不存在则返回 None
        """
        if source is None:
            return None

        is_dict = isinstance(source, dict)

        for key in keys:
            if is_dict:
                if key in source:
                    value = source[key]
                    if inspect.isawaitable(value):
                        value = await value
                    return value
                continue

            try:
                value = getattr(source, key)
                if inspect.isawaitable(value):
                    value = await value
                # 对于对象属性，如果找到了属性（即使值为 None），也应该返回
                # 因为 None 可能是有效值（特别是对于 Optional 类型）
                return value
            except (AttributeError, TypeError):
                continue

        return None

    @classmethod
    async def _resolve_value(cls, value: Any, type_annotation: Any = None) -> Any:
        """递归解析值：处理协程、函数、嵌套模型、列表、字典、集合等
        
        支持的 value 类型：
        1. Awaitable: 自动 await
        2. Callable: 自动调用，如果返回 awaitable 则 await
        3. List/Sequence: 如果元素是 Pydantic 模型，并发序列化
        4. Dict: 如果值是 Pydantic 模型，并发序列化值
        5. Set: 如果元素是 Pydantic 模型，并发序列化
        6. Pydantic Model: 递归序列化
        
        Args:
            value: 待解析的值（可能是协程、函数、嵌套模型等）
            type_annotation: 类型注解，用于指导解析过程
            
        Returns:
            解析后的值
        """
        # 如果值是协程，直接 await（用于处理异步属性返回的协程）
        # 注意：不支持直接传递协程对象（如 get_async_name()），应该传递函数对象
        if inspect.isawaitable(value):
            value = await value

        if value is None:
            return None

        # 处理可调用对象（函数）：支持同步函数和异步函数对象
        # 不支持传递协程对象（inspect.iscoroutine），应该传递函数对象
        if (callable(value) and 
            not isinstance(value, type) and 
            not inspect.iscoroutine(value)):
            try:
                # 调用函数（同步或异步）
                result = value()
                # 如果返回 awaitable，则 await
                if inspect.isawaitable(result):
                    result = await result
                value = result
                if value is None:
                    return None
            except (TypeError, ValueError, Exception):
                pass

        if type_annotation is None:
            return value

        origin = get_origin(type_annotation)
        args = get_args(type_annotation)

        # 处理 Union 类型（包括 Optional[T]）
        if origin is not None:
            origin_name = getattr(origin, '__name__', None) or str(origin)
            is_union = (
                'Union' in origin_name or 
                (args and type(None) in args) or
                (hasattr(origin, '__origin__') and 
                 getattr(origin, '__origin__', None) is not None)
            )
            
            if is_union and args:
                # 根据实际值类型选择最匹配的 Union 成员类型
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    # 尝试根据值的类型选择匹配的 Union 成员
                    matched_type = cls._match_union_type(value, non_none_args)
                    if matched_type:
                        type_annotation = matched_type
                    else:
                        type_annotation = non_none_args[0]
                    origin = get_origin(type_annotation)
                    args = get_args(type_annotation)

        # 处理列表类型
        is_annotation_list = origin is None and type_annotation is list
        is_annotation_tuple = origin is None and type_annotation is tuple
        is_list_type = origin is list or is_annotation_list
        is_tuple_type = origin is tuple or is_annotation_tuple
        is_sequence_type = origin is not None and origin not in (list, tuple) and isinstance(value, (list, tuple, Sequence))
        
        if is_list_type or is_tuple_type or is_sequence_type:
            is_original_tuple = isinstance(value, tuple)
            
            if not isinstance(value, (list, tuple)):
                value = list(value) if value else []
            
            if not value:
                return () if is_original_tuple else []

            inner_type = args[0] if args else None

            if inner_type and isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                # 对于大列表，分批处理以避免资源耗尽
                results = await cls._batch_serialize(inner_type, value, cls.BATCH_SIZE)
                return tuple(results) if is_original_tuple or is_tuple_type else list(results)
            else:
                return tuple(value) if is_original_tuple or is_tuple_type else value

        # 处理字典类型
        if origin is dict or isinstance(value, dict):
            if not value:
                return {}

            value_type = args[1] if len(args) > 1 else None

            if (value_type and isinstance(value_type, type) and 
                issubclass(value_type, BaseModel)):
                keys = list(value.keys())
                # 对于大字典，分批处理以避免资源耗尽
                values_list = await cls._batch_serialize(
                    value_type, 
                    [value[k] for k in keys], 
                    cls.BATCH_SIZE
                )
                return dict(zip(keys, values_list))
            else:
                return value

        # 处理集合类型
        if origin is set or isinstance(value, set):
            if not value:
                return set()

            inner_type = args[0] if args else None

            if inner_type and isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                # 对于大集合，分批处理以避免资源耗尽
                value_list = list(value)
                serialized_items = await cls._batch_serialize(inner_type, value_list, cls.BATCH_SIZE)
                return set(serialized_items)
            else:
                return value

        # 处理嵌套模型
        if isinstance(type_annotation, type) and issubclass(type_annotation, BaseModel):
            return await cls.serialize(type_annotation, value)

        return value

    @classmethod
    async def _batch_serialize(cls, model_cls: Type[T], items: list[Any], batch_size: int) -> list[T | None]:
        """批量序列化辅助方法，统一处理大列表的分批逻辑
        
        Args:
            model_cls: Pydantic 模型类
            items: 待序列化的项目列表
            batch_size: 每批的大小
            
        Returns:
            序列化后的模型列表（可能包含 None）
        """
        if len(items) <= batch_size:
            return list(await asyncio.gather(*(
                cls.serialize(model_cls, item) for item in items
            )))
        
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(*(
                cls.serialize(model_cls, item) for item in batch
            ))
            results.extend(batch_results)
        return results

    @staticmethod
    def _match_union_type(value: Any, union_args: list[Any]) -> Any | None:
        """根据实际值类型匹配 Union 成员类型
        
        Args:
            value: 实际值
            union_args: Union 类型的所有非 None 成员类型列表
            
        Returns:
            匹配的类型，如果没有匹配则返回 None
        """
        value_type = type(value)
        
        # 精确匹配（最快）
        if value_type in union_args:
            return value_type
        
        # 检查是否是子类（使用 isinstance，比 issubclass 更快）
        for arg in union_args:
            if isinstance(arg, type) and isinstance(value, arg):
                return arg
        
        # 检查是否是 BaseModel 子类（优化：先检查是否是 BaseModel 实例）
        if isinstance(value, BaseModel):
            value_class = value.__class__
            for arg in union_args:
                if isinstance(arg, type) and issubclass(arg, BaseModel):
                    # 优化：先检查类是否相同，再检查是否是子类
                    if value_class is arg or issubclass(value_class, arg):
                        return arg
        
        return None
