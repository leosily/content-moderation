from sqlalchemy.orm import Session
from typing import Optional
from models.user import User
from schemas.user import UserCreate, UserUpdate


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱查询用户（登录时用）"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    """创建新用户（注册时用）"""
    from core.auth import get_password_hash
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        phone=user_in.phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)  # 刷新数据，获取自增ID
    return db_user

def update_user(db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
    """修改用户信息"""
    from core.auth import get_password_hash
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    # 批量更新字段（只更新传入的非None字段）
    update_data = user_in.dict(exclude_unset=True)
    if "password" in update_data:
        # 密码需要重新加密
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user
