"""
数据可视化模块

提供丰富的图表类型和 HTML 渲染：
1. 图表类型：柱状图、折线图、饼图、雷达图、仪表盘、时间线
2. HTML 渲染：单文件报告，内嵌 Chart.js
3. 交互功能：折叠、筛选、动画
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class ChartType(Enum):
    """图表类型"""
    BAR = "bar"                    # 柱状图
    BAR_GROUPED = "bar_grouped"    # 分组柱状图
    BAR_STACKED = "bar_stacked"    # 堆叠柱状图
    LINE = "line"                  # 折线图
    PIE = "pie"                    # 饼图
    DOUGHNUT = "doughnut"          # 环形图
    RADAR = "radar"                # 雷达图
    GAUGE = "gauge"                # 仪表盘
    TIMELINE = "timeline"          # 时间线
    HEATMAP = "heatmap"            # 热力图
    SCATTER = "scatter"            # 散点图


@dataclass
class ChartDataset:
    """图表数据集"""
    label: str
    data: List[float]
    backgroundColor: str = None
    borderColor: str = None
    borderWidth: int = 1


@dataclass
class ChartConfig:
    """图表配置"""
    title: str
    chart_type: ChartType
    labels: List[str] = field(default_factory=list)
    datasets: List[ChartDataset] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    width: str = "100%"
    height: str = "400px"


class ChartGenerator:
    """图表生成器"""
    
    # 预定义颜色方案
    COLORS = {
        "primary": ["#4A90D9", "#67B7DC", "#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072", "#80B1D3"],
        "warm": ["#FF6B6B", "#FFA07A", "#FFD700", "#FF8C00", "#FF4500", "#DC143C"],
        "cool": ["#4169E1", "#00CED1", "#20B2AA", "#48D1CC", "#40E0D0", "#7FFFD4"],
        "business": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B", "#44BBA4"],
        "risk": ["#28A745", "#FFC107", "#FD7E14", "#DC3545", "#6C757D"]
    }
    
    def __init__(self):
        self.charts: List[Dict[str, Any]] = []
    
    def create_bar_chart(self, title: str, labels: List[str], datasets: List[Dict], 
                         options: Dict = None) -> Dict[str, Any]:
        """创建柱状图"""
        return {
            "type": "bar",
            "title": title,
            "data": {
                "labels": labels,
                "datasets": datasets
            },
            "options": options or {}
        }
    
    def create_grouped_bar_chart(self, title: str, labels: List[str], 
                                  datasets: List[Dict]) -> Dict[str, Any]:
        """创建分组柱状图"""
        return {
            "type": "bar",
            "title": title,
            "data": {
                "labels": labels,
                "datasets": datasets
            },
            "options": {
                "scales": {
                    "x": {"stacked": False},
                    "y": {"stacked": False}
                }
            }
        }
    
    def create_stacked_bar_chart(self, title: str, labels: List[str], 
                                  datasets: List[Dict]) -> Dict[str, Any]:
        """创建堆叠柱状图"""
        return {
            "type": "bar",
            "title": title,
            "data": {
                "labels": labels,
                "datasets": datasets
            },
            "options": {
                "scales": {
                    "x": {"stacked": True},
                    "y": {"stacked": True}
                }
            }
        }
    
    def create_line_chart(self, title: str, labels: List[str], datasets: List[Dict]) -> Dict[str, Any]:
        """创建折线图"""
        return {
            "type": "line",
            "title": title,
            "data": {
                "labels": labels,
                "datasets": datasets
            },
            "options": {
                "tension": 0.1
            }
        }
    
    def create_pie_chart(self, title: str, labels: List[str], data: List[float]) -> Dict[str, Any]:
        """创建饼图"""
        return {
            "type": "pie",
            "title": title,
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": data,
                    "backgroundColor": self.COLORS["primary"][:len(data)]
                }]
            },
            "options": {}
        }
    
    def create_doughnut_chart(self, title: str, labels: List[str], data: List[float]) -> Dict[str, Any]:
        """创建环形图"""
        return {
            "type": "doughnut",
            "title": title,
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": data,
                    "backgroundColor": self.COLORS["primary"][:len(data)]
                }]
            },
            "options": {
                "cutout": "60%"
            }
        }
    
    def create_radar_chart(self, title: str, labels: List[str], datasets: List[Dict]) -> Dict[str, Any]:
        """创建雷达图"""
        return {
            "type": "radar",
            "title": title,
            "data": {
                "labels": labels,
                "datasets": datasets
            },
            "options": {
                "scales": {
                    "r": {
                        "beginAtZero": True
                    }
                }
            }
        }
    
    def create_gauge_chart(self, title: str, value: float, max_value: float = 100,
                           thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        """创建仪表盘"""
        if thresholds is None:
            thresholds = {"danger": 30, "warning": 70, "success": 100}
        
        # 确定颜色
        color = "#DC3545"  # 红色
        if value >= thresholds.get("success", 100) * 0.7:
            color = "#28A745"  # 绿色
        elif value >= thresholds.get("warning", 70) * 0.7:
            color = "#FFC107"  # 黄色
        
        return {
            "type": "gauge",
            "title": title,
            "value": value,
            "max_value": max_value,
            "color": color,
            "options": {
                "thresholds": thresholds
            }
        }
    
    def create_timeline(self, title: str, milestones: List[Dict]) -> Dict[str, Any]:
        """创建时间线"""
        return {
            "type": "timeline",
            "title": title,
            "milestones": milestones
        }
    
    def create_comparison_table(self, title: str, headers: List[str], rows: List[List[str]]) -> Dict[str, Any]:
        """创建对比表格"""
        return {
            "type": "table",
            "title": title,
            "headers": headers,
            "rows": rows
        }
    
    def generate_colors(self, count: int, scheme: str = "primary") -> List[str]:
        """生成颜色方案"""
        colors = self.COLORS.get(scheme, self.COLORS["primary"])
        return [colors[i % len(colors)] for i in range(count)]


class HTMLReportRenderer:
    """HTML 报告渲染器"""
    
    def __init__(self):
        self.chart_generator = ChartGenerator()
    
    def render(self, title: str, sections: List[Dict], charts: List[Dict] = None) -> str:
        """渲染完整 HTML 报告"""
        charts = charts or []
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
{self._get_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="meta">
                <span class="date">生成时间：{self._get_current_time()}</span>
            </div>
        </header>
        
        <nav class="toc">
            <h2>目录</h2>
            <ul>
{self._generate_toc(sections)}
            </ul>
        </nav>
        
        <main>
{self._render_sections(sections)}
        </main>
        
{self._render_charts(charts)}
        
        <footer>
            <p>本报告由技术交流评估报告生成器自动生成</p>
        </footer>
    </div>
    
    <script>
{self._get_scripts(charts)}
    </script>
</body>
</html>"""
        return html
    
    def _get_styles(self) -> str:
        return """
        :root {
            --primary: #2E86AB;
            --secondary: #A23B72;
            --accent: #F18F01;
            --success: #28A745;
            --warning: #FFC107;
            --danger: #DC3545;
            --text: #333;
            --text-light: #666;
            --bg: #fff;
            --bg-light: #f8f9fa;
            --border: #dee2e6;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg-light);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: var(--bg);
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        
        header {
            text-align: center;
            padding: 40px 0;
            border-bottom: 3px solid var(--primary);
            margin-bottom: 30px;
        }
        
        header h1 {
            color: var(--primary);
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .meta {
            color: var(--text-light);
            font-size: 0.9em;
        }
        
        .toc {
            background: var(--bg-light);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        
        .toc h2 {
            color: var(--primary);
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .toc ul {
            list-style: none;
            columns: 2;
        }
        
        .toc li {
            margin-bottom: 8px;
        }
        
        .toc a {
            color: var(--text);
            text-decoration: none;
            transition: color 0.2s;
        }
        
        .toc a:hover {
            color: var(--primary);
        }
        
        main {
            margin-bottom: 40px;
        }
        
        .section {
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 1px solid var(--border);
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        h2 {
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--primary);
        }
        
        h3 {
            color: var(--secondary);
            margin: 20px 0 10px;
        }
        
        p {
            margin-bottom: 15px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: var(--bg);
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border: 1px solid var(--border);
        }
        
        th {
            background: var(--primary);
            color: white;
            font-weight: 600;
        }
        
        tr:nth-child(even) {
            background: var(--bg-light);
        }
        
        tr:hover {
            background: #e9ecef;
        }
        
        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: var(--bg);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .chart-container h3 {
            text-align: center;
            margin-bottom: 20px;
            color: var(--primary);
        }
        
        .chart-wrapper {
            position: relative;
            height: 400px;
            width: 100%;
        }
        
        .gauge-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
        }
        
        .gauge {
            position: relative;
            width: 200px;
            height: 100px;
            overflow: hidden;
        }
        
        .gauge-bg {
            position: absolute;
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: conic-gradient(
                var(--success) 0deg,
                var(--warning) 120deg,
                var(--danger) 240deg,
                transparent 360deg
            );
            clip-path: polygon(0 0, 100% 0, 100% 50%, 0 50%);
        }
        
        .gauge-value {
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            font-size: 2em;
            font-weight: bold;
            color: var(--primary);
        }
        
        .timeline {
            position: relative;
            padding: 20px 0;
        }
        
        .timeline::before {
            content: '';
            position: absolute;
            left: 50%;
            top: 0;
            bottom: 0;
            width: 2px;
            background: var(--primary);
            transform: translateX(-50%);
        }
        
        .timeline-item {
            position: relative;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
        }
        
        .timeline-item:nth-child(odd) {
            flex-direction: row-reverse;
        }
        
        .timeline-content {
            width: 45%;
            padding: 15px;
            background: var(--bg);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .timeline-dot {
            position: absolute;
            left: 50%;
            width: 20px;
            height: 20px;
            background: var(--primary);
            border-radius: 50%;
            transform: translateX(-50%);
        }
        
        .risk-high { color: var(--danger); font-weight: bold; }
        .risk-medium { color: var(--warning); font-weight: bold; }
        .risk-low { color: var(--success); font-weight: bold; }
        
        details {
            margin: 15px 0;
            padding: 15px;
            background: var(--bg-light);
            border-radius: 8px;
            border: 1px solid var(--border);
        }
        
        summary {
            cursor: pointer;
            font-weight: 600;
            color: var(--primary);
        }
        
        summary:hover {
            color: var(--secondary);
        }
        
        footer {
            text-align: center;
            padding: 30px;
            margin-top: 40px;
            background: var(--bg-light);
            border-radius: 8px;
            color: var(--text-light);
        }
        
        @media print {
            body {
                background: white;
            }
            .container {
                box-shadow: none;
            }
            .toc {
                break-after: page;
            }
            .section {
                break-inside: avoid;
            }
        }
        
        @media (max-width: 768px) {
            .toc ul {
                columns: 1;
            }
            .timeline::before {
                left: 20px;
            }
            .timeline-item,
            .timeline-item:nth-child(odd) {
                flex-direction: row;
            }
            .timeline-content {
                width: calc(100% - 50px);
                margin-left: 50px;
            }
            .timeline-dot {
                left: 20px;
            }
        }
        """
    
    def _get_current_time(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def _generate_toc(self, sections: List[Dict]) -> str:
        toc = ""
        for i, section in enumerate(sections):
            title = section.get("title", f"第{i+1}章")
            toc += f'                <li><a href="#section-{i}">{title}</a></li>\n'
        return toc
    
    def _render_sections(self, sections: List[Dict]) -> str:
        html = ""
        for i, section in enumerate(sections):
            title = section.get("title", f"第{i+1}章")
            content = section.get("content", "")
            
            html += f"""
            <section id="section-{i}" class="section">
                <h2>{title}</h2>
                {content}
            </section>
"""
        return html
    
    def _render_charts(self, charts: List[Dict]) -> str:
        if not charts:
            return ""
        
        html = '<section class="charts-section">\n'
        html += '    <h2>数据可视化</h2>\n'
        
        for i, chart in enumerate(charts):
            chart_type = chart.get("type", "bar")
            title = chart.get("title", f"图表{i+1}")
            
            if chart_type == "gauge":
                html += self._render_gauge(i, chart)
            elif chart_type == "timeline":
                html += self._render_timeline(i, chart)
            elif chart_type == "table":
                html += self._render_table(i, chart)
            else:
                html += self._render_chartjs(i, chart)
        
        html += '</section>\n'
        return html
    
    def _render_chartjs(self, index: int, chart: Dict) -> str:
        title = chart.get("title", f"图表{index+1}")
        return f"""
        <div class="chart-container">
            <h3>{title}</h3>
            <div class="chart-wrapper">
                <canvas id="chart-{index}"></canvas>
            </div>
        </div>
"""
    
    def _render_gauge(self, index: int, chart: Dict) -> str:
        title = chart.get("title", "")
        value = chart.get("value", 0)
        color = chart.get("color", "#4A90D9")
        
        return f"""
        <div class="chart-container">
            <h3>{title}</h3>
            <div class="gauge-container">
                <div class="gauge">
                    <div class="gauge-bg"></div>
                    <div class="gauge-value" style="color: {color}">{value}%</div>
                </div>
            </div>
        </div>
"""
    
    def _render_timeline(self, index: int, chart: Dict) -> str:
        title = chart.get("title", "")
        milestones = chart.get("milestones", [])
        
        items = ""
        for i, m in enumerate(milestones):
            time = m.get("time", "")
            label = m.get("label", "")
            items += f"""
                <div class="timeline-item">
                    <div class="timeline-content">
                        <strong>{time}</strong><br>
                        {label}
                    </div>
                    <div class="timeline-dot"></div>
                </div>
"""
        
        return f"""
        <div class="chart-container">
            <h3>{title}</h3>
            <div class="timeline">
                {items}
            </div>
        </div>
"""
    
    def _render_table(self, index: int, chart: Dict) -> str:
        title = chart.get("title", "")
        headers = chart.get("headers", [])
        rows = chart.get("rows", [])
        
        header_html = "".join(f"<th>{h}</th>" for h in headers)
        rows_html = ""
        for row in rows:
            cells = "".join(f"<td>{cell}</td>" for cell in row)
            rows_html += f"<tr>{cells}</tr>"
        
        return f"""
        <div class="chart-container">
            <h3>{title}</h3>
            <table>
                <thead><tr>{header_html}</tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
"""
    
    def _get_scripts(self, charts: List[Dict]) -> str:
        scripts = """
        // 折叠功能
        document.querySelectorAll('details').forEach(detail => {
            detail.addEventListener('toggle', e => {
                if (e.target.open) {
                    e.target.style.borderColor = 'var(--primary)';
                } else {
                    e.target.style.borderColor = 'var(--border)';
                }
            });
        });
        
        // 平滑滚动
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
"""
        
        # 渲染 Chart.js 图表
        chart_scripts = ""
        for i, chart in enumerate(charts):
            chart_type = chart.get("type", "bar")
            if chart_type in ["gauge", "timeline", "table"]:
                continue
            
            chart_scripts += f"""
        // 图表 {i}
        new Chart(document.getElementById('chart-{i}'), {{
            type: '{chart_type}',
            data: {json.dumps(chart.get('data', {}))},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: false
                    }},
                    legend: {{
                        position: 'top'
                    }}
                }},
                {json.dumps(chart.get('options', {}))[1:-1]}
            }}
        }});
"""
        
        return scripts + chart_scripts
