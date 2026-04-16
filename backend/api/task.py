from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import case, func
import csv
from io import StringIO
from typing import Optional
from database import SessionLocal, redis_client
from schemas.task import TaskCreateSingle, TaskCreateBatch, TaskResponse, TaskProgressResponse, TaskListResponse
from crud.task import create_task_single, create_task_batch, get_task_by_id, get_user_tasks, count_user_tasks, cancel_task, delete_task_record
from core.auth import get_current_user
from models.user import User
from models.task import Task, TaskStatus
from models.audit_result import AuditResult, AuditResultStatus
from celery_apps.task import audit_text_task
from core.limiter import limiter

router = APIRouter()

MAX_PAGE_LIMIT = 100


def _to_int(value, default=0):
    """将 Redis/DB 返回值安全转换为 int。"""
    if value is None:
        return default
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="ignore")
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/single", response_model=TaskResponse, tags=["任务管理"])
@limiter.limit("5/minute")  # 限制每分钟最多创建5个单条任务
def create_single_task(
    request: Request, 
    task_in: TaskCreateSingle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建单条文本审核任务"""
    # 创建任务
    task = create_task_single(db=db, task_in=task_in, user_id=current_user.id)
    # 推送异步审核任务
    audit_text_task.delay(task_id=task.id, contents=[task_in.content])
    return task

@router.post("/batch", response_model=TaskResponse, tags=["任务管理"])
@limiter.limit("3/minute")  # 限制每分钟最多创建3个批量任务
def create_batch_task(
    request: Request, 
    title: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建批量文本审核任务（CSV文件导入）"""
    # 校验文件格式
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="请上传CSV格式文件")
    
    # 解析CSV文件，提取文本内容
    contents = []
    try:
        # 读取CSV文件（兼容 utf-8-sig，避免 BOM 导致首列异常）
        content = file.file.read().decode("utf-8-sig")
        reader = csv.reader(StringIO(content))
        for row_index, row in enumerate(reader):
            if not row:
                continue

            first_col = row[0].strip()
            if not first_col:
                continue

            # 兼容常见表头写法：content/text/文本
            if row_index == 0 and first_col.lower() in {"content", "text", "文本"}:
                continue

            contents.append(first_col)  # 每行第一个字段作为文本内容
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV文件解析失败：{str(e)}")
    
    if not contents:
        raise HTTPException(status_code=400, detail="CSV文件中无有效文本内容")
    
    # 创建批量任务
    task_in = TaskCreateBatch(title=title, contents=contents)
    task = create_task_batch(db=db, task_in=task_in, user_id=current_user.id)
    # 推送异步审核任务
    audit_text_task.delay(task_id=task.id, contents=contents)
    return task

@router.get("/", response_model=TaskListResponse, tags=["任务管理"])
def get_user_task_list(
    skip: int = 0,
    limit: int = 10,
    status: Optional[TaskStatus] = None,
    keyword: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询当前用户的任务列表（分页）"""
    if skip < 0:
        raise HTTPException(status_code=400, detail="skip 不能小于 0")
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit 必须大于 0")
    if start_time and end_time and start_time > end_time:
        raise HTTPException(status_code=400, detail="start_time 不能晚于 end_time")
    limit = min(limit, MAX_PAGE_LIMIT)
    items = get_user_tasks(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time
    )
    total = count_user_tasks(
        db=db,
        user_id=current_user.id,
        status=status,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time
    )
    return {
        "items": items,
        "total": int(total),
        "skip": int(skip),
        "limit": int(limit)
    }

@router.get("/dashboard/stats", tags=["任务管理"])
def get_dashboard_stats(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取首页看板统计数据（按当前用户）"""
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="days 取值范围为 1-90")

    # 统计口径统一排除已撤销任务（兼容不同历史存储值）
    task_base_query = db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.status != TaskStatus.CANCELLED,
        Task.status != "已撤销",
        Task.status != "CANCELLED"
    )
    total_tasks = task_base_query.count()

    status_counts = db.query(
        func.sum(case((AuditResult.status == AuditResultStatus.PASS, 1), else_=0)).label("approved_count"),
        func.sum(case((AuditResult.status == AuditResultStatus.VIOLATE, 1), else_=0)).label("rejected_count"),
    ).join(
        Task, Task.id == AuditResult.task_id
    ).filter(
        Task.user_id == current_user.id
    ).one()
    approved_count = int(status_counts.approved_count or 0)
    rejected_count = int(status_counts.rejected_count or 0)

    pending_tasks = task_base_query.filter(Task.status.in_([TaskStatus.PENDING, TaskStatus.PROCESSING])).count()

    # 最近 N 天任务趋势
    end_day = datetime.now().date()
    start_day = end_day - timedelta(days=days - 1)
    trend_rows = db.query(
        func.date(Task.created_at).label("day"),
        func.count(Task.id).label("task_count")
    ).filter(
        Task.user_id == current_user.id,
        Task.created_at >= start_day,
        Task.status != TaskStatus.CANCELLED,
        Task.status != "已撤销",
        Task.status != "CANCELLED"
    ).group_by(
        func.date(Task.created_at)
    ).all()

    pass_rows = db.query(
        func.date(AuditResult.created_at).label("day"),
        func.count(AuditResult.id).label("pass_count")
    ).join(
        Task, Task.id == AuditResult.task_id
    ).filter(
        Task.user_id == current_user.id,
        Task.status != TaskStatus.CANCELLED,
        Task.status != "已撤销",
        Task.status != "CANCELLED",
        AuditResult.status == AuditResultStatus.PASS,
        AuditResult.created_at >= start_day
    ).group_by(
        func.date(AuditResult.created_at)
    ).all()

    day_to_count = {str(row.day): int(row.task_count) for row in trend_rows}
    day_to_pass = {str(row.day): int(row.pass_count) for row in pass_rows}
    trend_labels = []
    task_trend = []
    pass_trend = []

    for i in range(days):
        current_day = start_day + timedelta(days=i)
        day_key = str(current_day)
        trend_labels.append(current_day.strftime("%m-%d"))
        task_trend.append(day_to_count.get(day_key, 0))

        pass_trend.append(day_to_pass.get(day_key, 0))

    # 按违规类型统计分布（Top 5）
    risk_rows = db.query(
        AuditResult.violate_type,
        func.count(AuditResult.id).label("count")
    ).join(
        Task, Task.id == AuditResult.task_id
    ).filter(
        Task.user_id == current_user.id,
        AuditResult.status == AuditResultStatus.VIOLATE
    ).group_by(
        AuditResult.violate_type
    ).order_by(
        func.count(AuditResult.id).desc()
    ).limit(5).all()

    risk_labels = []
    approval_rate = []
    total_violates = sum(int(row.count) for row in risk_rows) or 0
    for row in risk_rows:
        label = row.violate_type or "未分类"
        risk_labels.append(label)
        # 为保持前端兼容沿用 approval_rate 字段，实际返回该类型违规占比
        rate = round((int(row.count) / total_violates) * 100, 2) if total_violates > 0 else 0
        approval_rate.append(rate)

    if not risk_labels:
        risk_labels = ["暂无数据"]
        approval_rate = [0]

    risk_distribution = [
        {"name": "通过", "value": int(approved_count)},
        {"name": "违规", "value": int(rejected_count)},
        {"name": "待处理", "value": int(pending_tasks)}
    ]

    return {
        "metrics": {
            "total_tasks": int(total_tasks),
            "approved_count": int(approved_count),
            "pending_tasks": int(pending_tasks),
            "rejected_count": int(rejected_count)
        },
        "charts": {
            "task_trend": {
                "labels": trend_labels,
                "tasks": task_trend,
                "approved": pass_trend
            },
            "approval_rate": {
                "labels": risk_labels,
                "values": approval_rate
            },
            "risk_distribution": risk_distribution
        }
    }


@router.get("/health", tags=["任务管理"])
def task_service_health(db: Session = Depends(get_db)):
    """任务服务健康检查。"""
    try:
        db.query(func.count(Task.id)).scalar()
        redis_client.ping()
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"service unavailable: {exc}")

@router.get("/{task_id}/progress", response_model=TaskProgressResponse, tags=["任务管理"])
def get_task_progress(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询任务审核进度"""
    # 先校验任务是否存在且有权限
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id, is_admin=current_user.is_admin)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权限查看")
    
    # 从Redis获取进度
    progress_key = f"task_progress_{task_id}"
    progress_data = redis_client.hgetall(progress_key)
    if not progress_data:
        # Redis中无数据，从数据库获取
        progress_data = {
            "completed": task.completed_count,
            "total": task.total_count,
            "status": task.status.value
        }
    
    # 计算进度百分比
    total = _to_int(progress_data.get("total"), default=0)
    completed = _to_int(progress_data.get("completed"), default=0)
    progress = (completed / total) * 100 if total > 0 else 0
    
    return {
        "task_id": task_id,
        "status": task.status,
        "completed": completed,
        "total": total,
        "progress": round(progress, 2)
    }


@router.get("/{task_id}", response_model=TaskResponse, tags=["任务管理"])
def get_task_detail(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询单个任务详情"""
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id, is_admin=current_user.is_admin)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权限查看")
    return task


@router.post("/{task_id}/cancel", response_model=TaskResponse, tags=["任务管理"])
def cancel_user_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """撤销任务（仅支持待审核/审核中）。"""
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id, is_admin=current_user.is_admin)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权限操作")

    if task.status == TaskStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="任务已撤销，无需重复操作")
    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        raise HTTPException(status_code=400, detail="当前状态不支持撤销")

    cancelled_task = cancel_task(db=db, task_id=task_id)
    if not cancelled_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return cancelled_task


@router.delete("/{task_id}", tags=["任务管理"])
def delete_user_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除任务记录（含关联审核结果）。"""
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id, is_admin=current_user.is_admin)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权限操作")

    try:
        deleted = delete_task_record(db=db, task_id=task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not deleted:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务删除成功", "task_id": task_id}
