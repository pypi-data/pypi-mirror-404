import uuid
from typing import Any, Dict, Type
from pydantic_core import core_schema
from datetime import datetime

def IntRange(minimum: int, maximum: int) -> Type[int]:
    """
    Factory for a constrained int subtype: value must be in [minimum, maximum].

    Usage:
        class User(BaseModel):
            age: IntRange(18, 35)
    """
    if minimum > maximum:
        raise ValueError(f"IntRange: minimum ({minimum}) cannot exceed maximum ({maximum})")

    class IntRangeType(int):
        @classmethod
        def __get_pydantic_core_schema__(cls, source, handler) -> core_schema.CoreSchema:
            # Use the built-in int_schema with ge/le
            return core_schema.int_schema(strict=True, ge=minimum, le=maximum)

        @classmethod
        def __modify_json_schema__(cls, schema: Dict[str, Any]) -> None:
            schema.update(
                type="integer",
                minimum=minimum,
                maximum=maximum,
                description=f"Integer in range [{minimum}, {maximum}]"
            )

    IntRangeType.__name__ = f"IntRange_{minimum}_{maximum}"
    return IntRangeType

class Boolean:
    """
    Type that parses "true"/"false"/"1"/"0" into bool.
    """

    @staticmethod
    def _parse_bool(v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if v is None or (isinstance(v, str) and not v):
            raise ValueError("Boolean type must be non-null")
        s = str(v).lower()
        if s in ("true", "1"):
            return True
        if s in ("false", "0"):
            return False
        raise ValueError(f"Invalid literal for Boolean(): {v!r}")

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.bool_schema(strict=True),
            core_schema.chain_schema([
                core_schema.str_schema(strict=False, coerce_numbers_to_str=True),
                core_schema.no_info_plain_validator_function(cls._parse_bool),
            ]),
        ], mode='smart')

    @classmethod
    def __modify_json_schema__(cls, schema: Dict[str, Any]) -> None:
        schema.update(
            type="boolean",
            description="Accepts true/false/1/0 (case-insensitive)"
        )


class PhoneNumber(str):
    """
    Phone number type for Chinese mobile numbers (11 digits, starts with 1[3-9]).
    """
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler) -> core_schema.CoreSchema:
        return core_schema.str_schema(
            strict=True,
            pattern=r"^1[3-9]\d{9}$",
            regex_engine="python-re"
        )

    @classmethod
    def __modify_json_schema__(cls, schema: Dict[str, Any]) -> None:
        schema.update(
            type="string",
            pattern=r"^1[3-9]\d{9}$",
            description="Chinese mobile phone number"
        )

class EmailStr(str):
    """
    Email address type.
    """
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler) -> core_schema.CoreSchema:
        return core_schema.str_schema(
            strict=True,
            pattern=r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
            regex_engine="python-re"
        )

    @classmethod
    def __modify_json_schema__(cls, schema: Dict[str, Any]) -> None:
        schema.update(
            type="string",
            format="email",
            description="Email address"
        )

def StrLen(max_length: int, min_length: int = 0) -> Type[str]:
    """
    Factory for a constrained string subtype: string length must be in [min_length, max_length].

    Usage:
        class User(BaseModel):
            username: StrLen(3, 20)  # between 3-20 characters
            name: StrLen(1, 50)      # between 1-50 characters
    """
    if min_length < 0:
        raise ValueError(f"StrLen: min_length ({min_length}) cannot be negative")
    if min_length > max_length:
        raise ValueError(f"StrLen: min_length ({min_length}) cannot exceed max_length ({max_length})")
    
    min_length = max_length if min_length == 0 else min_length

    class StrLenType(str):
        @classmethod
        def __get_pydantic_core_schema__(cls, source, handler) -> core_schema.CoreSchema:
            return core_schema.str_schema(
                strict=True,
                min_length=min_length,
                max_length=max_length
            )

        @classmethod
        def __modify_json_schema__(cls, schema: Dict[str, Any]) -> None:
            schema.update(
                type="string",
                minLength=min_length,
                maxLength=max_length,
                description=f"String with length between {min_length} and {max_length} characters"
            )

    StrLenType.__name__ = f"StrLen_{min_length}_{max_length}"
    return StrLenType

def DatetimeString(format: str, argument: str = "datetime") -> Type[str]:
    """
    Factory for datetime string type with custom format validation.
    
    Usage:
        class Event(BaseModel):
            created_at: DatetimeString("%Y-%m-%d %H:%M:%S")
            date_only: DatetimeString("%Y-%m-%d", "date")
    """
    
    class DatetimeStrType(str):
        @classmethod
        def __get_pydantic_core_schema__(cls, source, handler) -> core_schema.CoreSchema:
            def validate_datetime(value: str) -> str:
                try:
                    datetime.strptime(value, format)
                    return value
                except ValueError:
                    raise ValueError(f"Invalid {argument}: '{value}', expected format: {format}")
            
            return core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_datetime)
            ])
        
        @classmethod
        def __modify_json_schema__(cls, schema: Dict[str, Any]) -> None:
            # 根据格式判断是日期还是日期时间
            is_datetime = any(x in format for x in ["%H", "%M", "%S"])
            
            schema.update(
                type="string",
                format="date-time" if is_datetime else "date",
                description=f"{argument.title()} string in format: {format}",
                example=datetime.now().strftime(format)
            )
    
    DatetimeStrType.__name__ = f"DatetimeString_{argument}"
    return DatetimeStrType


class UUIDType(str):
    """
    UUID 类型验证器
    用于验证字符串是否为有效的 UUID 格式
    """
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler) -> core_schema.CoreSchema:
        def validate_uuid(value: Any) -> str:
            """验证 UUID 格式"""
            if value == "":
                return value
                
            try:
                # 验证是否为有效的 UUID
                uuid_obj = uuid.UUID(str(value))
                # 返回标准化的 UUID 字符串
                return str(uuid_obj)
            except (ValueError, TypeError):
                raise ValueError(f"{value} is not a valid UUID")
        
        return core_schema.no_info_plain_validator_function(
            validate_uuid
        )
    
    @classmethod
    def __modify_json_schema__(cls, schema: Dict[str, Any]) -> None:
        schema.update(
            type="string",
            format="uuid",
            pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            description="A valid UUID string"
        )
    
    @classmethod
    def is_valid_uuid(cls, value: str) -> bool:
        """
        检查字符串是否为有效的 UUID
        
        Args:
            value: 待验证的字符串
            
        Returns:
            bool: 如果是有效的 UUID 返回 True，否则返回 False
        """
        if not value or value == "":
            return False
            
        try:
            uuid.UUID(value)
            return True
        except (ValueError, TypeError):
            return False
        
# 预定义的常用日期时间格式
class CommonDateFormats:
    """常用的日期时间格式"""
    ISO_DATE = "%Y-%m-%d"                    # 2023-12-25
    ISO_DATETIME = "%Y-%m-%d %H:%M:%S"       # 2023-12-25 14:30:00
    ISO_DATETIME_MS = "%Y-%m-%d %H:%M:%S.%f" # 2023-12-25 14:30:00.123456
    US_DATE = "%m/%d/%Y"                     # 12/25/2023
    EU_DATE = "%d/%m/%Y"                     # 25/12/2023
    TIME_24H = "%H:%M:%S"                    # 14:30:00
    TIME_12H = "%I:%M:%S %p"                 # 02:30:00 PM


# 便捷的预定义类型
ISODate = DatetimeString(CommonDateFormats.ISO_DATE, "date")
ISODateTime = DatetimeString(CommonDateFormats.ISO_DATETIME, "datetime")
USDate = DatetimeString(CommonDateFormats.US_DATE, "date")
EUDate = DatetimeString(CommonDateFormats.EU_DATE, "date")
Time24H = DatetimeString(CommonDateFormats.TIME_24H, "time")
Time12H = DatetimeString(CommonDateFormats.TIME_12H, "time")


