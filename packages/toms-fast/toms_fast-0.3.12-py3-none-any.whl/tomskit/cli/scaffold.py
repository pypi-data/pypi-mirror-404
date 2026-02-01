"""
项目脚手架生成器
"""

from pathlib import Path

from .templates_config import (
    get_directory_structure,
    get_file_templates,
    get_template_functions,
)


class ProjectScaffold:
    """项目脚手架生成器"""
    
    def __init__(self, project_name: str, target_dir: str | None = None, project_type: str = "full", description: str | None = None):
        self.project_name = project_name
        current_dir = Path.cwd()
        
        # 如果未指定目标目录，检查当前目录名是否与项目名一致
        if target_dir is None:
            if current_dir.name == project_name:
                # 当前目录名与项目名一致，直接使用当前目录
                self.target_dir = current_dir
            else:
                # 当前目录名与项目名不一致，创建新目录
                self.target_dir = current_dir / project_name
        else:
            self.target_dir = Path(target_dir)
        
        self.project_path = self.target_dir / "backend"  # 代码放到 backend 目录
        self.project_type = project_type
        self.description = description
        self.templates = get_template_functions(project_name, project_type, description)
        
    def create(self):
        """创建项目结构"""
        project_type_names = {
            "fastapi": "FastAPI",
            "celery": "Celery",
            "full": "FastAPI + Celery"
        }
        print(f"🚀 正在创建项目: {self.project_name}")
        print(f"📦 项目类型: {project_type_names.get(self.project_type, self.project_type)}")
        print(f"📁 目标目录: {self.target_dir}")
        
        # 检查目录是否已存在
        if self.target_dir.exists():
            # 检查是否已有 backend 或 web 目录
            backend_exists = (self.target_dir / "backend").exists()
            web_exists = (self.target_dir / "web").exists()
            
            if backend_exists or web_exists:
                print(f"⚠️  警告: 目录 {self.target_dir} 中已存在项目结构")
                if backend_exists:
                    print(f"   - backend/ 目录已存在")
                if web_exists:
                    print(f"   - web/ 目录已存在")
                response = input(f"是否继续？这将覆盖现有文件 (y/N): ")
                if response.lower() != 'y':
                    print("❌ 已取消")
                    return
            elif any(self.target_dir.iterdir()):
                # 目录不为空但没有 backend/web，询问是否继续
                response = input(f"⚠️  目录 {self.target_dir} 已存在且不为空，是否继续？(y/N): ")
                if response.lower() != 'y':
                    print("❌ 已取消")
                    return
        
        # 创建 web 目录（前端代码）
        web_dir = self.target_dir / "web"
        web_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ 创建目录: web/")
        
        # 创建目录结构
        self._create_directories()
        
        # 创建文件（README 单独处理，放到项目根目录）
        self._create_files()
        
        print("\n✅ 项目创建成功！")
        print("\n📝 下一步:")
        # 如果目标目录就是当前目录，使用相对路径
        if self.target_dir == Path.cwd():
            print("   cd backend")
        else:
            print(f"   cd {self.target_dir}/backend")
        print("   uv sync  # 安装依赖（使用 uv 管理）")
        print("   cp .env.example .env")
        print("   # 编辑 .env 文件配置数据库和 Redis")
        
        if self.project_type in ("fastapi", "full"):
            print("\n   # 数据库迁移:")
            print("   # 1. 创建初始迁移:")
            print("   uv run alembic -c migrations/alembic.ini revision --autogenerate -m 'Initial migration'")
            print("   # 2. 应用迁移到数据库:")
            print("   uv run alembic -c migrations/alembic.ini upgrade head")
            print("\n   # 运行 FastAPI 应用:")
            print("   uv run uvicorn main:app --reload")
        if self.project_type in ("celery", "full"):
            print("   # 运行 Celery Worker:")
            print("   uv run celery -A celery_app worker --loglevel=info")
        
    def _create_directories(self):
        """创建目录结构（从配置文件读取）"""
        directory_structure = get_directory_structure(self.project_type)
        for dir_path_str, need_init in directory_structure.items():
            dir_path = self.project_path / dir_path_str
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # 如果需要，创建 __init__.py
            if need_init:
                (dir_path / "__init__.py").touch()
                print(f"  ✓ 创建目录: {dir_path_str}/ (含 __init__.py)")
            else:
                print(f"  ✓ 创建目录: {dir_path_str}/")
    
    def _create_files(self):
        """创建所有文件（从配置文件读取）"""
        file_templates = get_file_templates(self.project_type)
        for file_path_str, template_key in file_templates.items():
            # README.md 放到项目根目录（简化版）
            if file_path_str == "README.md":
                template_func = self.templates.get("readme_md")
                if template_func is None:
                    print(f"  ⚠️  警告: 模板 'readme_md' 未找到，跳过文件: {file_path_str}")
                    continue
                content = template_func()
                readme_path = self.target_dir / "README.md"
                readme_path.write_text(content, encoding="utf-8")
                print(f"  ✓ 创建文件: README.md")
                
                # 同时创建 backend 目录的 README.md（详细版）
                backend_readme_func = self.templates.get("backend_readme_md")
                if backend_readme_func:
                    backend_content = backend_readme_func()
                    backend_readme_path = self.project_path / "README.md"
                    backend_readme_path.write_text(backend_content, encoding="utf-8")
                    print(f"  ✓ 创建文件: backend/README.md")
                continue
            
            # 获取模板内容
            template_func = self.templates.get(template_key)
            if template_func is None:
                print(f"  ⚠️  警告: 模板 '{template_key}' 未找到，跳过文件: {file_path_str}")
                continue
            
            content = template_func()
            self._write_file(file_path_str, content)
    
    def _write_file(self, relative_path: str, content: str):
        """写入文件"""
        file_path = self.project_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        print(f"  ✓ 创建文件: {relative_path}")


def create_project(project_name: str, target_dir: str | None = None, project_type: str = "full", description: str | None = None):
    """创建项目的便捷函数"""
    scaffold = ProjectScaffold(project_name, target_dir, project_type, description)
    scaffold.create()
