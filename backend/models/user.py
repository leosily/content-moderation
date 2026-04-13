from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users" 
    
    # 主键自增ID
    id = Column(Integer, primary_key=True, index=True)
    # 手机号（可选，唯一）
    phone = Column(String(11), unique=True, index=True, nullable=True)
    # 邮箱（必填，唯一，用于登录）
    email = Column(String(50), unique=True, index=True, nullable=False)
    # 密码哈希（不存储明文密码）
    hashed_password = Column(String(100), nullable=False)
    # 用户名
    username = Column(String(20), nullable=False)
    # 管理员标识（基础版预留，默认普通用户）
    is_admin = Column(Boolean, default=False)
