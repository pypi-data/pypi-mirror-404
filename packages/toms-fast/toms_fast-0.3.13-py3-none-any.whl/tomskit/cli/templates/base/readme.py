"""
Readme templates
Templates for generating README files.
"""


def get_readme_content(project_name: str, project_type: str) -> str:
    """Generate project root README content (simplified version)."""
    project_type_names = {
        "fastapi": "FastAPI",
        "celery": "Celery",
        "full": "FastAPI + Celery"
    }
    project_desc = project_type_names.get(project_type, project_type)
    
    content = f'''# {project_name}

基于 [toms-fast](https://github.com/tomszhou/toms-fast) 的 {project_desc} 项目。

## 📁 项目结构

```
{project_name}/
├── backend/              # 后端代码目录（详见 backend/README.md）
├── web/                  # 前端代码目录
└── README.md             # 项目说明文档
```

## 🚀 快速开始

详细的使用说明请查看 [backend/README.md](backend/README.md)。

## 🔗 相关链接

- [toms-fast 文档](https://github.com/tomszhou/toms-fast)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Celery 文档](https://docs.celeryq.dev/)
'''
    
    return content


def get_backend_readme_content(project_name: str, project_type: str) -> str:
    """Generate backend directory README content."""
    project_type_names = {
        "fastapi": "FastAPI",
        "celery": "Celery",
        "full": "FastAPI + Celery"
    }
    project_desc = project_type_names.get(project_type, project_type)
    
    # 基础内容
    content = f'''# {project_name} - Backend

基于 [toms-fast](https://github.com/tomszhou/toms-fast) 的 {project_desc} 后端应用。

## 🚀 快速开始

### 前置要求

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) (推荐使用 uv 管理依赖)

### 1. 安装依赖

使用 uv 安装项目依赖：

```bash
# 安装 uv (如果还没有安装)
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip:
pip install uv

# 安装项目依赖
uv sync

# 或安装开发依赖
uv sync --group dev
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和 Redis 连接信息
```

'''
    
    # 根据项目类型添加运行说明
    if project_type in ("fastapi", "full"):
        content += '''### 3. 初始化数据库迁移

```bash
# 创建初始迁移
uv run alembic -c migrations/alembic.ini revision --autogenerate -m 'Initial migration'

# 应用迁移到数据库
uv run alembic -c migrations/alembic.ini upgrade head
```

### 4. 运行 FastAPI 应用

```bash
# 使用 uv 运行（推荐）
uv run uvicorn main:app --reload

# 或激活虚拟环境后运行
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
uvicorn main:app --reload

# 或直接运行
python main.py
```

### 5. 访问 API

- API 文档: http://localhost:8000/docs (如果启用了文档)
- 健康检查: http://localhost:8000/health
- 用户 API: http://localhost:8000/api/v1/users

'''
    
    if project_type in ("celery", "full"):
        content += '''### 3. 运行 Celery Worker

```bash
# 使用 uv 运行（推荐）
uv run celery -A celery_app worker --loglevel=info

# 或激活虚拟环境后运行
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
celery -A celery_app worker --loglevel=info
```

### 4. 运行 Celery Beat（定时任务，可选）

```bash
uv run celery -A celery_app beat --loglevel=info
```

'''
    
    # 项目结构
    content += '''## 📁 项目结构

```
backend/
'''
    
    if project_type in ("fastapi", "full"):
        content += '''├── app/
│   ├── controllers/      # 控制器层（API 路由）
│   │   └── users/        # 用户控制器示例
│   ├── models/           # 数据库模型
│   ├── schemas/          # Pydantic 模型（请求/响应）
│   ├── services/         # 业务逻辑层
│   ├── middleware/       # 中间件目录
│   │   ├── request_id.py      # 请求 ID 追踪
│   │   └── resource_cleanup.py  # 资源清理
│   └── utils/            # 工具函数
├── main.py               # FastAPI 应用入口
'''
    
    if project_type in ("celery", "full"):
        content += '''├── celery_app.py          # Celery 应用入口
├── tasks/                # Celery 任务
│   └── example_task.py   # 示例任务
'''
    
    content += '''├── extensions/          # 扩展功能初始化
├── tests/                # 测试文件
├── logs/                 # 日志目录
├── migrations/           # 数据库迁移目录
├── pyproject.toml        # 项目配置和依赖（使用 uv 管理）
└── .env                  # 环境变量配置
```

'''
    
    # 使用指南
    if project_type in ("fastapi", "full"):
        content += '''## 📖 使用指南

### 添加新控制器

1. 在 `app/controllers/` 下创建新控制器目录
2. 创建 `resources.py` 定义 Resource
3. 在 `app/schemas/` 中创建对应的数据模型（请求/响应）
4. 创建 `module.py` 定义控制器初始化函数
5. 在 `main.py` 中调用初始化函数

### 定义 Resource

```python
from tomskit.server import Resource, api_doc, register_resource
from fastapi import Request

@register_resource(module="users", path="/users", tags=["用户管理"])
class UserResource(Resource):
    @api_doc(
        summary="获取用户列表",
        response_model=list[UserResponse]
    )
    async def get(self, request: Request):
        return []
```

'''
    
    if project_type in ("celery", "full"):
        content += '''### 定义 Celery 任务

```python
from celery import shared_task
from tomskit.celery import AsyncTaskRunner

@shared_task(name="my_task", queue="default")
def my_task(message: str):
    runner = AsyncTaskRunner(async_my_task)
    return runner.run(message)

async def async_my_task(message: str):
    # 实现异步任务逻辑
    return f"处理完成: {message}"
```

'''
    
    content += '''## 🔗 相关链接

- [toms-fast 文档](https://github.com/tomszhou/toms-fast)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Celery 文档](https://docs.celeryq.dev/)
'''
    
    return content
