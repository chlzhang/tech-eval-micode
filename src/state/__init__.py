"""
状态管理模块
"""

from .manager import (
    StateManager,
    PipelineState,
    PipelineStatus,
    StageState,
    StageStatus
)

__all__ = [
    "StateManager",
    "PipelineState",
    "PipelineStatus",
    "StageState",
    "StageStatus"
]
