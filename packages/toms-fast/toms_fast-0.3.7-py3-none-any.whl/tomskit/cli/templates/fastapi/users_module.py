"""
Users module template
Template for generating app/controllers/users/module.py file.
"""

TEMPLATE = '''"""
用户控制器初始化
"""

from tomskit.server import FastApp, FastModule


def init_user_module(app: FastApp):
    """初始化用户控制器"""
    # 在函数内部导入 resources，触发 @register_resource 装饰器执行
    # 这会在类定义时自动将 Resource 注册到 ResourceRegistry
    from . import resources  # noqa: F401
    
    # 创建用户控制器模块
    user_module = FastModule(name="users")
    
    # 创建路由（前缀会自动添加到所有资源路径）
    user_module.create_router(prefix="/api/v1")
    
    # 自动注册所有标记为 "users" 模块的资源
    # 此时 resources 已经被导入，Resource 已经注册到 ResourceRegistry
    user_module.auto_register_resources()
    
    # 配置 CORS（如果需要）
    # user_module.setup_cors(
    #     allow_origins=["http://localhost:3000"],
    #     allow_credentials=True
    # )
    
    # 挂载控制器到主应用
    app.mount("/", user_module)
    
    print("✅ 用户控制器初始化成功")
'''
