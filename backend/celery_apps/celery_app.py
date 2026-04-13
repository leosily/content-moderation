from celery import Celery
from config import settings

# 初始化Celery，Redis作为消息代理和结果存储
celery_app = Celery(
    "ai_audit_tasks",
    broker=f"redis://{settings.REDIS_CONFIG['host']}:{settings.REDIS_CONFIG['port']}/{settings.REDIS_CONFIG['db']}",
    backend=f"redis://{settings.REDIS_CONFIG['host']}:{settings.REDIS_CONFIG['port']}/{settings.REDIS_CONFIG['db']}",
    include=[f"{__package__}.task"],  # 导入任务模块
)

# 基础配置
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    retry_attempts=3,  # 任务失败默认重试3次
    retry_backoff=5,    # 重试间隔5秒
)
