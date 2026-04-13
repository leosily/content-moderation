import pydantic
from pydantic import BaseModel, Field
from typing import List, Optional
from models.task import TaskStatus

_PYDANTIC_V2 = int(pydantic.VERSION.split(".", 1)[0]) >= 2
if _PYDANTIC_V2:
    from pydantic import ConfigDict

# 任务创建请求模型（单条文本）
class TaskCreateSingle(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    content: str  # 单条文本内容

# 任务创建请求模型（批量文本，CSV导入后解析为列表）
class TaskCreateBatch(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    contents: List[str]  # 批量文本列表

# 任务响应模型
class TaskResponse(BaseModel):
    id: int
    title: str
    content_type: str
    status: TaskStatus
    created_at: str  # 时间格式化输出
    total_count: int
    completed_count: int
    user_id: int
    
    if _PYDANTIC_V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

# 任务进度响应模型
class TaskProgressResponse(BaseModel):
    task_id: int
    status: TaskStatus
    completed: int
    total: int
    progress: float  # 进度百分比（0-100）
