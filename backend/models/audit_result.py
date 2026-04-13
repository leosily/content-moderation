from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

# 审核结果状态枚举
class AuditResultStatus(str, enum.Enum):
    PASS = "通过"
    VIOLATE = "违规"

class AuditResult(Base):
    __tablename__ = "audit_results"
    
    id = Column(Integer, primary_key=True, index=True)
    # 关联任务（外键，关联tasks表的id）
    task_id = Column(Integer, ForeignKey("tasks.id"))
    # 待审核的原始文本内容
    content = Column(Text, nullable=False)
    # 审核状态（通过/违规）
    status = Column(Enum(AuditResultStatus), nullable=False)
    # 违规类型（如涉政、广告，通过则为None）
    violate_type = Column(String(30), nullable=True)
    # 违规详情（如违规词、违规原因）
    violate_detail = Column(Text, nullable=True)
    # 审核时间
    created_at = Column(DateTime, default=func.now())   
    # 关联任务（多对一：多个审核结果对应一个任务）
    task = relationship("Task", back_populates="audit_results")
