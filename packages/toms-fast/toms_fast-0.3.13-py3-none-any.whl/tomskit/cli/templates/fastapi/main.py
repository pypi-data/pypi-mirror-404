"""
Main template
Template for generating main.py file.
"""

TEMPLATE = '''"""
{project_name} 应用入口

创建 FastAPI 应用实例，供 ASGI 服务器（如 uvicorn、gunicorn）使用。
"""

from app_factory import create_app

# 创建应用实例
app = create_app()

# 开发测试时使用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
