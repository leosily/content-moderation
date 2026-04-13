from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import SessionLocal
from schemas.audit_result import AuditResultResponse, BatchAuditResponse
from crud.audit_result import get_audit_results_by_task_id, get_audit_count_by_task_id
from crud.task import get_task_by_id
from core.auth import get_current_user
from models.user import User
from models.audit_result import AuditResultStatus


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/task/{task_id}", response_model=BatchAuditResponse, tags=["审核结果"])
def get_audit_results_by_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询某个任务的所有审核结果"""
    # 校验任务是否存在且有权限
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id, is_admin=current_user.is_admin)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权限查看")
    
    # 获取所有审核结果
    results = get_audit_results_by_task_id(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin
    )
    
    # 统计通过和违规数量
    pass_count = get_audit_count_by_task_id(db=db, task_id=task_id, status=AuditResultStatus.PASS)
    violate_count = get_audit_count_by_task_id(db=db, task_id=task_id, status=AuditResultStatus.VIOLATE)
    
    return {
        "task_id": task_id,
        "total": len(results),
        "completed": len(results),
        "pass_count": pass_count,
        "violate_count": violate_count,
        "results": results
    }
