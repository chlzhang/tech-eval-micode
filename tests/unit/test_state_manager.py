"""
状态管理器单元测试
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from src.state.manager import (
    StateManager,
    PipelineState,
    PipelineStatus,
    StageState,
    StageStatus
)


class TestStateManager:
    """状态管理器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.checkpoint_dir = Path(self.temp_dir) / "checkpoints"
        self.manager = StateManager(str(self.checkpoint_dir))
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_create_pipeline(self):
        """测试创建流水线"""
        state = self.manager.create_pipeline("test_pipeline")
        
        assert state.pipeline_id == "test_pipeline"
        assert state.status == PipelineStatus.PENDING
        assert self.manager.state is state
    
    def test_add_stage(self):
        """测试添加阶段"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.add_stage("stage1")
        self.manager.add_stage("stage2")
        
        assert "stage1" in self.manager.state.stages
        assert "stage2" in self.manager.state.stages
    
    def test_start_pipeline(self):
        """测试启动流水线"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.start_pipeline()
        
        assert self.manager.state.status == PipelineStatus.RUNNING
        assert self.manager.state.start_time is not None
    
    def test_stage_lifecycle(self):
        """测试阶段生命周期"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.add_stage("stage1")
        self.manager.start_pipeline()
        
        # 启动阶段
        self.manager.start_stage("stage1")
        assert self.manager.state.stages["stage1"].status == StageStatus.RUNNING
        assert self.manager.state.current_stage == "stage1"
        
        # 更新进度
        self.manager.update_stage_progress("stage1", 50.0)
        assert self.manager.state.stages["stage1"].progress == 50.0
        
        # 完成阶段
        self.manager.complete_stage("stage1", {"result": "success"})
        assert self.manager.state.stages["stage1"].status == StageStatus.COMPLETED
        assert self.manager.state.stages["stage1"].progress == 100.0
    
    def test_stage_failure(self):
        """测试阶段失败"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.add_stage("stage1")
        self.manager.start_pipeline()
        
        self.manager.start_stage("stage1")
        self.manager.fail_stage("stage1", "测试错误")
        
        assert self.manager.state.stages["stage1"].status == StageStatus.FAILED
        assert self.manager.state.stages["stage1"].error == "测试错误"
        assert "stage1: 测试错误" in self.manager.state.errors
    
    def test_stage_skip(self):
        """测试跳过阶段"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.add_stage("stage1")
        self.manager.start_pipeline()
        
        self.manager.skip_stage("stage1", "条件不满足")
        
        assert self.manager.state.stages["stage1"].status == StageStatus.SKIPPED
    
    def test_complete_pipeline(self):
        """测试完成流水线"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.add_stage("stage1")
        self.manager.start_pipeline()
        
        self.manager.start_stage("stage1")
        self.manager.complete_stage("stage1")
        
        self.manager.complete_pipeline()
        
        assert self.manager.state.status == PipelineStatus.COMPLETED
        assert self.manager.state.end_time is not None
    
    def test_fail_pipeline(self):
        """测试流水线失败"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.start_pipeline()
        
        self.manager.fail_pipeline("致命错误")
        
        assert self.manager.state.status == PipelineStatus.FAILED
        assert "致命错误" in self.manager.state.errors
    
    def test_pause_resume(self):
        """测试暂停和恢复"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.start_pipeline()
        
        self.manager.pause_pipeline()
        assert self.manager.state.status == PipelineStatus.PAUSED
        
        self.manager.resume_pipeline()
        assert self.manager.state.status == PipelineStatus.RUNNING
    
    def test_save_and_load_checkpoint(self):
        """测试保存和加载检查点"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.add_stage("stage1")
        self.manager.start_pipeline()
        
        self.manager.start_stage("stage1")
        self.manager.update_stage_progress("stage1", 50.0)
        
        # 保存检查点
        self.manager.save_checkpoint("test_checkpoint.json")
        
        # 验证文件存在
        checkpoint_path = self.checkpoint_dir / "test_checkpoint.json"
        assert checkpoint_path.exists()
        
        # 创建新的管理器并加载
        new_manager = StateManager(str(self.checkpoint_dir))
        loaded_state = new_manager.load_checkpoint("test_checkpoint.json")
        
        assert loaded_state.pipeline_id == "test_pipeline"
        assert loaded_state.stages["stage1"].progress == 50.0
    
    def test_load_latest_checkpoint(self):
        """测试加载最新检查点"""
        # 确保目录存在
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.manager.create_pipeline("test_pipeline")
        self.manager.save_checkpoint("checkpoint_1.json")
        
        # 等待一下确保时间戳不同
        import time
        time.sleep(0.5)
        
        self.manager.create_pipeline("test_pipeline2")
        self.manager.save_checkpoint("checkpoint_2.json")
        
        # 验证文件存在
        files = list(self.checkpoint_dir.glob("checkpoint_*.json"))
        assert len(files) == 2, f"Expected 2 files, got {len(files)}"
        
        # 加载最新的
        new_manager = StateManager(str(self.checkpoint_dir))
        loaded = new_manager.load_latest_checkpoint()
        
        # 验证加载成功
        assert loaded is not None
        assert loaded.pipeline_id == "test_pipeline2"
    
    def test_observer_notifications(self):
        """测试观察者通知"""
        notifications = []
        
        def observer(event, data):
            notifications.append({"event": event, "data": data})
        
        self.manager.add_observer(observer)
        
        self.manager.create_pipeline("test_pipeline")
        self.manager.add_stage("stage1")
        self.manager.start_pipeline()
        
        self.manager.start_stage("stage1")
        self.manager.complete_stage("stage1")
        self.manager.complete_pipeline()
        
        # 检查通知事件
        events = [n["event"] for n in notifications]
        assert "pipeline_created" in events
        assert "stage_added" in events
        assert "pipeline_started" in events
        assert "stage_started" in events
        assert "stage_completed" in events
        assert "pipeline_completed" in events
    
    def test_get_progress(self):
        """测试获取进度"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.add_stage("stage1")
        self.manager.add_stage("stage2")
        self.manager.start_pipeline()
        
        # 初始进度
        progress = self.manager.get_progress()
        assert progress["total_stages"] == 2
        assert progress["completed_stages"] == 0
        assert progress["overall_progress"] == 0
        
        # 完成一个阶段
        self.manager.start_stage("stage1")
        self.manager.complete_stage("stage1")
        
        progress = self.manager.get_progress()
        assert progress["completed_stages"] == 1
        assert progress["overall_progress"] == 50.0
    
    def test_get_stage_details(self):
        """测试获取阶段详情"""
        self.manager.create_pipeline("test_pipeline")
        self.manager.add_stage("stage1")
        self.manager.add_stage("stage2")
        self.manager.start_pipeline()
        
        self.manager.start_stage("stage1")
        self.manager.complete_stage("stage1")
        
        details = self.manager.get_stage_details()
        assert len(details) == 2
        
        stage1_detail = next(d for d in details if d["name"] == "stage1")
        assert stage1_detail["status"] == "completed"


class TestPipelineState:
    """流水线状态测试"""
    
    def test_to_dict(self):
        """测试转换为字典"""
        state = PipelineState(
            pipeline_id="test",
            status=PipelineStatus.RUNNING,
            current_stage="stage1"
        )
        state.stages["stage1"] = StageState(
            name="stage1",
            status=StageStatus.RUNNING,
            progress=50.0
        )
        
        data = state.to_dict()
        
        assert data["pipeline_id"] == "test"
        assert data["status"] == "running"
        assert data["stages"]["stage1"]["progress"] == 50.0
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "pipeline_id": "test",
            "status": "completed",
            "current_stage": None,
            "stages": {
                "stage1": {
                    "status": "completed",
                    "progress": 100.0,
                    "start_time": "2024-01-01T00:00:00",
                    "end_time": "2024-01-01T01:00:00",
                    "error": None
                }
            },
            "start_time": "2024-01-01T00:00:00",
            "end_time": "2024-01-01T01:00:00",
            "errors": [],
            "metadata": {}
        }
        
        state = PipelineState.from_dict(data)
        
        assert state.pipeline_id == "test"
        assert state.status == PipelineStatus.COMPLETED
        assert state.stages["stage1"].progress == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
