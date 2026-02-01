"""
Test users template
Template for generating tests/test_users.py file.
"""

TEMPLATE = '''"""
用户模块测试
"""

import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_get_users():
    """测试获取用户列表"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/users")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
'''
