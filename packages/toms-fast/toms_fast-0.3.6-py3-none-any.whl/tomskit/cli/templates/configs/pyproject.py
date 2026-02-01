"""
Configs init template
Template for generating configs/pyproject.py file.
"""

TEMPLATE='''
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING
from pydantic import Field
from pydantic_settings import BaseSettings, InitSettingsSource

if TYPE_CHECKING:
    from typing import Any


def _get_pyproject_toml_path() -> Path:
    """获取 pyproject.toml 文件路径"""
    # 获取项目根目录（当前文件在 configs/packaging/ 下，需要向上两级）
    project_root = Path(__file__).parent.parent.parent
    return project_root / "pyproject.toml"


def _load_project_from_toml() -> dict:
    """从 pyproject.toml 的 [project] 部分加载数据"""
    pyproject_path = _get_pyproject_toml_path()
    if not pyproject_path.exists():
        return {}
    
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
        return data.get("project", {})


class ProjectInitSettingsSource(InitSettingsSource):
    """自定义设置源，从 TOML 的 project 部分读取数据"""
    
    def __init__(self, settings_cls: type[BaseSettings], init_kwargs: dict[str, "Any"]):
        # 从 TOML 文件读取 project 部分的数据
        project_data = _load_project_from_toml()
        # 合并 TOML 数据和初始化参数（初始化参数优先级更高）
        merged_kwargs = {**project_data, **init_kwargs}
        super().__init__(settings_cls, merged_kwargs)


class PyProjectConfig(BaseSettings):
    """
    PyProject settings class.
    
    自动从 pyproject.toml 文件的 [project] 部分读取项目信息。
    可以直接访问：app_settings.project.name, app_settings.project.version 等
    """
    
    name: str = Field(description="PyProject name", default="")
    version: str = Field(description="PyProject version", default="")
    description: str = Field(description="PyProject description", default="")
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """自定义设置源，从 TOML 的 project 部分读取数据"""
        # 获取初始化参数
        init_kwargs = getattr(init_settings, 'init_kwargs', {})
        
        # 使用自定义的 ProjectInitSettingsSource 来读取 TOML 的 project 部分
        project_init_source = ProjectInitSettingsSource(
            settings_cls=settings_cls,
            init_kwargs=init_kwargs,
        )
        
        return (
            project_init_source,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

'''

