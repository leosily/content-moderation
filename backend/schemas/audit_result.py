import pydantic
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models.audit_result import AuditResultStatus

_PYDANTIC_V2 = int(pydantic.VERSION.split(".", 1)[0]) >= 2
if _PYDANTIC_V2:
    from pydantic import ConfigDict

# 审核结果响应模型
class AuditResultResponse(BaseModel):
    id: int
    task_id: int
    content: str
    status: AuditResultStatus
    violate_type: Optional[str]
    violate_detail: Optional[str]
    created_at: datetime
    
    if _PYDANTIC_V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

# 批量审核结果响应模型
class BatchAuditResponse(BaseModel):
    task_id: int
    total: int
    completed: int
    pass_count: int  # 通过数量
    violate_count: int  # 违规数量
    results: List[AuditResultResponse]
