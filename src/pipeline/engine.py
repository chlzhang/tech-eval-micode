"""
流水线引擎

提供可配置的流水线执行能力：
1. 动态阶段定义
2. 并行/串行执行
3. 条件分支
4. 错误处理和重试
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum


class StageStatus(Enum):
    """阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


@dataclass
class StageResult:
    """阶段执行结果"""
    stage_name: str
    status: StageStatus
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0


@dataclass
class StageConfig:
    """阶段配置"""
    name: str
    mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    agents: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    condition: Optional[Callable] = None
    timeout_seconds: int = 300
    retry_count: int = 0
    critical: bool = True


class Agent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent 任务"""
        pass


class PipelineContext:
    """流水线上下文"""
    
    def __init__(self, initial_data: Dict[str, Any] = None):
        self.data = initial_data or {}
        self.stage_results: Dict[str, StageResult] = {}
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now(),
            "pipeline_id": None
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置数据"""
        self.data[key] = value
    
    def merge(self, other: Dict[str, Any]):
        """合并数据"""
        self.data.update(other)
    
    def get_stage_result(self, stage_name: str) -> Optional[StageResult]:
        """获取阶段结果"""
        return self.stage_results.get(stage_name)
    
    def set_stage_result(self, stage_name: str, result: StageResult):
        """设置阶段结果"""
        self.stage_results[stage_name] = result


class PipelineEngine:
    """流水线引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.stages: List[StageConfig] = []
        self.agents: Dict[str, Agent] = {}
        self.context: Optional[PipelineContext] = None
        self._observers: List[Callable] = []
    
    def add_stage(self, stage_config: StageConfig):
        """添加阶段"""
        self.stages.append(stage_config)
    
    def register_agent(self, agent: Agent):
        """注册 Agent"""
        self.agents[agent.name] = agent
    
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
    
    def _check_dependencies(self, stage: StageConfig, context: PipelineContext) -> bool:
        """检查依赖是否满足"""
        for dep in stage.depends_on:
            result = context.get_stage_result(dep)
            if result is None or result.status != StageStatus.COMPLETED:
                return False
        return True
    
    def _check_condition(self, stage: StageConfig, context: PipelineContext) -> bool:
        """检查条件是否满足"""
        if stage.condition is None:
            return True
        try:
            return stage.condition(context)
        except Exception:
            return False
    
    async def _execute_agent(self, agent: Agent, context: Dict[str, Any], 
                           timeout: int = 300) -> Dict[str, Any]:
        """执行单个 Agent"""
        try:
            result = await asyncio.wait_for(
                agent.execute(context),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Agent {agent.name} 执行超时")
    
    async def _execute_stage_sequential(self, stage: StageConfig, 
                                       context: PipelineContext) -> StageResult:
        """串行执行阶段"""
        result = StageResult(
            stage_name=stage.name,
            status=StageStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            stage_data = {}
            for agent_name in stage.agents:
                if agent_name not in self.agents:
                    raise ValueError(f"Agent {agent_name} 未注册")
                
                agent = self.agents[agent_name]
                agent_context = {**context.data, **stage_data}
                
                self._notify_observers("agent_start", {
                    "stage": stage.name,
                    "agent": agent_name
                })
                
                agent_result = await self._execute_agent(
                    agent, agent_context, stage.timeout_seconds
                )
                stage_data.update(agent_result)
                
                self._notify_observers("agent_complete", {
                    "stage": stage.name,
                    "agent": agent_name
                })
            
            result.status = StageStatus.COMPLETED
            result.data = stage_data
            
        except Exception as e:
            result.status = StageStatus.FAILED
            result.error = str(e)
            
            self._notify_observers("stage_failed", {
                "stage": stage.name,
                "error": str(e)
            })
            
            if stage.critical:
                raise
        
        finally:
            result.end_time = datetime.now()
            if result.start_time:
                result.duration_seconds = (
                    result.end_time - result.start_time
                ).total_seconds()
        
        return result
    
    async def _execute_stage_parallel(self, stage: StageConfig, 
                                    context: PipelineContext) -> StageResult:
        """并行执行阶段"""
        result = StageResult(
            stage_name=stage.name,
            status=StageStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            tasks = []
            for agent_name in stage.agents:
                if agent_name not in self.agents:
                    raise ValueError(f"Agent {agent_name} 未注册")
                
                agent = self.agents[agent_name]
                task = self._execute_agent(agent, context.data, stage.timeout_seconds)
                tasks.append((agent_name, task))
            
            self._notify_observers("parallel_start", {
                "stage": stage.name,
                "agents": stage.agents
            })
            
            # 并行执行所有任务
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            # 合并结果
            stage_data = {}
            errors = []
            for (agent_name, _), agent_result in zip(tasks, results):
                if isinstance(agent_result, Exception):
                    errors.append(f"{agent_name}: {str(agent_result)}")
                else:
                    stage_data.update(agent_result)
            
            if errors:
                raise Exception(f"并行执行错误: {'; '.join(errors)}")
            
            result.status = StageStatus.COMPLETED
            result.data = stage_data
            
            self._notify_observers("parallel_complete", {
                "stage": stage.name
            })
            
        except Exception as e:
            result.status = StageStatus.FAILED
            result.error = str(e)
            
            self._notify_observers("stage_failed", {
                "stage": stage.name,
                "error": str(e)
            })
            
            if stage.critical:
                raise
        
        finally:
            result.end_time = datetime.now()
            if result.start_time:
                result.duration_seconds = (
                    result.end_time - result.start_time
                ).total_seconds()
        
        return result
    
    async def _execute_stage_with_retry(self, stage: StageConfig, 
                                       context: PipelineContext) -> StageResult:
        """带重试的阶段执行"""
        last_error = None
        
        for attempt in range(stage.retry_count + 1):
            try:
                if stage.mode == ExecutionMode.PARALLEL:
                    return await self._execute_stage_parallel(stage, context)
                else:
                    return await self._execute_stage_sequential(stage, context)
                    
            except Exception as e:
                last_error = e
                if attempt < stage.retry_count:
                    self._notify_observers("stage_retry", {
                        "stage": stage.name,
                        "attempt": attempt + 1,
                        "error": str(e)
                    })
                    await asyncio.sleep(1)  # 重试前等待
        
        # 所有重试都失败
        raise last_error
    
    async def execute(self, initial_data: Dict[str, Any] = None) -> PipelineContext:
        """执行流水线"""
        self.context = PipelineContext(initial_data)
        
        self._notify_observers("pipeline_start", {
            "stages": [s.name for s in self.stages]
        })
        
        try:
            for stage in self.stages:
                # 检查依赖
                if not self._check_dependencies(stage, self.context):
                    result = StageResult(
                        stage_name=stage.name,
                        status=StageStatus.SKIPPED,
                        error="依赖未满足"
                    )
                    self.context.set_stage_result(stage.name, result)
                    continue
                
                # 检查条件
                if not self._check_condition(stage, self.context):
                    result = StageResult(
                        stage_name=stage.name,
                        status=StageStatus.SKIPPED,
                        error="条件未满足"
                    )
                    self.context.set_stage_result(stage.name, result)
                    continue
                
                # 执行阶段
                self._notify_observers("stage_start", {"stage": stage.name})
                
                result = await self._execute_stage_with_retry(stage, self.context)
                self.context.set_stage_result(stage.name, result)
                
                # 合并阶段数据到上下文
                self.context.merge(result.data)
                
                self._notify_observers("stage_complete", {
                    "stage": stage.name,
                    "status": result.status.value
                })
            
            self._notify_observers("pipeline_complete", {
                "status": "success"
            })
            
        except Exception as e:
            self._notify_observers("pipeline_failed", {
                "error": str(e)
            })
            raise
        
        return self.context
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        if not self.context:
            return {"status": "not_started"}
        
        summary = {
            "stages": {},
            "total_duration": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0
        }
        
        for stage in self.stages:
            result = self.context.get_stage_result(stage.name)
            if result:
                summary["stages"][stage.name] = {
                    "status": result.status.value,
                    "duration": result.duration_seconds,
                    "error": result.error
                }
                summary["total_duration"] += result.duration_seconds
                
                if result.status == StageStatus.COMPLETED:
                    summary["completed"] += 1
                elif result.status == StageStatus.FAILED:
                    summary["failed"] += 1
                elif result.status == StageStatus.SKIPPED:
                    summary["skipped"] += 1
        
        return summary
