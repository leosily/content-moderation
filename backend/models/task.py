from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

# 任务状态枚举（基础版4种状态）
class TaskStatus(str, enum.Enum):
    PENDING = "待审核"
    PROCESSING = "审核中"
    COMPLETED = "已完成"
    FAILED = "审核失败"
    CANCELLED = "已撤销"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    # 任务名称（用户自定义）
    title = Column(String(50), nullable=False)
    # 内容类型（基础版仅支持text）
    content_type = Column(String(10), default="text")
    # 关联用户（外键，关联users表的id）
    user_id = Column(Integer, ForeignKey("users.id"))
    # 任务状态
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    # 任务创建时间（自动生成）
    created_at = Column(DateTime, default=func.now())
    # 本次任务总内容数
    total_count = Column(Integer, default=0)
    # 已审核内容数（用于计算进度）
    completed_count = Column(Integer, default=0)  
    # 关联审核结果（一对多：一个任务对应多个审核结果）
    audit_results = relationship("AuditResult", back_populates="task")
