"""
流水线引擎单元测试
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.pipeline.engine import (
    PipelineEngine,
    PipelineContext,
    Agent,
    StageConfig,
    StageResult,
    StageStatus,
    ExecutionMode
)


class MockAgent(Agent):
    """模拟 Agent"""
    
    def __init__(self, name: str, result: dict = None, delay: float = 0):
        super().__init__(name)
        self.result = result or {"data": f"{name}_result"}
        self.delay = delay
        self.executed = False
    
    async def execute(self, context: dict) -> dict:
        self.executed = True
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return self.result


class FailingAgent(Agent):
    """失败的 Agent"""
    
    def __init__(self, name: str, error_message: str = "Test error"):
        super().__init__(name)
        self.error_message = error_message
    
    async def execute(self, context: dict) -> dict:
        raise Exception(self.error_message)


class TestPipelineEngine:
    """流水线引擎测试"""
    
    def setup_method(self):
        self.engine = PipelineEngine()
    
    def test_create_engine(self):
        """测试创建引擎"""
        assert self.engine is not None
        assert len(self.engine.stages) == 0
        assert len(self.engine.agents) == 0
    
    def test_add_stage(self):
        """测试添加阶段"""
        stage = StageConfig(
            name="test_stage",
            mode=ExecutionMode.SEQUENTIAL,
            agents=["agent1"]
        )
        self.engine.add_stage(stage)
        
        assert len(self.engine.stages) == 1
        assert self.engine.stages[0].name == "test_stage"
    
    def test_register_agent(self):
        """测试注册 Agent"""
        agent = MockAgent("test_agent")
        self.engine.register_agent(agent)
        
        assert "test_agent" in self.engine.agents
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """测试串行执行"""
        agent1 = MockAgent("agent1", {"key1": "value1"})
        agent2 = MockAgent("agent2", {"key2": "value2"})
        
        self.engine.register_agent(agent1)
        self.engine.register_agent(agent2)
        
        stage = StageConfig(
            name="test_stage",
            mode=ExecutionMode.SEQUENTIAL,
            agents=["agent1", "agent2"]
        )
        self.engine.add_stage(stage)
        
        context = await self.engine.execute()
        
        assert context.get("key1") == "value1"
        assert context.get("key2") == "value2"
        assert agent1.executed is True
        assert agent2.executed is True
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """测试并行执行"""
        agent1 = MockAgent("agent1", {"key1": "value1"})
        agent2 = MockAgent("agent2", {"key2": "value2"})
        
        self.engine.register_agent(agent1)
        self.engine.register_agent(agent2)
        
        stage = StageConfig(
            name="test_stage",
            mode=ExecutionMode.PARALLEL,
            agents=["agent1", "agent2"]
        )
        self.engine.add_stage(stage)
        
        context = await self.engine.execute()
        
        assert context.get("key1") == "value1"
        assert context.get("key2") == "value2"
    
    @pytest.mark.asyncio
    async def test_stage_dependencies(self):
        """测试阶段依赖"""
        agent1 = MockAgent("agent1", {"key1": "value1"})
        agent2 = MockAgent("agent2", {"key2": "value2"})
        
        self.engine.register_agent(agent1)
        self.engine.register_agent(agent2)
        
        stage1 = StageConfig(
            name="stage1",
            mode=ExecutionMode.SEQUENTIAL,
            agents=["agent1"]
        )
        stage2 = StageConfig(
            name="stage2",
            mode=ExecutionMode.SEQUENTIAL,
            agents=["agent2"],
            depends_on=["stage1"]
        )
        
        self.engine.add_stage(stage1)
        self.engine.add_stage(stage2)
        
        context = await self.engine.execute()
        
        assert context.get("key1") == "value1"
        assert context.get("key2") == "value2"
    
    @pytest.mark.asyncio
    async def test_stage_condition(self):
        """测试阶段条件"""
        agent = MockAgent("agent1", {"key1": "value1"})
        self.engine.register_agent(agent)
        
        # 条件为 False 的阶段应该被跳过
        stage = StageConfig(
            name="test_stage",
            mode=ExecutionMode.SEQUENTIAL,
            agents=["agent1"],
            condition=lambda ctx: False
        )
        self.engine.add_stage(stage)
        
        context = await self.engine.execute()
        
        assert context.get("key1") is None
        assert agent.executed is False
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        agent = FailingAgent("failing_agent")
        self.engine.register_agent(agent)
        
        stage = StageConfig(
            name="test_stage",
            mode=ExecutionMode.SEQUENTIAL,
            agents=["failing_agent"],
            critical=True
        )
        self.engine.add_stage(stage)
        
        with pytest.raises(Exception, match="Test error"):
            await self.engine.execute()
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """测试重试机制"""
        agent = FailingAgent("failing_agent")
        self.engine.register_agent(agent)
        
        stage = StageConfig(
            name="test_stage",
            mode=ExecutionMode.SEQUENTIAL,
            agents=["failing_agent"],
            retry_count=2,
            critical=True
        )
        self.engine.add_stage(stage)
        
        with pytest.raises(Exception):
            await self.engine.execute()
        
        # 应该执行了 3 次（初始 + 2 次重试）
    
    @pytest.mark.asyncio
    async def test_observer_notifications(self):
        """测试观察者通知"""
        notifications = []
        
        def observer(event, data):
            notifications.append({"event": event, "data": data})
        
        self.engine.add_observer(observer)
        
        agent = MockAgent("agent1", {"key1": "value1"})
        self.engine.register_agent(agent)
        
        stage = StageConfig(
            name="test_stage",
            mode=ExecutionMode.SEQUENTIAL,
            agents=["agent1"]
        )
        self.engine.add_stage(stage)
        
        await self.engine.execute()
        
        # 检查通知
        events = [n["event"] for n in notifications]
        assert "pipeline_start" in events
        assert "stage_start" in events
        assert "stage_complete" in events
        assert "pipeline_complete" in events
    
    def test_execution_summary(self):
        """测试执行摘要"""
        summary = self.engine.get_execution_summary()
        assert summary["status"] == "not_started"


class TestPipelineContext:
    """流水线上下文测试"""
    
    def test_create_context(self):
        """测试创建上下文"""
        context = PipelineContext({"key1": "value1"})
        assert context.get("key1") == "value1"
    
    def test_set_and_get(self):
        """测试设置和获取"""
        context = PipelineContext()
        context.set("key1", "value1")
        assert context.get("key1") == "value1"
    
    def test_merge(self):
        """测试合并"""
        context = PipelineContext({"key1": "value1"})
        context.merge({"key2": "value2"})
        
        assert context.get("key1") == "value1"
        assert context.get("key2") == "value2"
    
    def test_stage_results(self):
        """测试阶段结果"""
        context = PipelineContext()
        result = StageResult(
            stage_name="test",
            status=StageStatus.COMPLETED,
            data={"key1": "value1"}
        )
        
        context.set_stage_result("test", result)
        
        retrieved = context.get_stage_result("test")
        assert retrieved is not None
        assert retrieved.status == StageStatus.COMPLETED


class TestStageConfig:
    """阶段配置测试"""
    
    def test_default_values(self):
        """测试默认值"""
        config = StageConfig(name="test")
        
        assert config.name == "test"
        assert config.mode == ExecutionMode.SEQUENTIAL
        assert config.timeout_seconds == 300
        assert config.retry_count == 0
        assert config.critical is True
    
    def test_custom_values(self):
        """测试自定义值"""
        config = StageConfig(
            name="test",
            mode=ExecutionMode.PARALLEL,
            agents=["a1", "a2"],
            depends_on=["prev"],
            timeout_seconds=600,
            retry_count=3,
            critical=False
        )
        
        assert config.mode == ExecutionMode.PARALLEL
        assert len(config.agents) == 2
        assert config.retry_count == 3
        assert config.critical is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
