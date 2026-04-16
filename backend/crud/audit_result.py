from sqlalchemy import case, func
from sqlalchemy.orm import Session
from typing import List
from models.audit_result import AuditResult, AuditResultStatus
from models.task import TaskStatus, Task
from .task import update_task_progress

def _normalize_audit_status(status: str) -> AuditResultStatus:
    """兼容英文/中文状态入参并转换为 AuditResultStatus。"""
    raw = str(status or "").strip()
    upper = raw.upper()
    if upper == "PASS" or raw == "通过":
        return AuditResultStatus.PASS
    if upper == "VIOLATE" or raw == "违规":
        return AuditResultStatus.VIOLATE
    raise ValueError(f"unsupported audit status: {status}")

def create_audit_result(
    db: Session,
    task_id: int,
    content: str,
    status: str,
    violate_type: str = None,
    violate_detail: str = None
) -> AuditResult:
    """创建审核结果"""
    normalized_status = _normalize_audit_status(status)
    db_audit = AuditResult(
        task_id=task_id,
        content=content,
        status=normalized_status,
        violate_type=violate_type,
        violate_detail=violate_detail
    )
    db.add(db_audit)
    db.commit()
    db.refresh(db_audit)
    return db_audit

def get_audit_results_by_task_id(
    db: Session,
    task_id: int,
    user_id: int,
    is_admin: bool = False
) -> List[AuditResult]:
    """根据任务ID查询所有审核结果（校验用户权限）"""
    query = db.query(AuditResult).filter(AuditResult.task_id == task_id)
    if not is_admin:
        # 普通用户只能查自己任务的结果（关联task表的user_id）
        query = query.join(Task).filter(Task.user_id == user_id)
    return query.all()

def get_audit_count_by_task_id(
    db: Session,
    task_id: int,
    status: AuditResultStatus
) -> int:
    """统计某个任务中，指定状态（通过/违规）的数量"""
    return db.query(AuditResult).filter(
        AuditResult.task_id == task_id,
        AuditResult.status == status
    ).count()


def get_audit_status_counts_by_task_id(db: Session, task_id: int) -> dict:
    """一次查询统计任务下通过/违规数量。"""
    row = db.query(
        func.sum(case((AuditResult.status == AuditResultStatus.PASS, 1), else_=0)).label("pass_count"),
        func.sum(case((AuditResult.status == AuditResultStatus.VIOLATE, 1), else_=0)).label("violate_count"),
    ).filter(
        AuditResult.task_id == task_id
    ).one()

    return {
        "pass_count": int(row.pass_count or 0),
        "violate_count": int(row.violate_count or 0),
    }