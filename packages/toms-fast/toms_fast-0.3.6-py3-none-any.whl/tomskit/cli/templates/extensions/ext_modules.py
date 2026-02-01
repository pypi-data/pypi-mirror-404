"""
Redis Extension Template for tomskit CLI

This template file contains the template for generating ext_redis.py file.
"""

TEMPLATE = '''"""
模块扩展初始化
用于将 FastModule 挂载到 FastApp 上
"""

from tomskit.server import FastApp


def is_enabled() -> bool:
    """检查扩展是否启用"""
    return True


def init_app(app: FastApp):
    """
    初始化并挂载所有 FastModule 到 FastApp
    
    此扩展负责：
    - 导入所有控制器的模块初始化函数
    - 调用初始化函数将 FastModule 挂载到主应用
    
    Args:
        app: FastAPI 应用实例
    """
    # 导入所有模块的初始化函数
    from app.controllers.users.module import init_user_module
    # 在这里导入更多模块的初始化函数
    # from app.controllers.products.module import init_product_module
    # from app.controllers.orders.module import init_order_module
    
    # 初始化并挂载所有模块
    init_user_module(app)
    # 在这里调用更多模块的初始化函数
    # init_product_module(app)
    # init_order_module(app)
'''
