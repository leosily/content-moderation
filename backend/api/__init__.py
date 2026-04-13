from fastapi import APIRouter
from . import user, task, audit

# 初始化总路由
api_router = APIRouter(prefix="/api")

# 注册各模块路由
api_router.include_router(user.router, prefix="/user", tags=["用户管理"])
api_router.include_router(task.router, prefix="/task", tags=["任务管理"])
api_router.include_router(audit.router, prefix="/audit", tags=["审核结果"])

__all__ = ["api_router"]