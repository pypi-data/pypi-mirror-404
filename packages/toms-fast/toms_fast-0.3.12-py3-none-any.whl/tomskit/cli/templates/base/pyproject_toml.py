"""
Pyproject toml template
Template for generating pyproject.toml file.
"""

TEMPLATE = '''[project]
name = "{project_name}"
version = "0.1.0"
description = "{description}"
requires-python = ">=3.11"
dependencies = [
    # 基础框架和工具库（包含 SQLAlchemy、Alembic、Celery、Redis 等）
    "toms-fast>=0.2.2",
    # 数据库迁移工具
    "alembic>=1.13.0",
    # 环境变量管理
    "python-dotenv>=1.0.0",
    # ASGI 服务器
    "uvicorn[standard]>=0.27.0",
    # 生产环境 ASGI 服务器
    "gunicorn>=21.2.0",
    "hypercorn>=0.16.0",
    # 异步支持库
    "greenlet>=3.0.0",
    # MySQL 异步驱动（应用运行时使用）
    "aiomysql>=0.2.0",
    # MySQL 同步驱动（Alembic 数据库迁移需要）
    "pymysql>=1.1.0",
]

[tool.uv]
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"

[dependency-groups]
dev = [
    "pytest>=8.3.5",
    "pytest-asyncio>=0.26.0",
    "httpx>=0.27.0",
]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true

[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "basic"
reportMissingImports = true
reportMissingTypeStubs = false
# 虚拟环境配置（uv sync 会在当前目录创建 .venv）
venvPath = "."
venv = ".venv"
# 注意：如果 Pyright 仍然无法解析导入，请确保：
# 1. 已运行 uv sync 安装依赖
# 2. 在 VS Code 中重新加载窗口（Cmd/Ctrl + Shift + P -> Reload Window）
# 3. 或重启 IDE

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
'''
