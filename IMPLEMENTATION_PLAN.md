# 架构优化实施计划

基于架构分析报告，制定具体的实施计划。

---

## 第一阶段：夯实基础（立即开始，2周内完成）

### 1.1 建立测试框架

**目标：** 实现自动化测试，确保代码质量

**任务清单：**
- [ ] 创建测试目录结构
- [ ] 编写单元测试（各组件）
- [ ] 编写集成测试（端到端流程）
- [ ] 建立回归测试套件

**目录结构：**
```
tests/
├── unit/
│   ├── test_material_reader.py
│   ├── test_benchmark_searcher.py
│   ├── test_report_writer.py
│   └── test_fact_checker.py
├── integration/
│   ├── test_pipeline_flow.py
│   └── test_agent_coordination.py
├── regression/
│   ├── test_report_quality.py
│   └── test_output_consistency.py
└── fixtures/
    ├── sample_transcript.md
    ├── sample_counterpart/
    └── sample_benchmark/
```

**示例测试代码：**
```python
# tests/unit/test_fact_checker.py
import pytest
from src.agents.fact_checker import FactChecker

class TestFactChecker:
    def setup_method(self):
        self.checker = FactChecker()
    
    def test_unit_conversion(self):
        """测试单位换算正确性"""
        result = self.checker.convert_units(1000, "kg", "吨")
        assert result == 1.0
    
    def test_numerical_claim_verification(self):
        """测试数值声明验证"""
        claim = "灭菌温度 >= 135°C"
        source = "标准要求灭菌温度不低于133°C"
        result = self.checker.verify_claim(claim, source)
        assert result.is_consistent == True
```

---

### 1.2 配置外部化

**目标：** 将硬编码参数提取到配置文件

**任务清单：**
- [ ] 创建配置文件模板
- [ ] 实现配置加载器
- [ ] 添加配置验证
- [ ] 支持环境变量覆盖

**配置文件结构：**
```
config/
├── default.yaml          # 默认配置
├── production.yaml       # 生产环境配置
├── development.yaml      # 开发环境配置
└── templates/
    ├── pipeline.yaml     # 流水线配置模板
    └── agents.yaml       # Agent 配置模板
```

**配置示例：**
```yaml
# config/default.yaml
app:
  name: tech-exchange-evaluator
  version: 1.0.0

pipeline:
  max_parallel_agents: 3
  timeout_minutes: 30
  retry_attempts: 2
  
search:
  max_queries: 7
  timeout_seconds: 30
  min_results_threshold: 3
  
output:
  formats:
    - docx
    - html
  chart_library: chartjs
  
logging:
  level: INFO
  file: output/evaluation.log
```

---

## 第二阶段：架构优化（1个月内完成）

### 2.1 流水线引擎

**目标：** 实现动态可配置的流水线

**核心组件：**
```python
# src/pipeline/engine.py
class PipelineEngine:
    def __init__(self, config):
        self.config = config
        self.stages = []
        self.state_manager = StateManager()
    
    def add_stage(self, stage):
        """添加处理阶段"""
        self.stages.append(stage)
    
    async def execute(self, input_data):
        """执行流水线"""
        context = PipelineContext(input_data)
        
        for stage in self.stages:
            if stage.condition and not stage.condition(context):
                continue
            
            self.state_manager.update(stage.name, "running")
            
            try:
                result = await stage.execute(context)
                context.merge(result)
                self.state_manager.update(stage.name, "completed")
            except Exception as e:
                self.state_manager.update(stage.name, "failed", str(e))
                if stage.critical:
                    raise
                continue
        
        return context.output
```

**流水线配置：**
```yaml
# config/pipeline.yaml
stages:
  - name: parallel_extraction
    type: parallel
    agents:
      - material_reader
      - benchmark_searcher
    timeout: 10m
    
  - name: report_synthesis
    type: sequential
    agents:
      - report_writer
    depends_on:
      - parallel_extraction
    
  - name: quality_assurance
    type: sequential
    agents:
      - critic_reviewer
      - fact_checker
    depends_on:
      - report_synthesis
    
  - name: output_generation
    type: parallel
    agents:
      - docx_generator
      - html_generator
    depends_on:
      - quality_assurance
```

---

### 2.2 状态管理

**目标：** 实现全局状态追踪和断点续传

**状态管理器：**
```python
# src/state/manager.py
class StateManager:
    def __init__(self):
        self.state = PipelineState()
        self.observers = []
    
    def update(self, stage, status, details=None):
        """更新阶段状态"""
        self.state.stages[stage] = {
            "status": status,
            "details": details,
            "updated_at": datetime.now()
        }
        self._notify_observers(stage, status)
    
    def save_checkpoint(self):
        """保存检查点"""
        checkpoint = {
            "state": self.state.to_dict(),
            "context": self.context.to_dict(),
            "timestamp": datetime.now()
        }
        save_to_file("checkpoint.json", checkpoint)
    
    def load_checkpoint(self):
        """加载检查点"""
        checkpoint = load_from_file("checkpoint.json")
        self.state = PipelineState.from_dict(checkpoint["state"])
        self.context = PipelineContext.from_dict(checkpoint["context"])
```

---

### 2.3 Agent 通信优化

**目标：** 替换文件系统通信，使用消息队列

**消息队列实现：**
```python
# src/communication/queue.py
import asyncio
from dataclasses import dataclass
from typing import Any

@dataclass
class AgentMessage:
    sender: str
    receiver: str
    data: Any
    message_type: str
    timestamp: datetime

class MessageQueue:
    def __init__(self):
        self.queues = {}
        self.subscribers = {}
    
    async def publish(self, message: AgentMessage):
        """发布消息"""
        if message.receiver not in self.queues:
            self.queues[message.receiver] = asyncio.Queue()
        await self.queues[message.receiver].put(message)
    
    async def subscribe(self, agent_id: str, callback):
        """订阅消息"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)
        
        # 启动消费者
        if agent_id not in self.queues:
            self.queues[agent_id] = asyncio.Queue()
        
        asyncio.create_task(self._consume(agent_id))
    
    async def _consume(self, agent_id: str):
        """消费消息"""
        while True:
            message = await self.queues[agent_id].get()
            for callback in self.subscribers.get(agent_id, []):
                await callback(message)
```

---

## 第三阶段：质量保障（2个月内完成）

### 3.1 搜索质量提升

**目标：** 提高搜索结果的准确性和覆盖率

**搜索验证器：**
```python
# src/search/validator.py
class SearchValidator:
    def __init__(self, config):
        self.config = config
    
    def validate_results(self, query, results):
        """验证搜索结果质量"""
        validation = {
            "query": query,
            "result_count": len(results),
            "quality_score": 0,
            "issues": []
        }
        
        # 检查结果数量
        if len(results) < self.config.min_results:
            validation["issues"].append("结果数量不足")
        
        # 检查相关性
        relevance_scores = [self._calculate_relevance(query, r) for r in results]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        if avg_relevance < 0.5:
            validation["issues"].append("相关性较低")
        
        # 检查时效性
        recency_scores = [self._check_recency(r) for r in results]
        avg_recency = sum(recency_scores) / len(recency_scores)
        if avg_recency < 0.6:
            validation["issues"].append("数据较旧")
        
        validation["quality_score"] = (avg_relevance + avg_recency) / 2
        return validation
```

---

### 3.2 报告质量自动化

**目标：** 建立自动化的质量评分系统

**质量评分器：**
```python
# src/quality/scorer.py
class QualityScorer:
    def __init__(self):
        self.checks = [
            ("fact_judgment_separation", 0.2),
            ("numerical_accuracy", 0.25),
            ("conflict_detection", 0.15),
            ("source_attribution", 0.2),
            ("completeness", 0.2)
        ]
    
    def score_report(self, report, materials, benchmarks):
        """计算报告质量分数"""
        scores = {}
        
        for check_name, weight in self.checks:
            check_func = getattr(self, f"_check_{check_name}")
            score = check_func(report, materials, benchmarks)
            scores[check_name] = score * weight
        
        total_score = sum(scores.values())
        return {
            "total": total_score,
            "breakdown": scores,
            "grade": self._calculate_grade(total_score)
        }
    
    def _check_fact_judgment_separation(self, report, materials, benchmarks):
        """检查事实与判断分离"""
        violations = 0
        for claim in report.claims:
            if claim.type == "对方主张" and not claim.source:
                violations += 1
        return max(0, 1 - violations / len(report.claims))
```

---

### 3.3 安全加固

**目标：** 修复安全漏洞，防止注入攻击

**输入验证器：**
```python
# src/security/validator.py
import re
from typing import Any

class InputValidator:
    def __init__(self):
        self.patterns = {
            "script": re.compile(r"<script.*?</script>", re.IGNORECASE | re.DOTALL),
            "event_handler": re.compile(r"on\w+\s*=", re.IGNORECASE),
            "iframe": re.compile(r"<iframe.*?</iframe>", re.IGNORECASE | re.DOTALL)
        }
    
    def sanitize(self, input_data: Any) -> Any:
        """清理输入数据"""
        if isinstance(input_data, str):
            return self._sanitize_string(input_data)
        elif isinstance(input_data, dict):
            return {k: self.sanitize(v) for k, v in input_data.items()}
        elif isinstance(input_data, list):
            return [self.sanitize(item) for item in input_data]
        return input_data
    
    def _sanitize_string(self, text: str) -> str:
        """清理字符串"""
        for pattern_name, pattern in self.patterns.items():
            text = pattern.sub("", text)
        return text
```

---

## 实施时间表

```
第1周：
├── 建立测试目录结构
├── 编写核心组件单元测试
└── 创建配置文件模板

第2周：
├── 实现配置加载器
├── 添加配置验证
└── 完成集成测试框架

第3-4周：
├── 实现流水线引擎
├── 实现状态管理器
└── 优化 Agent 通信

第5-6周：
├── 实现搜索验证器
├── 实现质量评分器
└── 添加安全加固

第7-8周：
├── 端到端测试
├── 性能优化
└── 文档更新
```

---

## 成功指标

| 指标 | 当前值 | 目标值 | 衡量方式 |
|------|--------|--------|----------|
| 测试覆盖率 | 0% | 80% | pytest-cov |
| 报告质量评分 | N/A | >85分 | QualityScorer |
| 搜索结果相关性 | N/A | >0.7 | SearchValidator |
| 执行时间 | 未知 | <15分钟 | 性能测试 |
| 错误率 | 未知 | <5% | 日志分析 |

---

## 风险和缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 测试数据不足 | 无法覆盖所有场景 | 建立测试数据生成器 |
| 性能下降 | 用户体验差 | 性能基准测试 + 优化 |
| 配置错误 | 系统异常 | 配置验证 + 默认值 |
| 依赖升级 | 兼容性问题 | 版本锁定 + 测试 |

---

*计划制定时间：2026-06-12*
*负责人：系统架构师*
