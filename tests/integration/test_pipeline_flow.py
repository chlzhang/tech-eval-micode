"""
流水线流程集成测试

测试三阶段流水线的完整流程：
1. Phase 1：并行读取与检索
2. Phase 2：报告撰写
3. Phase 3：双格式输出
"""

import pytest
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class PipelineConfig:
    """流水线配置"""
    input_dir: str = "input"
    output_dir: str = "output"
    version: str = "精简版"  # 精简版/完整版
    max_parallel_agents: int = 2
    timeout_minutes: int = 30


@dataclass
class PipelineState:
    """流水线状态"""
    pipeline_id: str
    status: str  # pending, running, completed, failed
    current_phase: str
    start_time: datetime
    end_time: datetime = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class PipelineEngine:
    """流水线引擎"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.state = None
    
    def create_pipeline(self) -> str:
        """创建流水线"""
        pipeline_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.state = PipelineState(
            pipeline_id=pipeline_id,
            status="pending",
            current_phase="initialization",
            start_time=datetime.now()
        )
        return pipeline_id
    
    def validate_inputs(self) -> bool:
        """验证输入文件"""
        input_dir = Path(self.config.input_dir)
        
        # 检查必需的转写文本
        transcript_path = input_dir / "transcript.md"
        if not transcript_path.exists():
            raise FileNotFoundError("缺少必需的转写文本: input/transcript.md")
        
        return True
    
    def run_phase1(self) -> Dict[str, Any]:
        """执行 Phase 1：并行读取与检索"""
        self.state.current_phase = "phase1"
        self.state.status = "running"
        
        results = {
            "materials": None,
            "benchmarks": None
        }
        
        # 模拟并行执行 Agent-A 和 Agent-B
        # Agent-A：素材读取
        materials_path = Path(self.config.input_dir) / "transcript.md"
        if materials_path.exists():
            results["materials"] = materials_path.read_text(encoding="utf-8")
        
        # Agent-B：行业检索（模拟）
        results["benchmarks"] = self._simulate_benchmark_search()
        
        return results
    
    def run_phase2(self, phase1_results: Dict[str, Any]) -> str:
        """执行 Phase 2：报告撰写"""
        self.state.current_phase = "phase2"
        
        # 读取素材和基准
        materials = phase1_results.get("materials", "")
        benchmarks = phase1_results.get("benchmarks", {})
        
        # 生成报告草稿
        report_draft = self._generate_report_draft(materials, benchmarks)
        
        # 保存报告草稿
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        draft_path = output_dir / "report_draft.md"
        draft_path.write_text(report_draft, encoding="utf-8")
        
        return str(draft_path)
    
    def run_phase3(self, report_path: str) -> Dict[str, str]:
        """执行 Phase 3：双格式输出"""
        self.state.current_phase = "phase3"
        
        output_files = {}
        
        # 读取报告内容
        report_content = Path(report_path).read_text(encoding="utf-8")
        
        # 生成 DOCX（模拟）
        docx_path = self._generate_docx(report_content)
        output_files["docx"] = docx_path
        
        # 生成 HTML
        html_path = self._generate_html(report_content)
        output_files["html"] = html_path
        
        # 生成图表数据 JSON
        json_path = self._generate_chart_data(report_content)
        output_files["json"] = json_path
        
        return output_files
    
    def _simulate_benchmark_search(self) -> Dict[str, Any]:
        """模拟行业检索"""
        return {
            "standards": [
                {"name": "GB/T 28101-2011", "content": "灭菌温度≥133°C"},
                {"name": "GB 13078-2017", "content": "饲料卫生标准"}
            ],
            "economic_data": {
                "investment_per_ton": "80-120万/吨",
                "operation_cost": "150-200元/吨"
            },
            "risk_factors": ["焦化问题", "政策变化", "市场竞争"]
        }
    
    def _generate_report_draft(self, materials: str, benchmarks: Dict) -> str:
        """生成报告草稿"""
        # 简化实现
        return """# 技术评估报告

## 一、执行摘要

基于技术交流素材和行业基准分析，本技术具有一定的可行性，但需要进一步验证。

## 二、交流背景

- **对方**：艾普罗斯环保科技有限公司
- **时间**：2024年12月15日
- **主题**：餐厨剩余物饲料化技术

## 三、对方技术主张

### 3.1 核心技术原理

采用"高温消毒+固态发酵"工艺路线。

### 3.2 关键技术参数

| 参数 | 对方主张 | 行业基准 |
|------|----------|----------|
| 灭菌温度 | ≥135°C | ≥133°C |
| 产品产率 | 25% | 20-30% |

## 四、初步结论

### 4.1 核心发现

1. 技术原理可行，符合行业标准
2. 经济性需进一步验证

### 4.2 推荐方案

建议在沈阳项目做试点，验证技术可行性和经济性。
"""
    
    def _generate_docx(self, content: str) -> str:
        """生成 DOCX 文件（模拟）"""
        output_dir = Path(self.config.output_dir)
        docx_path = output_dir / f"技术评估报告_{datetime.now().strftime('%Y%m%d')}.docx"
        
        # 实际应该使用 minimax-docx 技能
        # 这里只创建占位文件
        docx_path.write_text("DOCX placeholder", encoding="utf-8")
        
        return str(docx_path)
    
    def _generate_html(self, content: str) -> str:
        """生成 HTML 文件"""
        output_dir = Path(self.config.output_dir)
        html_path = output_dir / f"技术评估报告_{datetime.now().strftime('%Y%m%d')}.html"
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>技术评估报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        details {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
        summary {{ cursor: pointer; font-weight: bold; }}
    </style>
</head>
<body>
    {content}
</body>
</html>"""
        
        html_path.write_text(html_content, encoding="utf-8")
        
        return str(html_path)
    
    def _generate_chart_data(self, content: str) -> str:
        """生成图表数据 JSON"""
        output_dir = Path(self.config.output_dir)
        json_path = output_dir / "report_data.json"
        
        chart_data = {
            "title": "技术评估报告",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tech_topic": "餐厨剩余物饲料化",
            "version": self.config.version,
            "charts": {
                "benchmark_comparison": {
                    "title": "对方主张 vs 行业基准",
                    "type": "bar_grouped",
                    "labels": ["灭菌温度(°C)", "产品产率(%)"],
                    "datasets": [
                        {"label": "对方主张", "data": [135, 25]},
                        {"label": "行业基准", "data": [133, 20]}
                    ]
                }
            }
        }
        
        json_path.write_text(json.dumps(chart_data, ensure_ascii=False, indent=2), encoding="utf-8")
        
        return str(json_path)


class TestPipelineFlow:
    """流水线流程测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"
        self.output_dir = Path(__file__).parent.parent / "output"
        
        # 创建临时输入目录
        self.input_dir = Path(__file__).parent.parent / "temp_input"
        self.input_dir.mkdir(exist_ok=True)
        
        # 复制测试数据
        import shutil
        shutil.copy(
            self.fixtures_dir / "sample_transcript.md",
            self.input_dir / "transcript.md"
        )
        
        # 创建配置
        self.config = PipelineConfig(
            input_dir=str(self.input_dir),
            output_dir=str(self.output_dir),
            version="精简版"
        )
        
        self.engine = PipelineEngine(self.config)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        if self.input_dir.exists():
            shutil.rmtree(self.input_dir)
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
    
    def test_create_pipeline(self):
        """测试创建流水线"""
        pipeline_id = self.engine.create_pipeline()
        
        assert pipeline_id is not None
        assert pipeline_id.startswith("pipeline_")
        assert self.engine.state.status == "pending"
    
    def test_validate_inputs_success(self):
        """测试输入验证成功"""
        self.engine.create_pipeline()
        assert self.engine.validate_inputs() is True
    
    def test_validate_inputs_missing_transcript(self):
        """测试缺少转写文本"""
        self.engine.create_pipeline()
        
        # 删除转写文本
        transcript_path = self.input_dir / "transcript.md"
        transcript_path.unlink()
        
        with pytest.raises(FileNotFoundError, match="缺少必需的转写文本"):
            self.engine.validate_inputs()
    
    def test_run_phase1(self):
        """测试 Phase 1 执行"""
        self.engine.create_pipeline()
        self.engine.validate_inputs()
        
        results = self.engine.run_phase1()
        
        assert results["materials"] is not None
        assert results["benchmarks"] is not None
        assert "standards" in results["benchmarks"]
    
    def test_run_phase2(self):
        """测试 Phase 2 执行"""
        self.engine.create_pipeline()
        self.engine.validate_inputs()
        
        phase1_results = self.engine.run_phase1()
        report_path = self.engine.run_phase2(phase1_results)
        
        assert Path(report_path).exists()
        
        report_content = Path(report_path).read_text(encoding="utf-8")
        assert "技术评估报告" in report_content
        assert "执行摘要" in report_content
    
    def test_run_phase3(self):
        """测试 Phase 3 执行"""
        self.engine.create_pipeline()
        self.engine.validate_inputs()
        
        phase1_results = self.engine.run_phase1()
        report_path = self.engine.run_phase2(phase1_results)
        output_files = self.engine.run_phase3(report_path)
        
        assert "docx" in output_files
        assert "html" in output_files
        assert "json" in output_files
        
        # 验证 HTML 文件
        html_path = output_files["html"]
        assert Path(html_path).exists()
        
        html_content = Path(html_path).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html_content
        assert "chart.js" in html_content.lower()
        
        # 验证 JSON 文件
        json_path = output_files["json"]
        assert Path(json_path).exists()
        
        chart_data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        assert "charts" in chart_data
        assert "benchmark_comparison" in chart_data["charts"]
    
    def test_full_pipeline_flow(self):
        """测试完整流水线流程"""
        # 创建流水线
        pipeline_id = self.engine.create_pipeline()
        assert self.engine.state.status == "pending"
        
        # 验证输入
        self.engine.validate_inputs()
        
        # Phase 1
        phase1_results = self.engine.run_phase1()
        assert phase1_results["materials"] is not None
        
        # Phase 2
        report_path = self.engine.run_phase2(phase1_results)
        assert Path(report_path).exists()
        
        # Phase 3
        output_files = self.engine.run_phase3(report_path)
        assert len(output_files) == 3
        
        # 验证所有输出文件
        for file_type, file_path in output_files.items():
            assert Path(file_path).exists(), f"{file_type} 文件不存在"


class TestPipelineStateManagement:
    """流水线状态管理测试"""
    
    def test_state_transitions(self):
        """测试状态转换"""
        config = PipelineConfig()
        engine = PipelineEngine(config)
        
        # 创建流水线
        pipeline_id = engine.create_pipeline()
        assert engine.state.status == "pending"
        
        # 开始执行
        engine.run_phase1()
        assert engine.state.status == "running"
        assert engine.state.current_phase == "phase1"
    
    def test_error_handling(self):
        """测试错误处理"""
        config = PipelineConfig(input_dir="nonexistent")
        engine = PipelineEngine(config)
        
        engine.create_pipeline()
        
        with pytest.raises(FileNotFoundError):
            engine.validate_inputs()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
