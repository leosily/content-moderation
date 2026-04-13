from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
import csv
from io import StringIO
from typing import List
from database import SessionLocal, redis_client
from schemas.task import TaskCreateSingle, TaskCreateBatch, TaskResponse, TaskProgressResponse
from crud.task import create_task_single, create_task_batch, get_task_by_id, get_user_tasks
from core.auth import get_current_user
from models.user import User
from celery_apps.task import audit_text_task
from core.limiter import limiter

router = APIRouter()

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
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="请上传CSV格式文件")
    
    # 解析CSV文件，提取文本内容
    contents = []
    try:
        # 读取CSV文件（编码设为utf-8，避免中文乱码）
        content = file.file.read().decode("utf-8")
        reader = csv.reader(StringIO(content))
        # 跳过表头（如果CSV有表头），直接读取内容行
        for row in reader:
            if row:  # 跳过空行
                contents.append(row[0].strip())  # 每行第一个字段作为文本内容
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

@router.get("/", response_model=List[TaskResponse], tags=["任务管理"])
def get_user_task_list(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询当前用户的任务列表（分页）"""
    return get_user_tasks(db=db, user_id=current_user.id, skip=skip, limit=limit)

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
    total = int(progress_data["total"])
    completed = int(progress_data["completed"])
    progress = (completed / total) * 100 if total > 0 else 0
    
    return {
        "task_id": task_id,
        "status": task.status,
        "completed": completed,
        "total": total,
        "progress": round(progress, 2)
    }
