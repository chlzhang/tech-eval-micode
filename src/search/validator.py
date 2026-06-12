"""
搜索质量验证器

提供搜索结果质量评估和验证：
1. 结果相关性检查
2. 时效性验证
3. 来源可信度评估
4. 数据完整性检查
"""

import re
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class SourceType(Enum):
    """来源类型"""
    STANDARD = "standard"           # 国家标准
    INTERNATIONAL = "international" # 国际标准
    INDUSTRY = "industry"          # 行业报告
    ACADEMIC = "academic"          # 学术论文
    NEWS = "news"                  # 新闻
    UNKNOWN = "unknown"            # 未知


class ConfidenceLevel(Enum):
    """置信度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    content: str
    url: str = ""
    source_type: SourceType = SourceType.UNKNOWN
    publish_date: Optional[str] = None
    relevance_score: float = 0.0
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    score: float
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class SearchQueryValidator:
    """搜索查询验证器"""
    
    def __init__(self):
        self.required_keywords = {
            "标准": ["GB", "标准", "条款", "规范"],
            "经济": ["元/吨", "万元", "投资", "成本", "收益"],
            "技术": ["参数", "指标", "温度", "压力", "效率"],
            "风险": ["风险", "事故", "问题", "缺陷"]
        }
    
    def validate_query(self, query: str, category: str = None) -> ValidationResult:
        """验证搜索查询质量"""
        issues = []
        suggestions = []
        score = 100.0
        
        # 检查查询长度
        if len(query) < 5:
            issues.append("查询过短，可能影响搜索精度")
            score -= 20
        
        # 检查是否包含技术路线关键词
        if not self._has_tech_route_keyword(query):
            suggestions.append("建议添加具体技术路线关键词")
            score -= 10
        
        # 检查类别相关关键词
        if category and category in self.required_keywords:
            keywords = self.required_keywords[category]
            if not any(kw in query for kw in keywords):
                suggestions.append(f"建议包含{category}相关关键词: {', '.join(keywords[:3])}")
                score -= 15
        
        return ValidationResult(
            is_valid=score >= 60,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )
    
    def _has_tech_route_keyword(self, query: str) -> bool:
        """检查是否包含技术路线关键词"""
        tech_keywords = [
            "饲料化", "厌氧", "好氧", "堆肥", "焚烧",
            "热解", "气化", "发酵", "消毒", "干燥"
        ]
        return any(kw in query for kw in tech_keywords)


class SearchResultValidator:
    """搜索结果验证器"""
    
    def __init__(self):
        self.source_type_patterns = {
            SourceType.STANDARD: [
                r"GB[/\\]T?\s*\d+",
                r"国家标准",
                r"行业标准"
            ],
            SourceType.INTERNATIONAL: [
                r"ISO\s*\d+",
                r"EFSA",
                r"OIE",
                r"WHO",
                r"FAO"
            ],
            SourceType.INDUSTRY: [
                r"行业报告",
                r"市场研究",
                r"上市公司年报"
            ],
            SourceType.ACADEMIC: [
                r"论文",
                r"期刊",
                r"研究",
                r"学报"
            ]
        }
    
    def validate_result(self, result: SearchResult, query: str) -> ValidationResult:
        """验证单个搜索结果"""
        issues = []
        suggestions = []
        score = 100.0
        
        # 检查相关性
        relevance = self._calculate_relevance(result, query)
        if relevance < 0.3:
            issues.append(f"相关性较低: {relevance:.2f}")
            score -= 30
        elif relevance < 0.5:
            suggestions.append("相关性一般，建议优化搜索词")
            score -= 15
        
        # 检查时效性
        if result.publish_date:
            recency = self._check_recency(result.publish_date)
            if recency < 0.5:
                issues.append("数据较旧，建议寻找更新来源")
                score -= 20
        
        # 检查来源类型
        source_type = self._detect_source_type(result)
        if source_type == SourceType.UNKNOWN:
            suggestions.append("来源类型未知，建议核实")
            score -= 10
        
        # 检查内容完整性
        if len(result.content) < 50:
            issues.append("内容过短，信息可能不完整")
            score -= 15
        
        return ValidationResult(
            is_valid=score >= 60,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )
    
    def _calculate_relevance(self, result: SearchResult, query: str) -> float:
        """计算相关性分数"""
        query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', query.lower()))
        content_words = set(re.findall(r'[\w\u4e00-\u9fff]+', result.content.lower()))
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words & content_words)
        return overlap / len(query_words)
    
    def _check_recency(self, date_str: str) -> float:
        """检查时效性"""
        try:
            # 尝试解析日期
            for fmt in ["%Y-%m-%d", "%Y年%m月%d日", "%Y/%m/%d"]:
                try:
                    publish_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                return 0.5  # 无法解析日期
            
            # 计算时间差
            days_diff = (datetime.now() - publish_date).days
            
            # 2年内为满分
            if days_diff <= 365 * 2:
                return 1.0
            elif days_diff <= 365 * 5:
                return 0.7
            else:
                return 0.3
                
        except Exception:
            return 0.5
    
    def _detect_source_type(self, result: SearchResult) -> SourceType:
        """检测来源类型"""
        content = f"{result.title} {result.content}"
        
        for source_type, patterns in self.source_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return source_type
        
        return SourceType.UNKNOWN
    
    def calculate_confidence(self, result: SearchResult, validation: ValidationResult) -> ConfidenceLevel:
        """计算置信度"""
        if validation.score >= 80:
            return ConfidenceLevel.HIGH
        elif validation.score >= 60:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW


class BenchmarkSearchOptimizer:
    """行业基准搜索优化器"""
    
    def __init__(self):
        self.query_validator = SearchQueryValidator()
        self.result_validator = SearchResultValidator()
    
    def optimize_queries(self, base_queries: List[str], tech_route: str) -> List[str]:
        """优化搜索查询"""
        optimized = []
        
        for query in base_queries:
            # 添加技术路线关键词
            if tech_route not in query:
                query = f"{tech_route} {query}"
            
            # 验证查询质量
            validation = self.query_validator.validate_query(query)
            if validation.is_valid:
                optimized.append(query)
            else:
                # 尝试修复
                fixed_query = self._fix_query(query, validation.issues)
                optimized.append(fixed_query)
        
        return optimized
    
    def _fix_query(self, query: str, issues: List[str]) -> str:
        """修复查询"""
        # 简化实现
        return query
    
    def filter_results(self, results: List[SearchResult], 
                      min_score: float = 60.0) -> List[SearchResult]:
        """过滤搜索结果"""
        filtered = []
        
        for result in results:
            # 使用空查询进行基本验证
            validation = self.result_validator.validate_result(result, "")
            
            if validation.score >= min_score:
                filtered.append(result)
        
        # 按相关性排序
        filtered.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return filtered
    
    def deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重"""
        seen_urls = set()
        seen_contents = set()
        unique = []
        
        for result in results:
            # 基于 URL 去重
            if result.url and result.url in seen_urls:
                continue
            
            # 基于内容去重
            content_hash = hash(result.content[:200])
            if content_hash in seen_contents:
                continue
            
            if result.url:
                seen_urls.add(result.url)
            seen_contents.add(content_hash)
            unique.append(result)
        
        return unique
    
    def generate_search_report(self, queries: List[str], 
                              results: Dict[str, List[SearchResult]]) -> Dict[str, Any]:
        """生成搜索质量报告"""
        report = {
            "total_queries": len(queries),
            "total_results": 0,
            "average_score": 0,
            "source_distribution": {},
            "issues": [],
            "suggestions": []
        }
        
        all_scores = []
        source_counts = {}
        
        for query, query_results in results.items():
            report["total_results"] += len(query_results)
            
            for result in query_results:
                validation = self.result_validator.validate_result(result, query)
                all_scores.append(validation.score)
                
                source_type = self.result_validator._detect_source_type(result)
                source_counts[source_type.value] = source_counts.get(source_type.value, 0) + 1
        
        if all_scores:
            report["average_score"] = sum(all_scores) / len(all_scores)
        
        report["source_distribution"] = source_counts
        
        return report
