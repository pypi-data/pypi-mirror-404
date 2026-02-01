from typing import Any, Literal
from urllib.parse import quote_plus
from pydantic import Field, NonNegativeInt, PositiveInt, computed_field
from tomskit import TomsKitBaseSettings


class DatabaseConfig(TomsKitBaseSettings):
    """
    Configuration settings for the database
    """

    DB_TYPE: Literal["postgresql", "mysql"] = Field(
        description="Database type to use. OceanBase is MySQL-compatible.",
        default="mysql",
    )

    DB_HOST: str = Field(
        description="Hostname or IP address of the database server.",
        default="localhost",
    )

    DB_PORT: PositiveInt = Field(
        description="Port number on which the database server is listening.",
        default=5432,
    )

    DB_USERNAME: str = Field(
        description="Username for database authentication.",
        default="",
    )

    DB_PASSWORD: str = Field(
        description="Password for database authentication.",
        default="",
    )

    DB_DATABASE: str = Field(
        description="Name of the database to connect to.",
        default="tomskitdb",
    )

    DB_CHARSET: str = Field(
        description="Character set to use for the database connection.",
        default="",
    )

    DB_EXTRAS: str = Field(
        description="db extras options. Example: keepalives_idle=60&keepalives=1",
        default="",
    )

    SQLALCHEMY_DATABASE_URI_SCHEME: str = Field(
        description="db uri scheme",
        default="mysql+aiomysql",
    )

    SQLALCHEMY_DATABASE_SYNC_URI_SCHEME: str = Field(
        description="db uri scheme",
        default="mysql+pymysql",
    )

    @computed_field # type: ignore
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        db_extras = (
            f"{self.DB_EXTRAS}&client_encoding={self.DB_CHARSET}" if self.DB_CHARSET else self.DB_EXTRAS
        ).strip("&")
        db_extras = f"?{db_extras}" if db_extras else ""
        return (
            f"{self.SQLALCHEMY_DATABASE_URI_SCHEME}://"
            f"{quote_plus(self.DB_USERNAME)}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
            f"{db_extras}"
        )
    
    @computed_field # type: ignore
    @property
    def SQLALCHEMY_DATABASE_SYNC_URI(self) -> str:
        db_extras = (
            f"{self.DB_EXTRAS}&client_encoding={self.DB_CHARSET}" if self.DB_CHARSET else self.DB_EXTRAS
        ).strip("&")
        db_extras = f"?{db_extras}" if db_extras else ""
        return (
            f"{self.SQLALCHEMY_DATABASE_SYNC_URI_SCHEME}://"
            f"{quote_plus(self.DB_USERNAME)}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
            f"{db_extras}"
        )


    SQLALCHEMY_POOL_SIZE: NonNegativeInt = Field(
        description="pool size of SqlAlchemy",
        default=5,
    )

    SQLALCHEMY_MAX_OVERFLOW: NonNegativeInt = Field(
        description="max overflows for SqlAlchemy",
        default=5,
    )

    SQLALCHEMY_POOL_RECYCLE: NonNegativeInt = Field(
        description="SqlAlchemy pool recycle",
        default=1800,
    )

    SQLALCHEMY_POOL_PRE_PING: bool = Field(
        description="whether to enable pool pre-ping in SqlAlchemy",
        default=False,
    )

    SQLALCHEMY_ECHO: bool = Field(
        description="whether to enable SqlAlchemy echo",
        default=False,
    )

    SQLALCHEMY_POOL_ECHO: bool = Field(
        description="whether to enable pool echo in SqlAlchemy",
        default=False,
    )

    @computed_field # type: ignore
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self) -> dict[str, Any]:
        return {
            "pool_size": self.SQLALCHEMY_POOL_SIZE,
            "max_overflow": self.SQLALCHEMY_MAX_OVERFLOW,
            "pool_recycle": self.SQLALCHEMY_POOL_RECYCLE,
            "pool_pre_ping": self.SQLALCHEMY_POOL_PRE_PING,
            "echo": self.SQLALCHEMY_ECHO,
            "echo_pool": self.SQLALCHEMY_POOL_ECHO,
            # "connect_args": {"options": "-c timezone=UTC"},
        }
