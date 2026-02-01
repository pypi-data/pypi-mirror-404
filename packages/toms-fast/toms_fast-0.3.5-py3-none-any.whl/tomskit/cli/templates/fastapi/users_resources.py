"""
Users resources template
Template for generating app/controllers/users/resources.py file.
"""

TEMPLATE = '''"""
用户资源 API
"""

from fastapi import Request, HTTPException

from tomskit.server import Resource, api_doc, register_resource
from .schemas import UserResponse, UserCreate, UserUpdate


@register_resource(module="users", path="/users", tags=["用户管理"])
class UserResource(Resource):
    """用户资源"""
    
    @api_doc(
        path="/users/list",
        summary="获取用户列表",
        description="获取所有用户列表，支持分页",
        response_model=list[UserResponse],
        responses={
            200: "成功",
            500: "服务器错误"
        }
    )
    async def get(self, request: Request):
        """获取用户列表"""
        # TODO: 从数据库获取用户列表
        return [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ]
    
    @api_doc(
        path="/users/create",
        summary="创建用户",
        description="创建新用户",
        response_model=UserResponse,
        status_code=201,
        responses={
            201: "用户创建成功",
            400: "请求参数错误",
            409: "用户已存在"
        }
    )
    async def post(self, request: Request):
        """创建用户"""
        data = await request.json()
        # TODO: 验证数据并创建用户
        return {
            "id": 3,
            "name": data.get("name", ""),
            "email": data.get("email", "")
        }
    
    @api_doc(
        summary="获取用户详情",
        description="根据用户 ID 获取用户详情",
        response_model=UserResponse,
        path="/users/{user_id}",
        responses={
            200: "成功",
            404: "用户不存在"
        }
    )
    async def get(self, request: Request):
        """获取用户详情"""
        user_id = request.path_params.get("user_id")
        if not user_id:
            raise HTTPException(status_code=404, detail="用户不存在")
        # TODO: 从数据库获取用户
        return {"id": int(user_id), "name": "Alice", "email": "alice@example.com"}
    
    @api_doc(
        summary="更新用户",
        description="更新用户信息",
        response_model=UserResponse,
        path="/users/{user_id}",
        responses={
            200: "更新成功",
            404: "用户不存在",
            400: "请求参数错误"
        }
    )
    async def put(self, request: Request):
        """更新用户"""
        user_id = request.path_params.get("user_id")
        data = await request.json()
        # TODO: 更新用户信息
        return {"id": int(user_id), "name": data.get("name", ""), "email": data.get("email", "")}
    
    @api_doc(
        summary="删除用户",
        description="删除指定用户",
        path="/users/{user_id}",
        responses={
            204: "删除成功",
            404: "用户不存在"
        }
    )
    async def delete(self, request: Request):
        """删除用户"""
        user_id = request.path_params.get("user_id")
        # TODO: 删除用户
        return None
'''
