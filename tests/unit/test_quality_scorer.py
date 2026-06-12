"""
报告质量评分器单元测试
"""

import pytest

from src.quality.scorer import (
    ReportQualityScorer,
    QualityReport,
    QualityGrade,
    CheckResult
)


class TestReportQualityScorer:
    """报告质量评分器测试"""
    
    def setup_method(self):
        self.scorer = ReportQualityScorer()
    
    def test_high_quality_report(self):
        """测试高质量报告"""
        report = """
# 技术评估报告

## 一、执行摘要

基于技术交流素材分析，本技术具有可行性，建议在沈阳项目做试点验证。

## 二、交流背景

- **对方**：艾普罗斯环保科技有限公司
- **时间**：2024年12月15日
- **主题**：餐厨剩余物饲料化技术

## 三、对方技术主张

对方主张：灭菌温度≥135°C（来源：口头）
对方文档显示：产品产率约25%（来源：技术方案.md）

## 四、初步结论

### 4.1 核心发现

分析判断：该技术参数符合行业基准GB/T 28101-2011要求。

### 4.2 推荐建议

建议在沈阳项目做试点，验证技术可行性和经济性。
"""
        
        result = self.scorer.score_report(report)
        
        assert result.total_score >= 60
        assert result.grade in [QualityGrade.A, QualityGrade.B, QualityGrade.C, QualityGrade.D]
    
    def test_low_quality_report(self):
        """测试低质量报告"""
        report = """
技术评估报告
对方说温度135度。
"""
        
        result = self.scorer.score_report(report)
        
        # 低质量报告应该得分较低
        assert result.total_score < 80
        assert result.grade in [QualityGrade.C, QualityGrade.D, QualityGrade.F]
    
    def test_fact_judgment_separation(self):
        """测试事实与判断分离检查"""
        report = """
对方主张：灭菌温度≥135°C（来源：口头）
分析判断：该技术参数高于行业基准。
"""
        
        check_result = self.scorer._check_fact_judgment_separation(report, "", "")
        assert check_result.passed is True
    
    def test_numerical_accuracy(self):
        """测试数值准确性检查"""
        report = """
灭菌温度：135°C
产品产率：25%
处理成本：150元/吨
"""
        
        check_result = self.scorer._check_numerical_accuracy(report, "", "")
        assert check_result.passed is True
    
    def test_pending_verification(self):
        """测试待核实数值"""
        report = """
灭菌温度：135°C [待核实]
产品产率：25% [待核实]
"""
        
        check_result = self.scorer._check_numerical_accuracy(report, "", "")
        assert check_result.score < 100
    
    def test_conflict_detection(self):
        """测试冲突检测"""
        report = """
对方主张灭菌温度≥135°C，与行业基准≥133°C存在差异。
"""
        
        check_result = self.scorer._check_conflict_detection(report, "", "")
        assert check_result.passed is True
    
    def test_no_conflict_detection(self):
        """测试未检测到冲突"""
        report = """
技术参数符合要求。
"""
        
        check_result = self.scorer._check_conflict_detection(report, "", "")
        assert check_result.score < 100
    
    def test_source_attribution(self):
        """测试来源标注"""
        report = """
根据行业标准GB/T 28101-2011，灭菌温度≥133°C。
来源：国家标准原文
"""
        
        check_result = self.scorer._check_source_attribution(report, "", "")
        assert check_result.passed is True
    
    def test_completeness(self):
        """测试完整性"""
        report = """
# 技术评估报告

## 执行摘要
本技术具有可行性。

## 交流背景
对方：艾普罗斯公司

## 对方技术主张
技术原理：高温消毒+固态发酵
关键参数：135°C

## 初步结论
建议试点验证。
存在风险需要关注。
"""
        
        check_result = self.scorer._check_completeness(report, "", "")
        assert check_result.passed is True
    
    def test_incomplete_report(self):
        """测试不完整报告"""
        report = """
温度135度。
"""
        
        check_result = self.scorer._check_completeness(report, "", "")
        assert check_result.passed is False
    
    def test_quality_grade_calculation(self):
        """测试质量等级计算"""
        assert self.scorer._calculate_grade(95) == QualityGrade.A
        assert self.scorer._calculate_grade(85) == QualityGrade.B
        assert self.scorer._calculate_grade(75) == QualityGrade.C
        assert self.scorer._calculate_grade(65) == QualityGrade.D
        assert self.scorer._calculate_grade(55) == QualityGrade.F
    
    def test_recommendations_generation(self):
        """测试改进建议生成"""
        report = """
温度135度。
"""
        
        result = self.scorer.score_report(report)
        
        assert len(result.recommendations) > 0
    
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
分析判断：该技术参数符合行业标准GB/T 28101-2011。

存在差异需要进一步验证。
建议先做试点。
存在风险：焦化问题。
"""
        
        result = self.scorer.score_report(report)
        
        assert "total_score" in dir(result)
        assert "grade" in dir(result)
        assert "checks" in dir(result)
        assert "summary" in dir(result)
        assert "recommendations" in dir(result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
