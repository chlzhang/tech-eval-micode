"""
Schema 定义
"""

from .auth import LoginRequest, TokenResponse, UserInfo
from .task import TaskCreate, TaskResponse, TaskListResponse
from .report import ReportResponse, ReportDetailResponse

__all__ = [
    "LoginRequest", "TokenResponse", "UserInfo",
    "TaskCreate", "TaskResponse", "TaskListResponse",
    "ReportResponse", "ReportDetailResponse"
]
