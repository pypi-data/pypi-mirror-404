"""
User model template
Template for generating app/models/user.py file.
"""

TEMPLATE = '''"""
用户相关数据模型
包含用户、部门、用户部门关联等模型定义。
"""

import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Index
from tomskit.sqlalchemy import SQLAlchemy, db
from tomskit.sqlalchemy import StringUUID, uuid_generate_v4


class User(SQLAlchemy.Model): 
    """
    用户模型
    
    存储用户基本信息，包括登录凭证、个人资料等。
    """
    __tablename__ = "fa_users"
    __table_args__ = (
        # 移除重复的主键约束，primary_key=True 已足够
        # 添加唯一约束
        db.UniqueConstraint('username', name='fa_users_username_unique'),
        db.UniqueConstraint('email', name='fa_users_email_unique'),
        # 添加索引提升查询性能
        Index('idx_user_email', 'email'),
        Index('idx_user_phone', 'phone'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_is_active', 'is_active'),
    )

    id: Mapped[str] = mapped_column(StringUUID, primary_key=True, default=uuid_generate_v4)
    """用户ID（主键）"""
    
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    """用户名（唯一）"""
    
    nickname: Mapped[str] = mapped_column(String(255), nullable=False) 
    """花名"""
    
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    """邮箱（唯一，可为空）"""
    
    phone: Mapped[str | None] = mapped_column(String(36), nullable=True)
    """手机号"""
    
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=db.text("true"))
    """是否激活"""
    
    is_frozen: Mapped[bool] = mapped_column(Boolean, server_default=db.text("false"))
    """是否冻结（临时锁定账号）"""
    
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """密码哈希"""
    
    password_salt: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """密码盐"""
    
    is_password_set: Mapped[bool] = mapped_column(Boolean, server_default=db.text("false"))
    """是否设置密码"""
    
    locale: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """语言"""
    
    timezone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """时区"""
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=db.text('CURRENT_TIMESTAMP(0)'),
        nullable=False
    )
    """创建时间"""
    
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=db.text('CURRENT_TIMESTAMP(0)'),
        onupdate=db.text('CURRENT_TIMESTAMP(0)'),
        nullable=False  # 统一为不可空
    )
    """更新时间"""

    # 定义单向 relationship（不建立双向关联，不使用 back_populates）
    # 由于 UserDepartment.user_id 已定义 ForeignKey，可以省略 foreign_keys 参数
    user_departments: Mapped[list["UserDepartment"]] = relationship(
        "UserDepartment",
        lazy="select"  # 延迟加载：只有在访问 user.user_departments 时才查询
    )

    async def get_department_ids(self) -> list[str]:
        """
        异步方法：获取用户所属的部门ID列表（延迟加载）
        
        只有在调用此方法时才会查询 UserDepartment 表。
        使用 await 访问 relationship 触发延迟加载。
        """
        # 使用 await 访问 relationship，触发延迟加载查询
        user_departments = await self.awaitable_attrs.user_departments
        return [ud.department_id for ud in user_departments]
    
    @property
    def department_ids(self) -> list[str]:
        """
        同步属性：获取用户所属的部门ID列表
        
        注意：由于使用 lazy="select" 延迟加载，如果 user_departments 尚未加载，
        此属性可能返回空列表。
        
        推荐使用异步方法 get_department_ids() 来确保数据已加载。
        """
        # 尝试访问已加载的数据（如果已加载）
        try:
            # 如果 relationship 已加载，直接访问；否则会触发延迟加载但无法 await
            # 在同步属性中，如果未加载会返回空列表
            return [ud.department_id for ud in self.user_departments]
        except (AttributeError, KeyError, RuntimeError):
            # 如果未加载或无法访问，返回空列表
            return []


class Department(SQLAlchemy.Model):
    """
    部门模型
    
    存储部门信息，支持树形结构（通过 parent_id 实现）。
    """
    __tablename__ = "fa_departments"
    __table_args__ = (
        # 移除重复的主键约束
        # 添加索引
        Index('idx_department_parent_id', 'parent_id'),
        Index('idx_department_path', 'path'),
        Index('idx_department_is_active', 'is_active'),
    )

    id: Mapped[str] = mapped_column(StringUUID, primary_key=True, default=uuid_generate_v4)
    """部门ID（主键）"""
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    """部门名称"""
    
    short_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """简称"""
    
    external_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    """外部ID"""
    
    parent_id: Mapped[str | None] = mapped_column(
        StringUUID,
        ForeignKey("fa_departments.id", ondelete="SET NULL"),
        nullable=True
    )
    """父部门ID（自引用外键）"""
    
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    """部门路径"""
    
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    """部门级别"""
    
    dept_type: Mapped[str] = mapped_column(String(255), nullable=False) 
    """部门类型"""
    
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=db.text("true"))
    """是否激活"""
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=db.text('CURRENT_TIMESTAMP(0)'),
        nullable=False
    )
    """创建时间"""
    
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=db.text('CURRENT_TIMESTAMP(0)'),
        onupdate=db.text('CURRENT_TIMESTAMP(0)'),
        nullable=False  # 统一为不可空
    )
    """更新时间"""


class UserDepartment(SQLAlchemy.Model):
    """
    用户部门关联模型
    
    多对多关系表，记录用户与部门的关联关系。
    """
    __tablename__ = "fa_user_departments"
    __table_args__ = (
        db.UniqueConstraint('user_id', 'department_id', name='uq_user_department'),
        # 添加索引（外键通常会自动创建索引，但明确指定更清晰）
        Index('idx_user_department_user_id', 'user_id'),
        Index('idx_user_department_department_id', 'department_id'),
    )
    
    user_id: Mapped[str] = mapped_column(
        StringUUID,
        ForeignKey("fa_users.id", ondelete="CASCADE"),
        nullable=False
    )
    """用户ID（外键）"""

    department_id: Mapped[str] = mapped_column(
        StringUUID,
        ForeignKey("fa_departments.id", ondelete="CASCADE"),
        nullable=False
    )
    """部门ID（外键）"""

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=db.text("false"))
    """是否主部门"""
    
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """职位，例如"主管"、"开发工程师" """  # 职位，例如"主管"、"开发工程师"

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=db.text('CURRENT_TIMESTAMP(0)'),
        nullable=False
    )
    """创建时间"""
    
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=db.text('CURRENT_TIMESTAMP(0)'),
        onupdate=db.text('CURRENT_TIMESTAMP(0)'),
        nullable=False  # 统一为不可空
    )
    """更新时间"""
'''
