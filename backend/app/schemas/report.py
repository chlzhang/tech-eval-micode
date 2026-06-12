"""
报告相关 Schema
"""

from datetime import datetime
from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: int
    task_id: int
    title: str | None = None
    tech_topic: str | None = None
    version: str | None = None
    quality_score: float | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportDetailResponse(ReportResponse):
    html_content: str | None = None
    chart_data: dict | None = None
