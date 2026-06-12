"""
任务相关 Schema
"""

from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    version: str = "compact"  # compact, full


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    status: str
    version: str
    progress: float
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    file_count: int = 0
    has_report: bool = False
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    total: int
    items: list[TaskResponse]
