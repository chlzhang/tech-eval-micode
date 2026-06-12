"""
报告质量评分器

提供自动化报告质量评估：
1. 事实与判断分离检查
2. 数值准确性验证
3. 冲突检测
4. 来源标注完整性
5. 结构完整性检查
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class QualityGrade(Enum):
    """质量等级"""
    A = "A"  # 90-100分
    B = "B"  # 80-89分
    C = "C"  # 70-79分
    D = "D"  # 60-69分
    F = "F"  # <60分


@dataclass
class CheckResult:
    """检查结果"""
    check_name: str
    passed: bool
    score: float  # 0-100
    weight: float  # 权重
    issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """质量报告"""
    total_score: float
    grade: QualityGrade
    checks: Dict[str, CheckResult]
    summary: str
    recommendations: List[str] = field(default_factory=list)


class ReportQualityScorer:
    """报告质量评分器"""
    
    def __init__(self):
        self.checks = {
            "fact_judgment_separation": {"weight": 20, "checker": self._check_fact_judgment_separation},
            "numerical_accuracy": {"weight": 25, "checker": self._check_numerical_accuracy},
            "conflict_detection": {"weight": 15, "checker": self._check_conflict_detection},
            "source_attribution": {"weight": 20, "checker": self._check_source_attribution},
            "completeness": {"weight": 20, "checker": self._check_completeness}
        }
    
    def score_report(self, report: str, materials: str = "", benchmarks: str = "") -> QualityReport:
        """评分报告"""
        check_results = {}
        total_score = 0.0
        
        for check_name, check_config in self.checks.items():
            checker = check_config["checker"]
            weight = check_config["weight"]
            
            result = checker(report, materials, benchmarks)
            result.weight = weight
            check_results[check_name] = result
            
            total_score += result.score * weight / 100
        
        grade = self._calculate_grade(total_score)
        summary = self._generate_summary(check_results, total_score, grade)
        recommendations = self._generate_recommendations(check_results)
        
        return QualityReport(
            total_score=round(total_score, 1),
            grade=grade,
            checks=check_results,
            summary=summary,
            recommendations=recommendations
        )
    
    def _check_fact_judgment_separation(self, report: str, materials: str, benchmarks: str) -> CheckResult:
        """检查事实与判断分离"""
        issues = []
        score = 100.0
        
        # 检查对方主张是否有来源标注
        counterpart_patterns = [
            r'对方(?:主张|称|表示|介绍|认为)[：:]',
            r'对方文档(?:显示|指出|表明)[：:]'
        ]
        
        counterpart_claims = []
        for pattern in counterpart_patterns:
            matches = re.findall(pattern + r'.*?(?=\n|$)', report)
            counterpart_claims.extend(matches)
        
        for claim in counterpart_claims:
            if "来源" not in claim and "口头" not in claim and "文档" not in claim:
                issues.append(f"对方主张缺少来源标注")
                score -= 5
        
        # 检查分析结论是否标记为分析判断
        analysis_patterns = [
            r'(?:分析|判断|认为|建议)[：:]',
            r'(?:基于|根据).*(?:分析|判断|认为)'
        ]
        
        analysis_count = 0
        for pattern in analysis_patterns:
            analysis_count += len(re.findall(pattern, report))
        
        # 检查是否有推测伪装成事实
        speculation_words = ["可能", "也许", "大概", "估计", "或许"]
        fact_patterns = [r'(?:是|为|等于|达到|实现).*?(?:' + '|'.join(speculation_words) + ')']
        
        for pattern in fact_patterns:
            matches = re.findall(pattern, report)
            if matches:
                issues.append("发现推测与事实混用")
                score -= 10
        
        return CheckResult(
            check_name="事实与判断分离",
            passed=score >= 70,
            score=max(0, score),
            weight=0,
            issues=issues,
            details={
                "counterpart_claims_count": len(counterpart_claims),
                "analysis_count": analysis_count
            }
        )
    
    def _check_numerical_accuracy(self, report: str, materials: str, benchmarks: str) -> CheckResult:
        """检查数值准确性"""
        issues = []
        score = 100.0
        
        # 提取数值声明
        numerical_patterns = [
            (r'(\d+(?:\.\d+)?)\s*(?:°C|度)', "温度"),
            (r'(\d+(?:\.\d+)?)\s*(?:元/吨|万元/吨)', "成本"),
            (r'(\d+(?:\.\d+)?)\s*%', "百分比"),
            (r'(\d+(?:\.\d+)?)\s*(?:分钟|小时)', "时间"),
            (r'(\d+(?:\.\d+)?)\s*(?:吨/日|吨/年)', "产能")
        ]
        
        numerical_claims = []
        for pattern, label in numerical_patterns:
            matches = re.findall(pattern, report)
            for match in matches:
                numerical_claims.append({"value": float(match), "type": label})
        
        # 检查是否有待核实的数值
        pending_verification = report.count("[待核实]")
        if pending_verification > 0:
            issues.append(f"存在 {pending_verification} 个待核实数值")
            score -= min(30, pending_verification * 10)
        
        # 检查单位一致性
        if "吨" in report and "kg" in report:
            # 检查是否有单位换算说明
            if "换算" not in report and "转换" not in report:
                issues.append("存在混合单位，建议统一")
                score -= 10
        
        # 检查计算正确性（简化）
        calc_patterns = [
            r'(\d+(?:\.\d+)?)\s*[+×÷-]\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in calc_patterns:
            matches = re.findall(pattern, report)
            for match in matches:
                try:
                    # 简化验证
                    pass
                except Exception:
                    issues.append("发现计算错误")
                    score -= 10
        
        return CheckResult(
            check_name="数值准确性",
            passed=score >= 70,
            score=max(0, score),
            weight=0,
            issues=issues,
            details={
                "numerical_claims_count": len(numerical_claims),
                "pending_verification": pending_verification
            }
        )
    
    def _check_conflict_detection(self, report: str, materials: str, benchmarks: str) -> CheckResult:
        """检查冲突检测"""
        issues = []
        score = 100.0
        
        # 检查冲突标记
        conflict_patterns = [
            r'(?:存在?|有|发现).*?(?:冲突|矛盾|不一致|差异)',
            r'(?:对方|基准|标准).*?(?:高于|低于|不同于|不符合)',
            r'(?:冲突点|矛盾点|差异点)[：:]'
        ]
        
        conflicts_found = 0
        for pattern in conflict_patterns:
            matches = re.findall(pattern, report)
            conflicts_found += len(matches)
        
        # 如果完全没有冲突标记，可能遗漏了
        if conflicts_found == 0:
            issues.append("未发现冲突标记，可能存在遗漏")
            score -= 30
        
        # 检查是否有冲突分析
        if conflicts_found > 0:
            if "分析" not in report and "解释" not in report:
                issues.append("发现冲突但缺少分析说明")
                score -= 15
        
        return CheckResult(
            check_name="冲突检测",
            passed=score >= 70,
            score=max(0, score),
            weight=0,
            issues=issues,
            details={"conflicts_found": conflicts_found}
        )
    
    def _check_source_attribution(self, report: str, materials: str, benchmarks: str) -> CheckResult:
        """检查来源标注"""
        issues = []
        score = 100.0
        
        # 检查来源标注
        source_patterns = [
            r'(?:来源|出处|依据|根据|参考)[：:]',
            r'(?:根据|依据|参考).*?(?:标准|规范|文件|报告|数据)'
        ]
        
        sources_count = 0
        for pattern in source_patterns:
            sources_count += len(re.findall(pattern, report))
        
        # 检查数据点数量
        data_patterns = [
            r'\d+(?:\.\d+)?\s*(?:元|万元|%)',
            r'≥\s*\d+',
            r'≤\s*\d+',
            r'\d+(?:\.\d+)?\s*(?:°C|度|分钟|小时|吨)'
        ]
        
        data_points = 0
        for pattern in data_patterns:
            data_points += len(re.findall(pattern, report))
        
        # 计算标注率
        if data_points > 0:
            attribution_rate = sources_count / data_points
            if attribution_rate < 0.3:
                issues.append(f"来源标注率较低: {sources_count}/{data_points}")
                score -= 30
            elif attribution_rate < 0.5:
                issues.append(f"来源标注率一般: {sources_count}/{data_points}")
                score -= 15
        
        # 检查是否有标准引用
        standard_refs = re.findall(r'GB[/\\]T?\s*\d+|CJ[/\\]T\s*\d+', report)
        if not standard_refs and "标准" in report:
            issues.append("提及标准但未引用具体标准号")
            score -= 10
        
        return CheckResult(
            check_name="来源标注",
            passed=score >= 70,
            score=max(0, score),
            weight=0,
            issues=issues,
            details={
                "sources_count": sources_count,
                "data_points": data_points,
                "standard_refs": len(standard_refs)
            }
        )
    
    def _check_completeness(self, report: str, materials: str, benchmarks: str) -> CheckResult:
        """检查完整性"""
        issues = []
        score = 100.0
        
        # 检查必需章节
        required_sections = [
            ("执行摘要", r'(?:执行摘要|摘要|概述)'),
            ("交流背景", r'(?:交流背景|背景|会议信息)'),
            ("对方技术主张", r'(?:对方技术主张|技术主张|技术介绍)'),
            ("初步结论", r'(?:初步结论|结论|总结|建议)')
        ]
        
        missing_sections = []
        for section_name, pattern in required_sections:
            if not re.search(pattern, report):
                missing_sections.append(section_name)
                score -= 20
        
        if missing_sections:
            issues.append(f"缺少必需章节: {', '.join(missing_sections)}")
        
        # 检查关键要素
        key_elements = [
            ("技术原理", r'(?:技术原理|工艺路线|技术路线)'),
            ("关键参数", r'(?:关键参数|技术参数|技术指标)'),
            ("风险", r'(?:风险|问题|挑战)'),
            ("建议", r'(?:建议|推荐|下一步)')
        ]
        
        missing_elements = []
        for element_name, pattern in key_elements:
            if not re.search(pattern, report):
                missing_elements.append(element_name)
                score -= 10
        
        if missing_elements:
            issues.append(f"缺少关键要素: {', '.join(missing_elements)}")
        
        # 检查报告长度
        if len(report) < 500:
            issues.append("报告内容过短")
            score -= 20
        
        return CheckResult(
            check_name="完整性",
            passed=score >= 70,
            score=max(0, score),
            weight=0,
            issues=issues,
            details={
                "missing_sections": missing_sections,
                "missing_elements": missing_elements,
                "report_length": len(report)
            }
        )
    
    def _calculate_grade(self, score: float) -> QualityGrade:
        """计算等级"""
        if score >= 90:
            return QualityGrade.A
        elif score >= 80:
            return QualityGrade.B
        elif score >= 70:
            return QualityGrade.C
        elif score >= 60:
            return QualityGrade.D
        else:
            return QualityGrade.F
    
    def _generate_summary(self, checks: Dict[str, CheckResult], 
                         total_score: float, grade: QualityGrade) -> str:
        """生成总结"""
        passed_checks = sum(1 for c in checks.values() if c.passed)
        total_checks = len(checks)
        
        summary = f"报告质量评分: {total_score:.1f}分 (等级: {grade.value})\n"
        summary += f"通过检查: {passed_checks}/{total_checks}\n"
        
        # 列出主要问题
        all_issues = []
        for check in checks.values():
            all_issues.extend(check.issues)
        
        if all_issues:
            summary += f"发现问题: {len(all_issues)}个\n"
        
        return summary
    
    def _generate_recommendations(self, checks: Dict[str, CheckResult]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        for check_name, check in checks.items():
            if not check.passed:
                if check_name == "fact_judgment_separation":
                    recommendations.append("建议: 明确区分对方主张和我方分析判断，为对方主张添加来源标注")
                elif check_name == "numerical_accuracy":
                    recommendations.append("建议: 核实所有数值声明，统一单位，标注待核实数据")
                elif check_name == "conflict_detection":
                    recommendations.append("建议: 检查并标注对方主张与行业基准之间的差异和冲突")
                elif check_name == "source_attribution":
                    recommendations.append("建议: 为关键数据添加来源标注，引用具体标准编号")
                elif check_name == "completeness":
                    recommendations.append("建议: 补充缺失章节，确保报告结构完整")
        
        return recommendations
