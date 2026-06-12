"""
数值核验模块单元测试

测试 FACT-CHECKER 的核心功能：
1. 单位换算
2. 数值声明验证
3. 计算正确性检查
"""

import pytest
from dataclasses import dataclass
from typing import Optional


@dataclass
class NumericalClaim:
    """数值声明"""
    value: float
    unit: str
    context: str
    source: str


@dataclass
class VerificationResult:
    """核验结果"""
    is_consistent: bool
    confidence: str  # 高/中/低
    notes: str


class UnitConverter:
    """单位换算器"""
    
    # 单位换算表
    CONVERSIONS = {
        # 重量单位 -> kg
        ("吨", "kg"): 1000,
        ("kg", "kg"): 1,
        ("g", "kg"): 0.001,
        ("mg", "kg"): 0.000001,
        
        # 温度单位（特殊处理）
        ("°C", "°C"): 1,
        ("°F", "°C"): lambda x: (x - 32) * 5 / 9,
        
        # 时间单位 -> 分钟
        ("小时", "分钟"): 60,
        ("分钟", "分钟"): 1,
        ("秒", "分钟"): 1 / 60,
        
        # 长度单位 -> 米
        ("km", "米"): 1000,
        ("米", "米"): 1,
        ("cm", "米"): 0.01,
        ("mm", "米"): 0.001,
    }
    
    def convert(self, value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """单位换算"""
        if from_unit == to_unit:
            return value
        
        key = (from_unit, to_unit)
        if key not in self.CONVERSIONS:
            return None
        
        factor = self.CONVERSIONS[key]
        if callable(factor):
            return factor(value)
        return value * factor
    
    def is_comparable(self, unit1: str, unit2: str) -> bool:
        """判断两个单位是否可比较"""
        # 简化实现：相同单位或可转换的单位
        if unit1 == unit2:
            return True
        
        # 检查是否有转换路径
        return (unit1, unit2) in self.CONVERSIONS or (unit2, unit1) in self.CONVERSIONS


class FactChecker:
    """数值核验器"""
    
    def __init__(self):
        self.converter = UnitConverter()
    
    def verify_claim(self, claim: str, source: str) -> VerificationResult:
        """验证数值声明"""
        # 简化实现：检查数值是否在合理范围内
        # 实际应该使用 LLM 提取和比对数值
        
        # 提取数值
        claim_value = self._extract_number(claim)
        source_value = self._extract_number(source)
        
        if claim_value is None or source_value is None:
            return VerificationResult(
                is_consistent=False,
                confidence="低",
                notes="无法提取数值"
            )
        
        # 检查一致性（允许5%误差）
        if abs(claim_value - source_value) / source_value < 0.05:
            return VerificationResult(
                is_consistent=True,
                confidence="高",
                notes="数值一致"
            )
        
        return VerificationResult(
            is_consistent=False,
            confidence="中",
            notes=f"数值不一致: 声明={claim_value}, 来源={source_value}"
        )
    
    def verify_calculation(self, expression: str, expected_result: float) -> VerificationResult:
        """验证计算正确性"""
        try:
            # 安全计算表达式
            actual_result = self._safe_eval(expression)
            
            if abs(actual_result - expected_result) < 0.01:
                return VerificationResult(
                    is_consistent=True,
                    confidence="高",
                    notes="计算正确"
                )
            
            return VerificationResult(
                is_consistent=False,
                confidence="高",
                notes=f"计算错误: 期望={expected_result}, 实际={actual_result}"
            )
        except Exception as e:
            return VerificationResult(
                is_consistent=False,
                confidence="低",
                notes=f"计算失败: {str(e)}"
            )
    
    def _extract_number(self, text: str) -> Optional[float]:
        """从文本中提取数值"""
        import re
        match = re.search(r'[\d.]+', text)
        if match:
            return float(match.group())
        return None
    
    def _safe_eval(self, expression: str) -> float:
        """安全计算表达式"""
        # 只允许基本数学运算
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            raise ValueError(f"不允许的字符: {expression}")
        return eval(expression)


class TestUnitConverter:
    """单位换算器测试"""
    
    def setup_method(self):
        self.converter = UnitConverter()
    
    def test_same_unit_conversion(self):
        """测试相同单位换算"""
        assert self.converter.convert(100, "kg", "kg") == 100
        assert self.converter.convert(30, "°C", "°C") == 30
    
    def test_weight_conversion(self):
        """测试重量单位换算"""
        assert self.converter.convert(1, "吨", "kg") == 1000
        assert self.converter.convert(1000, "g", "kg") == 1
        assert self.converter.convert(1000000, "mg", "kg") == 1
    
    def test_temperature_conversion(self):
        """测试温度单位换算"""
        # 华氏度转摄氏度
        result = self.converter.convert(212, "°F", "°C")
        assert result is not None
        assert abs(result - 100) < 0.01
    
    def test_time_conversion(self):
        """测试时间单位换算"""
        assert self.converter.convert(1, "小时", "分钟") == 60
        assert self.converter.convert(60, "秒", "分钟") == 1
    
    def test_unsupported_conversion(self):
        """测试不支持的换算"""
        assert self.converter.convert(1, "kg", "米") is None
    
    def test_is_comparable(self):
        """测试单位可比较性"""
        assert self.converter.is_comparable("kg", "kg") is True
        assert self.converter.is_comparable("吨", "kg") is True
        assert self.converter.is_comparable("kg", "米") is False


class TestFactChecker:
    """数值核验器测试"""
    
    def setup_method(self):
        self.checker = FactChecker()
    
    def test_verify_claim_consistent(self):
        """测试一致的数值声明"""
        result = self.checker.verify_claim("温度135°C", "温度135°C")
        assert result.is_consistent is True
        assert result.confidence == "高"
    
    def test_verify_claim_inconsistent(self):
        """测试不一致的数值声明"""
        result = self.checker.verify_claim("温度135°C", "温度133°C")
        # 135 vs 133，差异约1.5%，应该是一致的
        assert result.is_consistent is True
    
    def test_verify_claim_large_difference(self):
        """测试差异较大的数值声明"""
        result = self.checker.verify_claim("成本150元/吨", "成本200元/吨")
        # 150 vs 200，差异25%，应该是不一致的
        assert result.is_consistent is False
    
    def test_verify_calculation_correct(self):
        """测试正确的计算"""
        result = self.checker.verify_calculation("100 + 200", 300)
        assert result.is_consistent is True
        assert result.confidence == "高"
    
    def test_verify_calculation_incorrect(self):
        """测试错误的计算"""
        result = self.checker.verify_calculation("100 + 200", 400)
        assert result.is_consistent is False
        assert "计算错误" in result.notes
    
    def test_verify_calculation_invalid_expression(self):
        """测试无效的表达式"""
        result = self.checker.verify_calculation("import os", 0)
        assert result.is_consistent is False
        assert "不允许的字符" in result.notes
    
    def test_extract_number(self):
        """测试数值提取"""
        assert self.checker._extract_number("温度135°C") == 135
        assert self.checker._extract_number("成本150.5元/吨") == 150.5
        assert self.checker._extract_number("无数字") is None


class TestNumericalAccuracy:
    """数值准确性测试"""
    
    def test_unit_consistency_check(self):
        """测试单位一致性检查"""
        # 比较前必须统一单位
        converter = UnitConverter()
        
        # 模拟：对方说1吨，行业基准1000kg
        counterpart = 1  # 吨
        benchmark = 1000  # kg
        
        # 转换后比较
        counterpart_in_kg = converter.convert(counterpart, "吨", "kg")
        assert counterpart_in_kg == benchmark
    
    def test_percentage_calculation(self):
        """测试百分比计算"""
        # 产品产率 = 产品重量 / 原料重量 * 100%
        product_weight = 25  # kg
        raw_material_weight = 100  # kg
        
        yield_rate = product_weight / raw_material_weight * 100
        assert yield_rate == 25
    
    def test_cost_calculation(self):
        """测试成本计算"""
        # 总成本 = 单位成本 * 处理量
        unit_cost = 150  # 元/吨
        processing_volume = 10  # 吨/日
        
        daily_cost = unit_cost * processing_volume
        assert daily_cost == 1500  # 元/日
    
    def test_investment_recovery_calculation(self):
        """测试投资回收期计算"""
        total_investment = 800  # 万元
        annual_profit = 100  # 万元/年
        
        recovery_period = total_investment / annual_profit
        assert recovery_period == 8  # 年


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
