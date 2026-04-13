from sqlalchemy.orm import Session
from typing import List, Optional
from models.task import Task, TaskStatus
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
    redis_client.hset(
        f"task_progress_{db_task.id}",
        mapping={"completed": 0, "total": 1, "status": TaskStatus.PROCESSING.value}
    )
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
    redis_client.hset(
        f"task_progress_{db_task.id}",
        mapping={"completed": 0, "total": total, "status": TaskStatus.PROCESSING.value}
    )
    return db_task

def get_task_by_id(db: Session, task_id: int, user_id: int, is_admin: bool = False) -> Optional[Task]:
    """根据ID查询任务（普通用户只能查自己的，管理员可查所有）"""
    query = db.query(Task).filter(Task.id == task_id)
    if not is_admin:
        query = query.filter(Task.user_id == user_id)
    return query.first()

def get_user_tasks(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> List[Task]:
    """查询用户的所有任务（分页）"""
    return db.query(Task).filter(Task.user_id == user_id).offset(skip).limit(limit).all()

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
    # 更新进度
    db_task.completed_count = completed
    db_task.total_count = total
    # 更新状态（如果传入）
    if status:
        db_task.status = status
    # 同步更新Redis进度
    redis_client.hset(
        f"task_progress_{db_task.id}",
        mapping={"completed": completed, "total": total, "status": status.value if status else db_task.status.value}
    )
    db.commit()
    db.refresh(db_task)
    return db_task
