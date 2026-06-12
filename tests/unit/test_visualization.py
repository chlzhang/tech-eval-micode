"""
数据可视化模块测试
"""

import pytest
import json

from src.visualization import (
    ChartType,
    ChartDataset,
    ChartConfig,
    ChartGenerator,
    HTMLReportRenderer
)


class TestChartGenerator:
    """图表生成器测试"""
    
    def setup_method(self):
        self.generator = ChartGenerator()
    
    def test_create_bar_chart(self):
        """测试创建柱状图"""
        chart = self.generator.create_bar_chart(
            title="测试柱状图",
            labels=["A", "B", "C"],
            datasets=[{"label": "数据", "data": [10, 20, 30]}]
        )
        
        assert chart["type"] == "bar"
        assert chart["title"] == "测试柱状图"
        assert len(chart["data"]["labels"]) == 3
    
    def test_create_grouped_bar_chart(self):
        """测试创建分组柱状图"""
        chart = self.generator.create_grouped_bar_chart(
            title="分组柱状图",
            labels=["Q1", "Q2", "Q3", "Q4"],
            datasets=[
                {"label": "2023", "data": [10, 20, 30, 40]},
                {"label": "2024", "data": [15, 25, 35, 45]}
            ]
        )
        
        assert chart["type"] == "bar"
        assert len(chart["data"]["datasets"]) == 2
    
    def test_create_line_chart(self):
        """测试创建折线图"""
        chart = self.generator.create_line_chart(
            title="趋势图",
            labels=["1月", "2月", "3月"],
            datasets=[{"label": "销售额", "data": [100, 150, 200]}]
        )
        
        assert chart["type"] == "line"
    
    def test_create_pie_chart(self):
        """测试创建饼图"""
        chart = self.generator.create_pie_chart(
            title="占比图",
            labels=["A", "B", "C"],
            data=[30, 40, 30]
        )
        
        assert chart["type"] == "pie"
        assert len(chart["data"]["datasets"][0]["data"]) == 3
    
    def test_create_doughnut_chart(self):
        """测试创建环形图"""
        chart = self.generator.create_doughnut_chart(
            title="环形图",
            labels=["X", "Y"],
            data=[60, 40]
        )
        
        assert chart["type"] == "doughnut"
        assert chart["options"]["cutout"] == "60%"
    
    def test_create_radar_chart(self):
        """测试创建雷达图"""
        chart = self.generator.create_radar_chart(
            title="能力评估",
            labels=["技术", "管理", "沟通", "创新"],
            datasets=[{"label": "得分", "data": [80, 70, 90, 60]}]
        )
        
        assert chart["type"] == "radar"
    
    def test_create_gauge_chart(self):
        """测试创建仪表盘"""
        chart = self.generator.create_gauge_chart(
            title="完成度",
            value=75
        )
        
        assert chart["type"] == "gauge"
        assert chart["value"] == 75
    
    def test_create_timeline(self):
        """测试创建时间线"""
        milestones = [
            {"time": "T+0", "label": "启动"},
            {"time": "T+3月", "label": "完成"},
            {"time": "T+6月", "label": "验收"}
        ]
        chart = self.generator.create_timeline(
            title="项目时间线",
            milestones=milestones
        )
        
        assert chart["type"] == "timeline"
        assert len(chart["milestones"]) == 3
    
    def test_create_comparison_table(self):
        """测试创建对比表格"""
        chart = self.generator.create_comparison_table(
            title="参数对比",
            headers=["指标", "对方", "基准"],
            rows=[
                ["温度", "135°C", "133°C"],
                ["时间", "30分钟", "30分钟"]
            ]
        )
        
        assert chart["type"] == "table"
        assert len(chart["rows"]) == 2
    
    def test_generate_colors(self):
        """测试生成颜色"""
        colors = self.generator.generate_colors(5, "primary")
        assert len(colors) == 5
        
        colors2 = self.generator.generate_colors(10, "warm")
        assert len(colors2) == 10


class TestHTMLReportRenderer:
    """HTML 报告渲染器测试"""
    
    def setup_method(self):
        self.renderer = HTMLReportRenderer()
    
    def test_render_basic_report(self):
        """测试渲染基础报告"""
        sections = [
            {"title": "第一章", "content": "<p>内容1</p>"},
            {"title": "第二章", "content": "<p>内容2</p>"}
        ]
        
        html = self.renderer.render("测试报告", sections)
        
        assert "<!DOCTYPE html>" in html
        assert "测试报告" in html
        assert "第一章" in html
        assert "第二章" in html
    
    def test_render_with_charts(self):
        """测试渲染带图表的报告"""
        sections = [
            {"title": "概览", "content": "<p>图表展示</p>"}
        ]
        
        charts = [
            {
                "type": "bar",
                "title": "柱状图",
                "data": {
                    "labels": ["A", "B", "C"],
                    "datasets": [{"label": "数据", "data": [10, 20, 30]}]
                }
            }
        ]
        
        html = self.renderer.render("图表报告", sections, charts)
        
        assert "chart-container" in html
        assert "canvas id=\"chart-0\"" in html
    
    def test_render_with_gauge(self):
        """测试渲染仪表盘"""
        sections = [{"title": "指标", "content": ""}]
        
        charts = [
            {
                "type": "gauge",
                "title": "完成度",
                "value": 85,
                "color": "#28A745"
            }
        ]
        
        html = self.renderer.render("仪表盘报告", sections, charts)
        
        assert "gauge" in html
        assert "85%" in html
    
    def test_render_with_timeline(self):
        """测试渲染时间线"""
        sections = [{"title": "计划", "content": ""}]
        
        charts = [
            {
                "type": "timeline",
                "title": "项目时间线",
                "milestones": [
                    {"time": "第1月", "label": "启动"},
                    {"time": "第6月", "label": "完成"}
                ]
            }
        ]
        
        html = self.renderer.render("时间线报告", sections, charts)
        
        assert "timeline" in html
        assert "第1月" in html
    
    def test_render_with_table(self):
        """测试渲染表格"""
        sections = [{"title": "对比", "content": ""}]
        
        charts = [
            {
                "type": "table",
                "title": "参数对比",
                "headers": ["指标", "值"],
                "rows": [["温度", "135°C"], ["时间", "30分钟"]]
            }
        ]
        
        html = self.renderer.render("表格报告", sections, charts)
        
        assert "<table>" in html
        assert "135°C" in html
    
    def test_render_full_report(self):
        """测试渲染完整报告"""
        sections = [
            {
                "title": "执行摘要",
                "content": """
                    <p>本技术具有可行性。</p>
                    <table>
                        <tr><th>指标</th><th>值</th></tr>
                        <tr><td>温度</td><td>135°C</td></tr>
                    </table>
                """
            },
            {
                "title": "技术分析",
                "content": "<p>技术原理可行。</p>"
            }
        ]
        
        charts = [
            {
                "type": "bar",
                "title": "参数对比",
                "data": {
                    "labels": ["温度", "时间", "产率"],
                    "datasets": [
                        {"label": "对方", "data": [135, 30, 25]},
                        {"label": "基准", "data": [133, 30, 20]}
                    ]
                }
            },
            {
                "type": "timeline",
                "title": "决策时间线",
                "milestones": [
                    {"time": "T+0", "label": "启动试点"},
                    {"time": "T+3月", "label": "完成验证"}
                ]
            }
        ]
        
        html = self.renderer.render("完整报告", sections, charts)
        
        # 验证结构
        assert "<!DOCTYPE html>" in html
        assert "完整报告" in html
        assert "目录" in html
        
        # 验证章节
        assert "执行摘要" in html
        assert "技术分析" in html
        
        # 验证图表
        assert "chart-0" in html
        assert "timeline" in html
        
        # 验证交互功能
        assert "smooth" in html  # 平滑滚动
        assert "details" in html  # 折叠功能


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
