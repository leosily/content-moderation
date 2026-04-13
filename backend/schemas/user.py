import pydantic
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Pydantic v1 也暴露了 ConfigDict（实为 dict），不能用它判断版本
_PYDANTIC_V2 = int(pydantic.VERSION.split(".", 1)[0]) >= 2
if _PYDANTIC_V2:
    from pydantic import ConfigDict

# 用户注册请求模型
class UserCreate(BaseModel):
    email: EmailStr  # 邮箱格式校验
    username: str = Field(min_length=2, max_length=20)  # 用户名长度校验
    password: str = Field(min_length=6, max_length=20)  # 密码长度校验
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")  # 手机号格式校验

# 用户登录请求模型
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 用户信息响应模型（不返回密码哈希）
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    phone: Optional[str]
    is_admin: bool
    
    if _PYDANTIC_V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True  # 支持SQLAlchemy模型直接转换为响应

# 用户信息修改请求模型
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=2, max_length=20)
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    password: Optional[str] = Field(None, min_length=6, max_length=20)
