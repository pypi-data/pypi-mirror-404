"""
Users schemas template
Template for generating app/controllers/users/schemas.py file.
"""

TEMPLATE = '''"""
用户数据模型
"""

from pydantic import BaseModel


class UserBase(BaseModel):
    """用户基础模型"""
    name: str
    email: str  # 如需邮箱验证，可安装 email-validator 并使用 EmailStr


class UserCreate(UserBase):
    """创建用户请求模型"""
    pass


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    name: str | None = None
    email: str | None = None  # 如需邮箱验证，可安装 email-validator 并使用 EmailStr


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    
    class Config:
        from_attributes = True
'''
