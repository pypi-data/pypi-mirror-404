from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional

from sqlalchemy import CHAR as sa_CHAR
from sqlalchemy import JSON as sa_JSON
from sqlalchemy import BigInteger as sa_BigInteger
from sqlalchemy import Boolean as sa_Boolean
from sqlalchemy import Column as sa_Column
from sqlalchemy import DateTime as sa_DateTime
from sqlalchemy import Float as sa_Float
from sqlalchemy import ForeignKey as sa_ForeignKey
from sqlalchemy import Index as sa_Index
from sqlalchemy import Integer as sa_Integer
from sqlalchemy import LargeBinary as sa_LargeBinary
from sqlalchemy import MetaData as sa_MetaData
from sqlalchemy import Numeric as sa_Numeric
from sqlalchemy import PickleType as sa_PickleType
from sqlalchemy import PrimaryKeyConstraint as sa_PrimaryKeyConstraint
from sqlalchemy import Sequence as sa_Sequence
from sqlalchemy import String as sa_String
from sqlalchemy import Text as sa_Text
from sqlalchemy import UniqueConstraint as sa_UniqueConstraint
from sqlalchemy import and_ as sa_and_
from sqlalchemy import delete as sa_delete
from sqlalchemy import func as sa_func
from sqlalchemy import insert as sa_insert
from sqlalchemy import select as sa_select
from sqlalchemy import text as sa_text
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship as sa_relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.sql import Select

from tomskit.sqlalchemy.pagination import Pagination, SelectPagination

__all__ = [
    "SQLAlchemy",
    "Pagination",
    "SelectPagination"
]
# Define a naming convention for indexes and constraints in MySQL
DB_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

# Define metadata with the naming convention
metadata = sa_MetaData(naming_convention=DB_INDEXES_NAMING_CONVENTION)

# Base model class for all models
# Base = declarative_base(metadata=metadata)


# Define the SQLAlchemy class
class SQLAlchemy(ABC):
    # Define all the common SQLAlchemy constructs
    class Model(AsyncAttrs, DeclarativeBase):
        metadata = metadata

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
    text = staticmethod(sa_text)
    ForeignKey = sa_ForeignKey
    Index = sa_Index
    uuid = sa_CHAR(36)  # Define a UUID column
    PrimaryKeyConstraint = sa_PrimaryKeyConstraint
    UniqueConstraint = sa_UniqueConstraint
    select = staticmethod(sa_select)
    delete = staticmethod(sa_delete)
    update = staticmethod(sa_update)
    insert = staticmethod(sa_insert)
    func = sa_func
    relationship = staticmethod(sa_relationship)
    and_ = staticmethod(sa_and_)
    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None  


    @abstractmethod
    async def paginate(self,
        select: Select[Any], 
        *, 
        page: int | None = None,
        per_page: int | None = None,
        max_per_page: int | None = None,
        error_out: bool = True,
        count: bool = True
    ) -> Pagination:
        raise NotImplementedError

    @property
    def session(self) -> AsyncSession:
        raise NotImplementedError
    
    @abstractmethod
    def create_session(self) -> AsyncSession:
        raise NotImplementedError
    
    @abstractmethod
    async def close_session(self):
        raise NotImplementedError
    
    @abstractmethod
    def initialize_session_pool(self, db_url: str):
        raise NotImplementedError
    
    @abstractmethod
    async def close_session_pool(self):
        raise NotImplementedError


