from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from config import settings
from database import SessionLocal
from crud.user import get_user_by_email

def _password_bytes(password: str) -> bytes:
    """Bcrypt 仅使用密码 UTF-8 编码的前 72 字节。"""
    pw = password.encode("utf-8")
    return pw[:72] if len(pw) > 72 else pw


# OAuth2令牌获取方式（从请求头的Authorization获取）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/user/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希密码是否匹配"""
    return bcrypt.checkpw(
        _password_bytes(plain_password),
        hashed_password.encode("utf-8"),
    )

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hashpw(
        _password_bytes(password),
        bcrypt.gensalt(),
    ).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(
    db: Session = Depends(lambda: SessionLocal()),
    token: str = Depends(oauth2_scheme)
):
    """获取当前登录用户（依赖注入，用于接口权限校验）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码JWT令牌
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # 从数据库查询用户
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user
