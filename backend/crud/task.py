from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Optional
from models.task import Task, TaskStatus
from models.audit_result import AuditResult
from schemas.task import TaskCreateSingle, TaskCreateBatch
from database import redis_client

def create_task_single(db: Session, task_in: TaskCreateSingle, user_id: int) -> Task:
    """创建单条文本审核任务"""
    db_task = Task(
        title=task_in.title,
        content_type="text",
        user_id=user_id,
        total_count=1,  # 单条任务，总数量为1
        status=TaskStatus.PROCESSING  # 直接进入审核中
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    # 初始化Redis任务进度
    progress_key = f"task_progress_{db_task.id}"
    pipe = redis_client.pipeline()
    # 兼容旧版 Redis：HSET 一次只支持一个 field/value
    pipe.hset(progress_key, "completed", 0)
    pipe.hset(progress_key, "total", 1)
    pipe.hset(progress_key, "status", TaskStatus.PROCESSING.value)
    pipe.execute()
    return db_task

def create_task_batch(db: Session, task_in: TaskCreateBatch, user_id: int) -> Task:
    """创建批量文本审核任务"""
    total = len(task_in.contents)
    db_task = Task(
        title=task_in.title,
        content_type="text",
        user_id=user_id,
        total_count=total,
        status=TaskStatus.PROCESSING
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    # 初始化Redis任务进度
    progress_key = f"task_progress_{db_task.id}"
    pipe = redis_client.pipeline()
    # 兼容旧版 Redis：HSET 一次只支持一个 field/value
    pipe.hset(progress_key, "completed", 0)
    pipe.hset(progress_key, "total", total)
    pipe.hset(progress_key, "status", TaskStatus.PROCESSING.value)
    pipe.execute()
    return db_task

def get_task_by_id(db: Session, task_id: int, user_id: int, is_admin: bool = False) -> Optional[Task]:
    """根据ID查询任务（普通用户只能查自己的，管理员可查所有）"""
    query = db.query(Task).filter(Task.id == task_id)
    if not is_admin:
        query = query.filter(Task.user_id == user_id)
    return query.first()

def get_task_by_id_internal(db: Session, task_id: int) -> Optional[Task]:
    """根据ID查询任务（内部使用，不校验用户权限）。"""
    return db.query(Task).filter(Task.id == task_id).first()

def cancel_task(db: Session, task_id: int) -> Optional[Task]:
    """撤销任务（仅将状态置为已撤销，不删除数据）。"""
    db_task = get_task_by_id_internal(db=db, task_id=task_id)
    if not db_task:
        return None

    db_task.status = TaskStatus.CANCELLED
    progress_key = f"task_progress_{db_task.id}"
    pipe = redis_client.pipeline()
    pipe.hset(progress_key, "completed", db_task.completed_count)
    pipe.hset(progress_key, "total", db_task.total_count)
    pipe.hset(progress_key, "status", TaskStatus.CANCELLED.value)
    pipe.execute()
    db.commit()
    db.refresh(db_task)
    return db_task

def is_task_cancelled(db: Session, task_id: int) -> bool:
    """判断任务是否已被撤销。"""
    db_task = get_task_by_id_internal(db=db, task_id=task_id)
    return bool(db_task and db_task.status == TaskStatus.CANCELLED)

def delete_task_record(db: Session, task_id: int) -> bool:
    """删除任务记录及其关联审核结果、缓存进度。"""
    db_task = get_task_by_id_internal(db=db, task_id=task_id)
    if not db_task:
        return False

    # 避免删除审核中任务导致异步任务写入孤儿记录
    if db_task.status == TaskStatus.PROCESSING:
        raise ValueError("任务审核中，暂不支持删除")

    db.query(AuditResult).filter(AuditResult.task_id == task_id).delete(synchronize_session=False)
    db.delete(db_task)
    redis_client.delete(f"task_progress_{task_id}")
    db.commit()
    return True

def get_user_tasks(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    status: Optional[TaskStatus] = None,
    keyword: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[Task]:
    """查询用户任务列表（支持分页与可选筛选）"""
    query = db.query(Task).filter(Task.user_id == user_id)

    if status is not None:
        query = query.filter(Task.status == status)
    if keyword:
        query = query.filter(Task.title.ilike(f"%{keyword.strip()}%"))
    if start_time is not None:
        query = query.filter(Task.created_at >= start_time)
    if end_time is not None:
        query = query.filter(Task.created_at <= end_time)

    return query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()


def count_user_tasks(
    db: Session,
    user_id: int,
    status: Optional[TaskStatus] = None,
    keyword: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> int:
    """统计用户任务总数（支持与列表一致的筛选条件）。"""
    query = db.query(Task).filter(Task.user_id == user_id)

    if status is not None:
        query = query.filter(Task.status == status)
    if keyword:
        query = query.filter(Task.title.ilike(f"%{keyword.strip()}%"))
    if start_time is not None:
        query = query.filter(Task.created_at >= start_time)
    if end_time is not None:
        query = query.filter(Task.created_at <= end_time)

    return query.count()

def update_task_progress(
    db: Session,
    task_id: int,
    completed: int,
    total: int,
    status: Optional[TaskStatus] = None
) -> Optional[Task]:
    """更新任务进度和状态"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        return None
    # 已撤销任务不再接受异步进度更新，避免被 Celery 覆盖状态
    if db_task.status == TaskStatus.CANCELLED and status != TaskStatus.CANCELLED:
        return db_task
    # 更新进度
    db_task.completed_count = completed
    db_task.total_count = total
    # 更新状态（如果传入）
    if status:
        db_task.status = status
    # 同步更新Redis进度
    progress_key = f"task_progress_{db_task.id}"
    pipe = redis_client.pipeline()
    # 兼容旧版 Redis：HSET 一次只支持一个 field/value
    pipe.hset(progress_key, "completed", completed)
    pipe.hset(progress_key, "total", total)
    pipe.hset(progress_key, "status", status.value if status else db_task.status.value)
    pipe.execute()
    db.commit()
    db.refresh(db_task)
    return db_task
