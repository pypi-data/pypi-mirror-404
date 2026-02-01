"""
TomsKit 配置基类模块

提供统一的配置基类，所有配置类都应该继承 TomsKitBaseSettings。
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class TomsKitBaseSettings(BaseSettings):
    """
    TomsKit 配置基类
    
    所有配置类都应该继承此类，以统一管理环境变量文件和配置行为。
    提供统一的 .env 文件加载和配置项处理。

    需要在 .env 文件中配置 TOMSKIT_ENV_FILE 变量，指定环境变量文件路径。如果未配置，则使用 .env 文件。
    
    Example:
        from tomskit import TomsKitBaseSettings
        
        class MyConfig(TomsKitBaseSettings):
            MY_SETTING: str = "default"
    """

    model_config = SettingsConfigDict(
        env_file=os.getenv("TOMSKIT_ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )
