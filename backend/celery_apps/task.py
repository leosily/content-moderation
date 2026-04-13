from .celery_app import celery_app
from crud.audit_result import create_audit_result
from crud.task import update_task_progress
from core.ai_client import text_audit
from database import SessionLocal
from models.task import TaskStatus

@celery_app.task(bind=True, max_retries=3)
def audit_text_task(self, task_id: int, contents: list):
    """
    异步文本审核任务
    :param task_id: 任务ID
    :param contents: 待审核的文本列表（单条任务则长度为1）
    """
    db = SessionLocal()
    try:
        # 初始化任务进度（防止Celery重启后进度丢失）
        update_task_progress(db, task_id, 0, len(contents), status=TaskStatus.PROCESSING)
        total = len(contents)
        completed = 0
        
        # 逐一条审核文本
        for content in contents:
            # 调用AI审核接口
            audit_res = text_audit(content)
            if audit_res["status"] == "failed":
                # AI接口调用失败，触发重试
                self.retry(exc=Exception(audit_res["msg"]), countdown=5)
            
            # 存储审核结果
            create_audit_result(
                db=db,
                task_id=task_id,
                content=content,
                status=audit_res["status"],
                violate_type=audit_res.get("violate_type"),
                violate_detail=audit_res.get("violate_detail")
            )
            
            # 更新进度（每完成1条更新一次）
            completed += 1
            update_task_progress(db, task_id, completed, total)
        
        # 所有文本审核完成，更新任务状态为已完成
        update_task_progress(db, task_id, total, total, status=TaskStatus.COMPLETED)
        return {"task_id": task_id, "status": "completed", "total": total, "completed": completed}
    
    except Exception as e:
        # 任务执行失败，更新任务状态为审核失败
        update_task_progress(db, task_id, completed, total, status=TaskStatus.FAILED)
        raise e  # 抛出异常，Celery记录失败日志
    finally:
        db.close()  # 关闭数据库连接
