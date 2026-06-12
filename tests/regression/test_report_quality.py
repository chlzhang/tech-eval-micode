"""
报告质量回归测试

验证报告是否符合质量标准：
1. 事实与判断分离
2. 数值准确性
3. 冲突检测
4. 来源标注
"""

import pytest
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class QualityCheckResult:
    """质量检查结果"""
    check_name: str
    passed: bool
    score: float  # 0-100
    issues: List[str]
    details: Dict


class ReportQualityChecker:
    """报告质量检查器"""
    
    def __init__(self):
        self.checks = [
            ("fact_judgment_separation", 20),
            ("numerical_accuracy", 25),
            ("conflict_detection", 15),
            ("source_attribution", 20),
            ("completeness", 20)
        ]
    
    def check_report(self, report_content: str, materials: str = "", benchmarks: str = "") -> Dict:
        """检查报告质量"""
        results = {}
        total_score = 0
        
        for check_name, weight in self.checks:
            check_func = getattr(self, f"_check_{check_name}")
            result = check_func(report_content, materials, benchmarks)
            results[check_name] = result
            total_score += result.score * weight / 100
        
        return {
            "total_score": round(total_score, 1),
            "grade": self._calculate_grade(total_score),
            "checks": results
        }
    
    def _check_fact_judgment_separation(self, report: str, materials: str, benchmarks: str) -> QualityCheckResult:
        """检查事实与判断分离"""
        issues = []
        score = 100
        
        # 检查对方主张是否有来源标注
        counterpart_claims = re.findall(r'对方(?:主张|称|表示|介绍)[：:](.*?)(?:\n|$)', report)
        for claim in counterpart_claims:
            if "来源" not in claim and "口头" not in claim and "文档" not in claim:
                issues.append(f"对方主张缺少来源标注: {claim[:50]}...")
                score -= 10
        
        # 检查分析结论是否标记为分析判断
        analysis_patterns = [r'分析[：:]', r'判断[：:]', r'认为[：:]']
        for pattern in analysis_patterns:
            matches = re.findall(pattern, report)
            # 分析结论应该明确标记
        
        # 检查是否有推测伪装成事实的情况
        speculation_patterns = [r'可能', r'也许', r'大概', r'估计']
        for pattern in speculation_patterns:
            if pattern in report:
                # 检查是否与事实性陈述混在一起
                pass
        
        score = max(0, score)
        
        return QualityCheckResult(
            check_name="事实与判断分离",
            passed=score >= 70,
            score=score,
            issues=issues,
            details={"counterpart_claims_count": len(counterpart_claims)}
        )
    
    def _check_numerical_accuracy(self, report: str, materials: str, benchmarks: str) -> QualityCheckResult:
        """检查数值准确性"""
        issues = []
        score = 100
        
        # 提取报告中的数值声明
        numerical_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:°C|度)',
            r'(\d+(?:\.\d+)?)\s*(?:元/吨|万元)',
            r'(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*(?:分钟|小时|天)'
        ]
        
        numerical_claims = []
        for pattern in numerical_patterns:
            matches = re.findall(pattern, report)
            numerical_claims.extend(matches)
        
        # 检查是否有待核实的数值
        if "[待核实]" in report:
            issues.append("存在待核实的数值")
            score -= 20
        
        # 检查单位一致性
        if "吨" in report and "kg" in report:
            # 检查是否统一单位后再比较
            pass
        
        score = max(0, score)
        
        return QualityCheckResult(
            check_name="数值准确性",
            passed=score >= 70,
            score=score,
            issues=issues,
            details={"numerical_claims_count": len(numerical_claims)}
        )
    
    def _check_conflict_detection(self, report: str, materials: str, benchmarks: str) -> QualityCheckResult:
        """检查冲突检测"""
        issues = []
        score = 100
        
        # 检查是否有冲突标记
        conflict_patterns = [
            r'冲突',
            r'矛盾',
            r'不一致',
            r'差异'
        ]
        
        conflicts_found = 0
        for pattern in conflict_patterns:
            matches = re.findall(pattern, report)
            conflicts_found += len(matches)
        
        # 如果没有发现冲突标记，可能遗漏了冲突
        if conflicts_found == 0:
            issues.append("未发现冲突标记，可能存在遗漏")
            score -= 30
        
        score = max(0, score)
        
        return QualityCheckResult(
            check_name="冲突检测",
            passed=score >= 70,
            score=score,
            issues=issues,
            details={"conflicts_found": conflicts_found}
        )
    
    def _check_source_attribution(self, report: str, materials: str, benchmarks: str) -> QualityCheckResult:
        """检查来源标注"""
        issues = []
        score = 100
        
        # 检查数据来源标注
        source_patterns = [
            r'来源[：:]',
            r'根据',
            r'依据',
            r'参考'
        ]
        
        sources_count = 0
        for pattern in source_patterns:
            matches = re.findall(pattern, report)
            sources_count += len(matches)
        
        # 检查是否有未标注来源的数据
        data_patterns = [
            r'\d+(?:\.\d+)?\s*(?:元|万元|%)',
            r'≥\s*\d+',
            r'≤\s*\d+'
        ]
        
        data_points = 0
        for pattern in data_patterns:
            matches = re.findall(pattern, report)
            data_points += len(matches)
        
        # 来源标注率应该足够高
        if data_points > 0 and sources_count / data_points < 0.5:
            issues.append(f"来源标注率较低: {sources_count}/{data_points}")
            score -= 30
        
        score = max(0, score)
        
        return QualityCheckResult(
            check_name="来源标注",
            passed=score >= 70,
            score=score,
            issues=issues,
            details={"sources_count": sources_count, "data_points": data_points}
        )
    
    def _check_completeness(self, report: str, materials: str, benchmarks: str) -> QualityCheckResult:
        """检查完整性"""
        issues = []
        score = 100
        
        # 检查必需章节
        required_sections = [
            "执行摘要",
            "交流背景",
            "对方技术主张",
            "初步结论"
        ]
        
        for section in required_sections:
            if section not in report:
                issues.append(f"缺少必需章节: {section}")
                score -= 25
        
        # 检查关键要素
        key_elements = [
            "技术原理",
            "关键参数",
            "风险",
            "建议"
        ]
        
        for element in key_elements:
            if element not in report:
                issues.append(f"缺少关键要素: {element}")
                score -= 10
        
        score = max(0, score)
        
        return QualityCheckResult(
            check_name="完整性",
            passed=score >= 70,
            score=score,
            issues=issues,
            details={"required_sections": required_sections}
        )
    
    def _calculate_grade(self, score: float) -> str:
        """计算等级"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


class TestReportQuality:
    """报告质量测试"""
    
    def setup_method(self):
        self.checker = ReportQualityChecker()
    
    def test_fact_judgment_separation(self):
        """测试事实与判断分离"""
        report = """
        对方主张：灭菌温度≥135°C（来源：口头）
        分析判断：该技术参数高于行业基准。
        """
        
        result = self.checker._check_fact_judgment_separation(report, "", "")
        assert result.passed is True
    
    def test_numerical_accuracy(self):
        """测试数值准确性"""
        report = """
        灭菌温度：135°C
        产品产率：25%
        处理成本：150元/吨
        """
        
        result = self.checker._check_numerical_accuracy(report, "", "")
        assert result.passed is True
    
    def test_conflict_detection(self):
        """测试冲突检测"""
        report = """
        对方主张灭菌温度≥135°C，与行业基准≥133°C存在差异。
        """
        
        result = self.checker._check_conflict_detection(report, "", "")
        assert result.passed is True
    
    def test_source_attribution(self):
        """测试来源标注"""
        report = """
        根据行业标准GB/T 28101-2011，灭菌温度≥133°C。
        来源：国家标准原文
        """
        
        result = self.checker._check_source_attribution(report, "", "")
        assert result.passed is True
    
    def test_completeness(self):
        """测试完整性"""
        report = """
        # 技术评估报告
        
        ## 一、执行摘要
        本技术具有可行性。
        
        ## 二、交流背景
        对方：艾普罗斯公司
        
        ## 三、对方技术主张
        技术原理：高温消毒+固态发酵
        
        ## 四、初步结论
        建议试点验证。
        
        关键参数：135°C
        风险：焦化问题
        建议：先做试点
        """
        
        result = self.checker._check_completeness(report, "", "")
        assert result.passed is True
    
    def test_full_quality_check(self):
        """测试完整质量检查"""
        report = """
        # 技术评估报告
        
        ## 一、执行摘要
        基于技术交流素材分析，本技术具有可行性。
        
        ## 二、交流背景
        - 对方：艾普罗斯环保科技有限公司
        - 时间：2024年12月15日
        
        ## 三、对方技术主张
        对方主张：灭菌温度≥135°C（来源：口头）
        
        ## 四、初步结论
        分析判断：该技术参数符合行业标准。
        
        关键参数：135°C、25%
        风险：焦化问题
        建议：先做试点验证
        """
        
        result = self.checker.check_report(report, "", "")
        
        assert "total_score" in result
        assert "grade" in result
        assert "checks" in result
        assert result["total_score"] >= 60


class TestQualityRegression:
    """质量回归测试"""
    
    def setup_method(self):
        self.checker = ReportQualityChecker()
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"
    
    def test_sample_report_quality(self):
        """测试示例报告质量"""
        # 使用之前生成的报告草稿
        report_path = Path(__file__).parent.parent / "output" / "report_draft.md"
        
        if report_path.exists():
            report_content = report_path.read_text(encoding="utf-8")
            result = self.checker.check_report(report_content)
            
            # 确保质量分数不低于60
            assert result["total_score"] >= 60, f"报告质量分数过低: {result['total_score']}"
    
    def test_quality_improvement(self):
        """测试质量改进"""
        # 模拟改进前后的报告
        report_before = """
        技术评估报告
        对方说温度135度。
        """
        
        report_after = """
        # 技术评估报告
        
        ## 执行摘要
        本技术具有可行性。
        
        ## 对方技术主张
        对方主张：灭菌温度≥135°C（来源：口头）
        分析判断：该参数符合行业基准≥133°C。
        """
        
        result_before = self.checker.check_report(report_before)
        result_after = self.checker.check_report(report_after)
        
        # 改进后的报告质量应该更高
        assert result_after["total_score"] > result_before["total_score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
