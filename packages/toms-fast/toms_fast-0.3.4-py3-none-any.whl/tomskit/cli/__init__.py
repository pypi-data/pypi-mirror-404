"""
toms-fast CLI 工具
"""

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Optional

from .scaffold import create_project


def init_migrations(project_path: Optional[Path] = None):
    """为已存在的项目初始化数据库迁移"""
    if project_path is None:
        project_path = Path.cwd()
    
    project_path = Path(project_path).resolve()
    
    # 检查是否在 backend 目录或项目根目录
    backend_path = project_path
    project_root = project_path
    if (project_path / "backend").exists():
        # 在项目根目录，使用 backend 目录
        backend_path = project_path / "backend"
        project_root = project_path
    elif not (project_path / "main.py").exists() and not (project_path / "app").exists():
        print("❌ 错误: 未找到项目文件，请确保在项目根目录或 backend 目录运行此命令")
        sys.exit(1)
    else:
        # 在 backend 目录，项目根目录是父目录
        project_root = project_path.parent
    
    # 获取项目名称
    project_name = project_root.name
    
    # 尝试从 pyproject.toml 读取项目名称
    pyproject_path = backend_path / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
                if "project" in pyproject_data and "name" in pyproject_data["project"]:
                    project_name = pyproject_data["project"]["name"]
        except Exception:
            # 如果读取失败，使用目录名称
            pass
    
    migrations_dir = backend_path / "migrations"
    alembic_ini = migrations_dir / "alembic.ini"
    
    # 检查是否已经初始化
    if migrations_dir.exists() and alembic_ini.exists():
        print("⚠️  警告: migrations 目录和 alembic.ini 已存在")
        response = input("是否重新初始化？这将覆盖现有配置 (y/N): ")
        if response.lower() != 'y':
            print("❌ 已取消")
            return
    
    print(f"🚀 正在为{project_name}项目初始化数据库迁移...")
    print(f"📁 后端路径: {backend_path}")
    print(f"📦 项目名称: {project_name}")
    
    # 创建 migrations 目录结构
    migrations_dir.mkdir(exist_ok=True)
    versions_dir = migrations_dir / "versions"
    versions_dir.mkdir(exist_ok=True)
    
    # 创建 __init__.py 文件
    (migrations_dir / "__init__.py").write_text('"""\n数据库迁移目录\n"""\n', encoding="utf-8")
    (versions_dir / "__init__.py").write_text('"""\n数据库迁移版本目录\n"""\n', encoding="utf-8")
    
    # 从模板创建配置文件
    from .templates.migrations import get_migrations_templates
    
    templates = get_migrations_templates(project_name)
    
    # 创建 migrations/alembic.ini
    if "alembic_ini" in templates:
        alembic_content = templates["alembic_ini"]()
        alembic_ini.write_text(alembic_content, encoding="utf-8")
        print("  ✓ 创建文件: migrations/alembic.ini")
    
    # 创建 migrations/env.py
    if "migrations_env_py" in templates:
        env_content = templates["migrations_env_py"]()
        (migrations_dir / "env.py").write_text(env_content, encoding="utf-8")
        print(f"  ✓ 创建文件: migrations/env.py")
    
    # 创建 migrations/script.py.mako
    if "migrations_script_py_mako" in templates:
        script_content = templates["migrations_script_py_mako"]()
        (migrations_dir / "script.py.mako").write_text(script_content, encoding="utf-8")
        print(f"  ✓ 创建文件: migrations/script.py.mako")
    
    print("\n✅ 数据库迁移初始化成功！")
    print("\n📝 下一步:")
    print("   # 创建初始迁移:")
    print("   uv run alembic -c migrations/alembic.ini revision --autogenerate -m 'Initial migration'")
    print("   # 应用迁移到数据库:")
    print("   uv run alembic -c migrations/alembic.ini upgrade head")


def main():
    """CLI 入口函数"""
    parser = argparse.ArgumentParser(
        description="toms-fast 项目脚手架生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # init 命令：创建新项目
    init_parser = subparsers.add_parser("init", help="创建新项目")
    init_parser.add_argument(
        "project_name",
        nargs="?",
        help="项目名称（将作为包名和目录名）"
    )
    init_parser.add_argument(
        "-d", "--dir",
        dest="target_dir",
        help="目标目录（默认为当前目录）",
        default=None
    )
    init_parser.add_argument(
        "-t", "--type",
        dest="project_type",
        choices=["fastapi", "celery", "full"],
        default="full",
        help="项目类型：fastapi（仅 FastAPI）、celery（仅 Celery）、full（FastAPI + Celery，默认）"
    )
    init_parser.add_argument(
        "--description",
        dest="description",
        help="项目描述（默认为：基于 toms-fast 的 FastAPI 应用）",
        default=None
    )
    
    # migrations 命令：初始化数据库迁移
    migrations_parser = subparsers.add_parser("migrations", help="为已存在的项目初始化数据库迁移")
    migrations_parser.add_argument(
        "-d", "--dir",
        dest="project_dir",
        help="项目目录（默认为当前目录）",
        default=None
    )
    
    args = parser.parse_args()
    
    # 如果没有指定命令，默认使用 init（向后兼容）
    if args.command is None:
        # 尝试解析为 init 命令的参数
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            project_name = sys.argv[1]
            # 解析其他参数
            target_dir = None
            project_type = "full"
            description = None
            
            i = 2
            while i < len(sys.argv):
                if sys.argv[i] in ("-d", "--dir") and i + 1 < len(sys.argv):
                    target_dir = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] in ("-t", "--type") and i + 1 < len(sys.argv):
                    project_type = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] in ("--description") and i + 1 < len(sys.argv):
                    description = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            # 验证项目名称
            if not project_name.replace("_", "").replace("-", "").isalnum():
                print("❌ 错误: 项目名称只能包含字母、数字、下划线和连字符")
                sys.exit(1)
            
            # 如果未提供描述，提示输入
            if not description:
                description = input("请输入项目描述（可选，直接回车使用默认值）: ").strip()
                if not description:
                    description = None
            
            # 创建脚手架
            try:
                create_project(project_name, target_dir, project_type, description)
            except Exception as e:
                print(f"❌ 创建项目失败: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            # 如果没有提供项目名称，提示输入
            project_name = input("请输入项目名称: ").strip()
            if not project_name:
                print("❌ 错误: 项目名称不能为空")
                sys.exit(1)
            
            # 验证项目名称
            if not project_name.replace("_", "").replace("-", "").isalnum():
                print("❌ 错误: 项目名称只能包含字母、数字、下划线和连字符")
                sys.exit(1)
            
            # 如果未提供描述，提示输入
            description = input("请输入项目描述（可选，直接回车使用默认值）: ").strip()
            if not description:
                description = None
            
            # 创建脚手架
            try:
                create_project(project_name, None, "full", description)
            except Exception as e:
                print(f"❌ 创建项目失败: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
    elif args.command == "init":
        # 如果未提供项目名称，提示输入
        project_name = args.project_name
        if not project_name:
            project_name = input("请输入项目名称: ").strip()
            if not project_name:
                print("❌ 错误: 项目名称不能为空")
                sys.exit(1)
        
        # 验证项目名称
        if not project_name.replace("_", "").replace("-", "").isalnum():
            print("❌ 错误: 项目名称只能包含字母、数字、下划线和连字符")
            sys.exit(1)
        
        # 如果未提供描述，提示输入
        description = args.description
        if not description:
            description = input("请输入项目描述（可选，直接回车使用默认值）: ").strip()
            if not description:
                description = None
        
        # 创建脚手架
        try:
            create_project(project_name, args.target_dir, args.project_type, description)
        except Exception as e:
            print(f"❌ 创建项目失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    elif args.command == "migrations":
        # 初始化 migrations
        try:
            init_migrations(args.project_dir)
        except Exception as e:
            print(f"❌ 初始化 migrations 失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
