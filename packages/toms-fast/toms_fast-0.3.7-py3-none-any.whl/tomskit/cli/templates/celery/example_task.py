"""
Example task template
Template for generating tasks/example_task.py file.
"""

TEMPLATE = '''"""
{project_name} 示例 Celery 任务
"""

from tomskit.celery import async_shared_task

@async_shared_task(queue="default")
def example_task(message: str):
    """
    异步任务函数
    
    Args:
        message: 要处理的消息
        
    Returns:
        str: 处理结果
    """
    # TODO: 实现你的异步任务逻辑
    # 可以使用 db.session 进行数据库操作
    # 可以使用 redis_client 进行 Redis 操作
    
    print(f"处理消息: {{message}}")
    return f"任务完成: {{message}}"
'''
