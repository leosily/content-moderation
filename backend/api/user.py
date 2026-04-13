from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from database import SessionLocal
from schemas.user import UserCreate, UserResponse, UserUpdate
from crud.user import create_user, get_user_by_email, update_user
from core.auth import get_current_user, create_access_token, verify_password
from config import settings
from core.limiter import limiter

router = APIRouter()

# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserResponse, tags=["用户管理"])
@limiter.limit(settings.RATE_LIMIT)
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查邮箱是否已存在
    db_user = get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    # 创建新用户
    return create_user(db=db, user_in=user_in)

@router.post("/login", tags=["用户管理"])
@limiter.limit(settings.RATE_LIMIT)
def login(
    request: Request, 
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录，返回JWT令牌"""
    # 检查用户是否存在
    user = get_user_by_email(db, email=form_data.username)  # 用邮箱作为登录账号
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 生成JWT令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

@router.get("/me", response_model=UserResponse, tags=["用户管理"])
def get_current_user_info(current_user = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user

@router.put("/me", response_model=UserResponse, tags=["用户管理"])
@limiter.limit(settings.RATE_LIMIT)
def update_user_info(
    request: Request, 
    user_in: UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改当前登录用户信息"""
    updated_user = update_user(db=db, user_id=current_user.id, user_in=user_in)
    if not updated_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return updated_user
