"""
Orjson serializer for Celery.

This module provides orjson-based serialization support for Celery tasks and results.
Orjson is a fast, correct JSON library for Python that supports more types than the
standard json library.
"""

from __future__ import annotations

import typing as t

try:
    import orjson  # type: ignore[import-untyped]
except ImportError:
    orjson = None  # type: ignore[assignment]

from kombu.serialization import register


def dumps(obj: t.Any) -> bytes:
    """
    Serialize object to JSON bytes using orjson.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON bytes representation of the object
        
    Raises:
        ImportError: If orjson is not installed
    """
    if orjson is None:
        raise ImportError(
            "orjson is not installed. Please install it with: pip install orjson"
        )
    
    return orjson.dumps(
        obj,
        option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_DATACLASS
    )


def loads(data: bytes | str) -> t.Any:
    """
    Deserialize JSON bytes/string to Python object using orjson.
    
    Args:
        data: JSON bytes or string to deserialize
        
    Returns:
        Deserialized Python object
        
    Raises:
        ImportError: If orjson is not installed
    """
    if orjson is None:
        raise ImportError(
            "orjson is not installed. Please install it with: pip install orjson"
        )
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    return orjson.loads(data)


def register_orjson_serializer() -> None:
    """
    Register orjson serializer with Kombu (Celery's messaging library).
    
    This function registers 'orjson' as a valid serializer name that can be used
    in Celery configuration (CELERY_TASK_SERIALIZER, CELERY_RESULT_SERIALIZER, etc.).
    
    Raises:
        ImportError: If orjson is not installed
    """
    if orjson is None:
        raise ImportError(
            "orjson is not installed. Please install it with: pip install orjson"
        )
    
    register(
        'orjson',
        dumps,
        loads,
        content_type='application/x-orjson',
        content_encoding='utf-8',
    )
