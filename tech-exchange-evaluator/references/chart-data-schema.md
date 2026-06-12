# 图表数据格式参考

报告需要提取结构化图表数据，写入 `output/report_data.json`，格式如下：

## 基本结构

```json
{
  "title": "报告标题",
  "date": "YYYY-MM-DD",
  "tech_topic": "技术主题简称",
  "version": "精简版/完整版",
  "charts": {
    "benchmark_comparison": { ... },
    "cost_by_pathway": { ... },
    "scenario_analysis": { ... },
    "risk_matrix": { ... },
    "decision_timeline": { ... },
    "investment_breakdown": { ... }
  }
}
```

## 图表类型说明

### 1. benchmark_comparison - 对方主张 vs 行业基准

**用途：** 对比对方声称的技术参数与行业基准值

```json
{
  "title": "对方主张 vs 行业基准",
  "type": "bar_grouped",
  "labels": ["指标1", "指标2", "指标3"],
  "datasets": [
    {
      "label": "对方主张",
      "data": [值1, 值2, 值3]
    },
    {
      "label": "行业基准",
      "data": [值1, 值2, 值3]
    }
  ]
}
```

**Chart.js 渲染代码：**
```javascript
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: chartData.labels,
    datasets: chartData.datasets
  },
  options: {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: chartData.title
      }
    }
  }
});
```

### 2. cost_by_pathway - 各技术路线运营成本对比

**用途：** 展示不同技术路线的经济性差异

```json
{
  "title": "各技术路线运营成本对比",
  "type": "bar",
  "labels": ["饲料化路线", "厌氧消化路线", "好氧堆肥路线"],
  "datasets": [
    {
      "label": "运营成本(元/吨)",
      "data": [150, 200, 180]
    }
  ]
}
```

### 3. scenario_analysis - 投资收益情景分析

**用途：** 展示不同情景下的投资回报

```json
{
  "title": "投资收益情景分析",
  "type": "bar_grouped",
  "labels": ["悲观", "中性", "乐观"],
  "datasets": [
    {
      "label": "年收入(万元)",
      "data": [500, 800, 1200]
    },
    {
      "label": "年成本(万元)",
      "data": [600, 700, 800]
    },
    {
      "label": "年毛利(万元)",
      "data": [-100, 100, 400]
    }
  ]
}
```

### 4. risk_matrix - 主要风险评估

**用途：** 展示各风险的严重程度

```json
{
  "title": "主要风险评估",
  "type": "horizontal_bar",
  "labels": ["技术风险", "市场风险", "政策风险", "合作风险"],
  "datasets": [
    {
      "label": "风险评分",
      "data": [8, 6, 7, 5]
    }
  ]
}
```

**说明：** 风险评分范围 1-10，10 为最高风险

### 5. decision_timeline - 决策路径时间线

**用途：** 展示关键决策节点和时间安排

```json
{
  "title": "决策路径时间线",
  "type": "timeline",
  "milestones": [
    {
      "time": "T+0",
      "label": "启动试点评估"
    },
    {
      "time": "T+3月",
      "label": "完成技术验证"
    },
    {
      "time": "T+6月",
      "label": "经济性测算完成"
    },
    {
      "time": "T+12月",
      "label": "试点项目验收"
    }
  ]
}
```

**Chart.js 渲染建议：** 使用自定义 HTML/CSS 渲染，而非 Chart.js 原生图表

### 6. investment_breakdown - 投资构成

**用途：** 展示各方投入的构成

```json
{
  "title": "投资构成",
  "type": "stacked_bar",
  "labels": ["我方", "对方"],
  "datasets": [
    {
      "label": "设备投资",
      "data": [300, 500]
    },
    {
      "label": "场地改造",
      "data": [100, 50]
    },
    {
      "label": "流动资金",
      "data": [200, 100]
    }
  ]
}
```

## 数据要求

1. **数值必须与报告正文一致** - 图表数据应直接从报告中提取
2. **仅提取可量化的数值** - 温度、金额、百分比等，不可量化的描述性内容不纳入
3. **如某类数据不存在** - 对应图表字段留空 `{}`
4. **单位标注** - 在 dataset 的 label 中注明单位（如"元/吨"、"万元"）

## HTML 报告中的图表插入位置

- **4.1 核心发现后** → 基准对比图（对方主张 vs 行业基准）
- **4.2 量化分析中** → 情景分析图 + 各路线成本对比图
- **4.3 决策路径中** → 时间线图 + 投资构成图
- **4.4 主要风险后** → 风险矩阵图

## 示例：餐厨剩余物饲料化项目

```json
{
  "title": "餐厨剩余物饲料化技术评估报告",
  "date": "2026-06-12",
  "tech_topic": "餐厨剩余物饲料化",
  "version": "精简版",
  "charts": {
    "benchmark_comparison": {
      "title": "对方主张 vs 行业基准",
      "type": "bar_grouped",
      "labels": ["灭菌温度(°C)", "灭菌时间(min)", "产品产率(%)", "处理成本(元/吨)"],
      "datasets": [
        {
          "label": "对方主张",
          "data": [135, 30, 25, 150]
        },
        {
          "label": "行业基准",
          "data": [133, 30, 20, 200]
        }
      ]
    },
    "cost_by_pathway": {
      "title": "各技术路线运营成本对比",
      "type": "bar",
      "labels": ["饲料化", "厌氧消化", "好氧堆肥"],
      "datasets": [
        {
          "label": "运营成本(元/吨)",
          "data": [150, 250, 180]
        }
      ]
    },
    "scenario_analysis": {
      "title": "投资收益情景分析",
      "type": "bar_grouped",
      "labels": ["悲观", "中性", "乐观"],
      "datasets": [
        {
          "label": "年收入(万元)",
          "data": [800, 1200, 1600]
        },
        {
          "label": "年成本(万元)",
          "data": [900, 1000, 1100]
        },
        {
          "label": "年毛利(万元)",
          "data": [-100, 200, 500]
        }
      ]
    },
    "risk_matrix": {
      "title": "主要风险评估",
      "type": "horizontal_bar",
      "labels": ["技术成熟度", "政策合规", "市场竞争", "合作稳定性"],
      "datasets": [
        {
          "label": "风险评分",
          "data": [7, 5, 6, 4]
        }
      ]
    },
    "decision_timeline": {
      "title": "决策路径时间线",
      "type": "timeline",
      "milestones": [
        {"time": "T+0", "label": "启动沈阳试点"},
        {"time": "T+2月", "label": "完成加热设备选型"},
        {"time": "T+4月", "label": "试点项目投产"},
        {"time": "T+6月", "label": "经济性验证完成"},
        {"time": "T+12月", "label": "评估是否扩大合作"}
      ]
    },
    "investment_breakdown": {
      "title": "投资构成",
      "type": "stacked_bar",
      "labels": ["我方（光大）", "对方（艾普罗斯）"],
      "datasets": [
        {
          "label": "设备投资(万元)",
          "data": [200, 500]
        },
        {
          "label": "场地改造(万元)",
          "data": [50, 100]
        },
        {
          "label": "流动资金(万元)",
          "data": [100, 200]
        }
      ]
    }
  }
}
```
