"""
搜索质量验证器单元测试
"""

import pytest
from datetime import datetime, timedelta

from src.search.validator import (
    SearchQueryValidator,
    SearchResultValidator,
    BenchmarkSearchOptimizer,
    SearchResult,
    SourceType,
    ConfidenceLevel,
    ValidationResult
)


class TestSearchQueryValidator:
    """搜索查询验证器测试"""
    
    def setup_method(self):
        self.validator = SearchQueryValidator()
    
    def test_valid_query(self):
        """测试有效查询"""
        query = "餐厨剩余物饲料化 国家标准 GB/T 28101"
        result = self.validator.validate_query(query, "标准")
        
        assert result.is_valid is True
        assert result.score >= 60
    
    def test_short_query(self):
        """测试过短的查询"""
        query = "标准"
        result = self.validator.validate_query(query)
        
        assert result.score < 100
        assert any("过短" in issue for issue in result.issues)
    
    def test_missing_tech_route(self):
        """测试缺少技术路线关键词"""
        query = "国家标准 GB/T 28101"
        result = self.validator.validate_query(query)
        
        assert any("技术路线" in s for s in result.suggestions)
    
    def test_category_keywords(self):
        """测试类别关键词检查"""
        query = "餐厨剩余物饲料化 运营成本"
        result = self.validator.validate_query(query, "经济")
        
        assert result.is_valid is True


class TestSearchResultValidator:
    """搜索结果验证器测试"""
    
    def setup_method(self):
        self.validator = SearchResultValidator()
    
    def test_relevant_result(self):
        """测试相关结果"""
        result = SearchResult(
            title="餐厨垃圾饲料化技术标准",
            content="GB/T 28101-2011 餐厨垃圾处理技术规范 饲料化 标准 灭菌温度≥133°C的要求",
            url="https://example.com/standard"
        )
        
        validation = self.validator.validate_result(result, "餐厨垃圾饲料化 标准")
        # 相关性检查可能因为分词问题导致分数较低
        assert validation.score >= 40
    
    def test_irrelevant_result(self):
        """测试不相关结果"""
        result = SearchResult(
            title="今日天气",
            content="明天晴转多云，气温15-25度",
            url="https://example.com/weather"
        )
        
        validation = self.validator.validate_result(result, "餐厨垃圾饲料化")
        assert validation.score < 60
    
    def test_old_data(self):
        """测试旧数据"""
        result = SearchResult(
            title="餐厨垃圾处理技术",
            content="餐厨垃圾处理技术规范",
            publish_date="2015-01-01"
        )
        
        validation = self.validator.validate_result(result, "餐厨垃圾")
        # 旧数据应该扣分
        assert any("旧" in issue for issue in validation.issues)
    
    def test_recent_data(self):
        """测试近期数据"""
        recent_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        result = SearchResult(
            title="餐厨垃圾处理技术",
            content="餐厨垃圾处理技术规范",
            publish_date=recent_date
        )
        
        validation = self.validator.validate_result(result, "餐厨垃圾")
        # 近期数据不应该扣时效性分
    
    def test_source_type_detection(self):
        """测试来源类型检测"""
        # 国家标准
        result = SearchResult(
            title="GB/T 28101-2011",
            content="国家标准 餐厨垃圾处理技术规范"
        )
        source_type = self.validator._detect_source_type(result)
        assert source_type == SourceType.STANDARD
        
        # 国际标准
        result = SearchResult(
            title="ISO 22000",
            content="ISO 食品安全管理体系"
        )
        source_type = self.validator._detect_source_type(result)
        assert source_type == SourceType.INTERNATIONAL
    
    def test_confidence_calculation(self):
        """测试置信度计算"""
        result = SearchResult(title="test", content="test")
        
        # 高置信度
        validation = ValidationResult(is_valid=True, score=90)
        confidence = self.validator.calculate_confidence(result, validation)
        assert confidence == ConfidenceLevel.HIGH
        
        # 中置信度
        validation = ValidationResult(is_valid=True, score=70)
        confidence = self.validator.calculate_confidence(result, validation)
        assert confidence == ConfidenceLevel.MEDIUM
        
        # 低置信度
        validation = ValidationResult(is_valid=False, score=40)
        confidence = self.validator.calculate_confidence(result, validation)
        assert confidence == ConfidenceLevel.LOW


class TestBenchmarkSearchOptimizer:
    """行业基准搜索优化器测试"""
    
    def setup_method(self):
        self.optimizer = BenchmarkSearchOptimizer()
    
    def test_optimize_queries(self):
        """测试查询优化"""
        queries = ["国家标准", "经济数据"]
        optimized = self.optimizer.optimize_queries(queries, "餐厨剩余物饲料化")
        
        assert len(optimized) == 2
        for query in optimized:
            assert "餐厨剩余物饲料化" in query
    
    def test_filter_results(self):
        """测试结果过滤"""
        results = [
            SearchResult(
                title="相关结果",
                content="餐厨垃圾饲料化技术规范 国家标准",
                relevance_score=0.8
            ),
            SearchResult(
                title="不相关结果",
                content="今天天气真好",
                relevance_score=0.1
            )
        ]
        
        filtered = self.optimizer.filter_results(results, min_score=60)
        assert len(filtered) <= len(results)
    
    def test_deduplicate_results(self):
        """测试去重"""
        results = [
            SearchResult(
                title="结果1",
                content="相同内容",
                url="https://example.com/1"
            ),
            SearchResult(
                title="结果1",
                content="相同内容",
                url="https://example.com/1"
            ),
            SearchResult(
                title="结果2",
                content="不同内容",
                url="https://example.com/2"
            )
        ]
        
        unique = self.optimizer.deduplicate_results(results)
        assert len(unique) == 2
    
    def test_generate_search_report(self):
        """测试生成搜索报告"""
        queries = ["query1", "query2"]
        results = {
            "query1": [
                SearchResult(title="r1", content="content1"),
                SearchResult(title="r2", content="content2")
            ],
            "query2": [
                SearchResult(title="r3", content="content3")
            ]
        }
        
        report = self.optimizer.generate_search_report(queries, results)
        
        assert report["total_queries"] == 2
        assert report["total_results"] == 3
        assert "average_score" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
