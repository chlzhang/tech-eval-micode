"""
状态管理器

提供流水线状态追踪和检查点功能：
1. 全局状态机
2. 检查点保存/恢复
3. 进度追踪
4. 断点续传
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum


class PipelineStatus(Enum):
    """流水线状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StageStatus(Enum):
    """阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageState:
    """阶段状态"""
    name: str
    status: StageStatus = StageStatus.PENDING
    progress: float = 0.0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineState:
    """流水线状态"""
    pipeline_id: str
    status: PipelineStatus = PipelineStatus.PENDING
    current_stage: Optional[str] = None
    stages: Dict[str, StageState] = field(default_factory=dict)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status.value,
            "current_stage": self.current_stage,
            "stages": {
                name: {
                    "status": stage.status.value,
                    "progress": stage.progress,
                    "start_time": stage.start_time,
                    "end_time": stage.end_time,
                    "error": stage.error
                }
                for name, stage in self.stages.items()
            },
            "start_time": self.start_time,
            "end_time": self.end_time,
            "errors": self.errors,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineState':
        """从字典创建"""
        state = cls(
            pipeline_id=data["pipeline_id"],
            status=PipelineStatus(data["status"]),
            current_stage=data.get("current_stage"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            errors=data.get("errors", []),
            metadata=data.get("metadata", {})
        )
        
        for name, stage_data in data.get("stages", {}).items():
            state.stages[name] = StageState(
                name=name,
                status=StageStatus(stage_data["status"]),
                progress=stage_data.get("progress", 0),
                start_time=stage_data.get("start_time"),
                end_time=stage_data.get("end_time"),
                error=stage_data.get("error")
            )
        
        return state


class StateManager:
    """状态管理器"""
    
    def __init__(self, checkpoint_dir: str = "output/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self._state: Optional[PipelineState] = None
        self._observers: List[Callable] = []
        self._auto_save: bool = True
        self._save_interval: int = 300  # 秒
    
    @property
    def state(self) -> Optional[PipelineState]:
        """获取当前状态"""
        return self._state
    
    def create_pipeline(self, pipeline_id: str) -> PipelineState:
        """创建新流水线"""
        self._state = PipelineState(
            pipeline_id=pipeline_id,
            status=PipelineStatus.PENDING,
            start_time=datetime.now().isoformat()
        )
        self._notify_observers("pipeline_created", {"pipeline_id": pipeline_id})
        return self._state
    
    def add_stage(self, stage_name: str):
        """添加阶段"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        self._state.stages[stage_name] = StageState(name=stage_name)
        self._notify_observers("stage_added", {"stage_name": stage_name})
    
    def start_pipeline(self):
        """启动流水线"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        self._state.status = PipelineStatus.RUNNING
        self._state.start_time = datetime.now().isoformat()
        self._notify_observers("pipeline_started", {"pipeline_id": self._state.pipeline_id})
    
    def start_stage(self, stage_name: str):
        """启动阶段"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        if stage_name not in self._state.stages:
            raise ValueError(f"阶段 {stage_name} 不存在")
        
        stage = self._state.stages[stage_name]
        stage.status = StageStatus.RUNNING
        stage.start_time = datetime.now().isoformat()
        stage.progress = 0.0
        
        self._state.current_stage = stage_name
        self._notify_observers("stage_started", {"stage_name": stage_name})
    
    def update_stage_progress(self, stage_name: str, progress: float, data: Dict[str, Any] = None):
        """更新阶段进度"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        if stage_name not in self._state.stages:
            raise ValueError(f"阶段 {stage_name} 不存在")
        
        stage = self._state.stages[stage_name]
        stage.progress = min(100.0, max(0.0, progress))
        
        if data:
            stage.data.update(data)
        
        self._notify_observers("stage_progress", {
            "stage_name": stage_name,
            "progress": progress
        })
    
    def complete_stage(self, stage_name: str, data: Dict[str, Any] = None):
        """完成阶段"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        if stage_name not in self._state.stages:
            raise ValueError(f"阶段 {stage_name} 不存在")
        
        stage = self._state.stages[stage_name]
        stage.status = StageStatus.COMPLETED
        stage.progress = 100.0
        stage.end_time = datetime.now().isoformat()
        
        if data:
            stage.data.update(data)
        
        self._notify_observers("stage_completed", {"stage_name": stage_name})
        
        # 自动保存检查点
        if self._auto_save:
            self.save_checkpoint()
    
    def fail_stage(self, stage_name: str, error: str):
        """阶段失败"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        if stage_name not in self._state.stages:
            raise ValueError(f"阶段 {stage_name} 不存在")
        
        stage = self._state.stages[stage_name]
        stage.status = StageStatus.FAILED
        stage.end_time = datetime.now().isoformat()
        stage.error = error
        
        self._state.errors.append(f"{stage_name}: {error}")
        
        self._notify_observers("stage_failed", {
            "stage_name": stage_name,
            "error": error
        })
    
    def skip_stage(self, stage_name: str, reason: str = ""):
        """跳过阶段"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        if stage_name not in self._state.stages:
            raise ValueError(f"阶段 {stage_name} 不存在")
        
        stage = self._state.stages[stage_name]
        stage.status = StageStatus.SKIPPED
        stage.end_time = datetime.now().isoformat()
        stage.error = reason
        
        self._notify_observers("stage_skipped", {
            "stage_name": stage_name,
            "reason": reason
        })
    
    def complete_pipeline(self):
        """完成流水线"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        self._state.status = PipelineStatus.COMPLETED
        self._state.end_time = datetime.now().isoformat()
        self._state.current_stage = None
        
        self._notify_observers("pipeline_completed", {
            "pipeline_id": self._state.pipeline_id
        })
        
        # 保存最终检查点
        self.save_checkpoint()
    
    def fail_pipeline(self, error: str):
        """流水线失败"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        self._state.status = PipelineStatus.FAILED
        self._state.end_time = datetime.now().isoformat()
        self._state.errors.append(error)
        
        self._notify_observers("pipeline_failed", {
            "pipeline_id": self._state.pipeline_id,
            "error": error
        })
        
        # 保存检查点
        self.save_checkpoint()
    
    def pause_pipeline(self):
        """暂停流水线"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        self._state.status = PipelineStatus.PAUSED
        self._notify_observers("pipeline_paused", {
            "pipeline_id": self._state.pipeline_id
        })
        
        self.save_checkpoint()
    
    def resume_pipeline(self):
        """恢复流水线"""
        if self._state is None:
            raise RuntimeError("流水线未创建")
        
        self._state.status = PipelineStatus.RUNNING
        self._notify_observers("pipeline_resumed", {
            "pipeline_id": self._state.pipeline_id
        })
    
    def save_checkpoint(self, filename: str = None):
        """保存检查点"""
        if self._state is None:
            return
        
        if filename is None:
            filename = f"checkpoint_{self._state.pipeline_id}.json"
        
        checkpoint_path = self.checkpoint_dir / filename
        checkpoint_data = self._state.to_dict()
        checkpoint_data["saved_at"] = datetime.now().isoformat()
        
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        
        self._notify_observers("checkpoint_saved", {"path": str(checkpoint_path)})
    
    def load_checkpoint(self, filename: str) -> PipelineState:
        """加载检查点"""
        checkpoint_path = self.checkpoint_dir / filename
        
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"检查点文件不存在: {checkpoint_path}")
        
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            checkpoint_data = json.load(f)
        
        self._state = PipelineState.from_dict(checkpoint_data)
        
        self._notify_observers("checkpoint_loaded", {
            "pipeline_id": self._state.pipeline_id
        })
        
        return self._state
    
    def get_latest_checkpoint(self) -> Optional[str]:
        """获取最新的检查点文件"""
        checkpoints = list(self.checkpoint_dir.glob("checkpoint_*.json"))
        if not checkpoints:
            return None
        
        # 按修改时间排序
        checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return checkpoints[0].name
    
    def load_latest_checkpoint(self) -> Optional[PipelineState]:
        """加载最新的检查点"""
        latest = self.get_latest_checkpoint()
        if latest:
            return self.load_checkpoint(latest)
        return None
    
    def add_observer(self, callback: Callable):
        """添加观察者"""
        self._observers.append(callback)
    
    def _notify_observers(self, event: str, data: Dict[str, Any]):
        """通知观察者"""
        for observer in self._observers:
            try:
                observer(event, data)
            except Exception as e:
                print(f"Observer error: {e}")
    
    def get_progress(self) -> Dict[str, Any]:
        """获取整体进度"""
        if self._state is None:
            return {"status": "not_started"}
        
        total_stages = len(self._state.stages)
        if total_stages == 0:
            return {"status": "no_stages", "progress": 0}
        
        completed = sum(
            1 for s in self._state.stages.values()
            if s.status == StageStatus.COMPLETED
        )
        
        running_progress = sum(
            s.progress / 100
            for s in self._state.stages.values()
            if s.status == StageStatus.RUNNING
        )
        
        overall_progress = (completed + running_progress) / total_stages * 100
        
        return {
            "status": self._state.status.value,
            "current_stage": self._state.current_stage,
            "total_stages": total_stages,
            "completed_stages": completed,
            "overall_progress": round(overall_progress, 1)
        }
    
    def get_stage_details(self) -> List[Dict[str, Any]]:
        """获取阶段详情"""
        if self._state is None:
            return []
        
        return [
            {
                "name": stage.name,
                "status": stage.status.value,
                "progress": stage.progress,
                "start_time": stage.start_time,
                "end_time": stage.end_time,
                "error": stage.error
            }
            for stage in self._state.stages.values()
        ]
