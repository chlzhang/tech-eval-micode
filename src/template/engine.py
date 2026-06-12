"""
报告模板系统

提供灵活的报告模板管理：
1. 模板定义与加载
2. 变量替换
3. 模板继承
4. 条件渲染
5. 循环渲染
"""

import os
import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from enum import Enum


class TemplateType(Enum):
    """模板类型"""
    FULL = "full"           # 完整版（8章）
    COMPACT = "compact"     # 精简版（4章）
    CUSTOM = "custom"       # 自定义


@dataclass
class TemplateSection:
    """模板章节"""
    id: str
    title: str
    content: str
    required: bool = True
    order: int = 0
    conditions: List[str] = field(default_factory=list)
    variables: Set[str] = field(default_factory=set)


@dataclass
class Template:
    """报告模板"""
    name: str
    version: str
    description: str
    template_type: TemplateType
    sections: List[TemplateSection]
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent: Optional[str] = None  # 继承的父模板
    
    def get_section(self, section_id: str) -> Optional[TemplateSection]:
        """获取指定章节"""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None
    
    def get_ordered_sections(self) -> List[TemplateSection]:
        """获取按顺序排列的章节"""
        return sorted(self.sections, key=lambda s: s.order)


class TemplateParser:
    """模板解析器"""
    
    # 变量模式：{{variable_name}}
    VARIABLE_PATTERN = re.compile(r'\{\{(\w+(?:\.\w+)*)\}\}')
    
    # 条件模式：{% if condition %}...{% endif %}
    CONDITION_PATTERN = re.compile(
        r'\{%\s*if\s+(\w+(?:\.\w+)*)\s*%\}(.*?)\{%\s*endif\s*%\}',
        re.DOTALL
    )
    
    # 循环模式：{% for item in collection %}...{% endfor %}
    LOOP_PATTERN = re.compile(
        r'\{%\s*for\s+(\w+)\s+in\s+(\w+(?:\.\w+)*)\s*%\}(.*?)\{%\s*endfor\s*%\}',
        re.DOTALL
    )
    
    def parse(self, template_content: str) -> Dict[str, Any]:
        """解析模板内容"""
        # 提取变量
        variables = set(self.VARIABLE_PATTERN.findall(template_content))
        
        # 提取条件
        conditions = self.CONDITION_PATTERN.findall(template_content)
        
        # 提取循环
        loops = self.LOOP_PATTERN.findall(template_content)
        
        return {
            "variables": variables,
            "conditions": conditions,
            "loops": loops,
            "content": template_content
        }
    
    def extract_variables(self, content: str) -> Set[str]:
        """提取模板中的变量"""
        return set(self.VARIABLE_PATTERN.findall(content))


class TemplateRenderer:
    """模板渲染器"""
    
    def __init__(self):
        self.parser = TemplateParser()
    
    def render(self, template: Template, context: Dict[str, Any]) -> str:
        """渲染模板"""
        # 获取有序章节
        sections = template.get_ordered_sections()
        
        # 渲染每个章节
        rendered_sections = []
        for section in sections:
            # 检查条件
            if not self._check_conditions(section, context):
                continue
            
            # 渲染章节内容
            rendered_content = self._render_section(section, context)
            
            if rendered_content.strip():
                rendered_sections.append(rendered_content)
        
        # 合并所有章节
        return "\n\n".join(rendered_sections)
    
    def _check_conditions(self, section: TemplateSection, context: Dict[str, Any]) -> bool:
        """检查章节条件"""
        if not section.conditions:
            return True
        
        for condition in section.conditions:
            # 简单条件检查：变量存在且为真值
            if condition.startswith("!"):
                # 否定条件
                var_name = condition[1:]
                if self._get_variable(var_name, context):
                    return False
            else:
                if not self._get_variable(condition, context):
                    return False
        
        return True
    
    def _render_section(self, section: TemplateSection, context: Dict[str, Any]) -> str:
        """渲染单个章节"""
        content = section.content
        
        # 处理条件
        content = self._process_conditions(content, context)
        
        # 处理循环
        content = self._process_loops(content, context)
        
        # 替换变量
        content = self._replace_variables(content, context)
        
        return content
    
    def _process_conditions(self, content: str, context: Dict[str, Any]) -> str:
        """处理条件渲染"""
        def replace_condition(match):
            condition = match.group(1)
            block = match.group(2)
            
            if self._get_variable(condition, context):
                return block
            return ""
        
        return re.sub(
            r'\{%\s*if\s+(\w+(?:\.\w+)*)\s*%\}(.*?)\{%\s*endif\s*%\}',
            replace_condition,
            content,
            flags=re.DOTALL
        )
    
    def _process_loops(self, content: str, context: Dict[str, Any]) -> str:
        """处理循环渲染"""
        def replace_loop(match):
            item_var = match.group(1)
            collection_var = match.group(2)
            block = match.group(3)
            
            collection = self._get_variable(collection_var, context)
            if not collection or not isinstance(collection, (list, tuple)):
                return ""
            
            results = []
            for item in collection:
                # 创建新的上下文，添加循环变量
                loop_context = {**context, item_var: item}
                rendered = self._replace_variables(block, loop_context)
                results.append(rendered)
            
            return "\n".join(results)
        
        return re.sub(
            r'\{%\s*for\s+(\w+)\s+in\s+(\w+(?:\.\w+)*)\s*%\}(.*?)\{%\s*endfor\s*%\}',
            replace_loop,
            content,
            flags=re.DOTALL
        )
    
    def _replace_variables(self, content: str, context: Dict[str, Any]) -> str:
        """替换变量"""
        def replace_var(match):
            var_name = match.group(1)
            value = self._get_variable(var_name, context)
            if value is None:
                return match.group(0)  # 保留原始占位符
            return str(value)
        
        return re.sub(r'\{\{(\w+(?:\.\w+)*)\}\}', replace_var, content)
    
    def _get_variable(self, var_path: str, context: Dict[str, Any]) -> Any:
        """获取变量值（支持点号路径）"""
        parts = var_path.split(".")
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
            
            if value is None:
                return None
        
        return value


class TemplateManager:
    """模板管理器"""
    
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = Path(template_dir)
        self.templates: Dict[str, Template] = {}
        self.renderer = TemplateRenderer()
        self.parser = TemplateParser()
        
        # 加载内置模板
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """加载内置模板"""
        # 精简版模板
        compact_template = Template(
            name="compact",
            version="1.0.0",
            description="精简版报告模板（4章）",
            template_type=TemplateType.COMPACT,
            sections=[
                TemplateSection(
                    id="executive_summary",
                    title="一、执行摘要",
                    content=self._get_compact_summary_template(),
                    order=1
                ),
                TemplateSection(
                    id="background",
                    title="二、交流背景",
                    content=self._get_compact_background_template(),
                    order=2
                ),
                TemplateSection(
                    id="claims",
                    title="三、对方技术主张",
                    content=self._get_compact_claims_template(),
                    order=3
                ),
                TemplateSection(
                    id="conclusion",
                    title="四、初步结论",
                    content=self._get_compact_conclusion_template(),
                    order=4
                )
            ]
        )
        self.templates["compact"] = compact_template
        
        # 完整版模板
        full_template = Template(
            name="full",
            version="1.0.0",
            description="完整版报告模板（8章）",
            template_type=TemplateType.FULL,
            sections=self._create_full_sections()
        )
        self.templates["full"] = full_template
    
    def _get_compact_summary_template(self) -> str:
        return """# 一、执行摘要

{{summary.content}}

**总体判断**：{{summary.judgment}}
**关键理由**：{{summary.reasons}}
**潜在价值**：{{summary.value}}
**最大障碍**：{{summary.obstacles}}"""
    
    def _get_compact_background_template(self) -> str:
        return """# 二、交流背景

**对方单位**：{{background.counterpart.name}}
**主营业务**：{{background.counterpart.business}}
**交流形式**：{{background.meeting.form}}
**交流时间**：{{background.meeting.time}}
**核心技术**：{{background.tech_topic}}"""
    
    def _get_compact_claims_template(self) -> str:
        return """# 三、对方技术主张

## 3.1 核心技术原理

{{claims.principle}}

## 3.2 关键性能指标

| 参数 | 对方主张 | 行业基准 | 差异分析 |
|------|----------|----------|----------|
{% for param in claims.parameters %}| {{param.name}} | {{param.claimed}} | {{param.benchmark}} | {{param.analysis}} |
{% endfor %}

## 3.3 技术成熟度

{{claims.maturity}}

## 3.4 已有案例

{{cases.content}}"""
    
    def _get_compact_conclusion_template(self) -> str:
        return """# 四、初步结论

## 4.1 核心发现

{% for finding in conclusion.findings %}- **{{finding.title}}**：{{finding.content}}
{% endfor %}

## 4.2 量化分析

{{conclusion.quantitative.content}}

## 4.3 推荐方案与决策路径

**推荐方案**：{{conclusion.recommendation.content}}

| 决策节点 | 条件 | 行动 |
|----------|------|------|
{% for node in conclusion.decision_nodes %}| {{node.name}} | {{node.condition}} | {{node.action}} |
{% endfor %}

**退出条件**：
{% for condition in conclusion.exit_conditions %}- {{condition}}
{% endfor %}

## 4.4 主要风险

{% for risk in conclusion.risks %}- **{{risk.level}}**：{{risk.description}}
{% endfor %}

## 4.5 待核实清单

{% for item in conclusion.verification_list %}- [ ] {{item.content}}（建议核实方式：{{item.method}}）
{% endfor %}"""
    
    def _create_full_sections(self) -> List[TemplateSection]:
        """创建完整版模板章节"""
        return [
            TemplateSection(id="summary", title="一、执行摘要", content="", order=1),
            TemplateSection(id="background", title="二、交流背景", content="", order=2),
            TemplateSection(id="claims", title="三、对方技术主张", content="", order=3),
            TemplateSection(id="observations", title="四、我方现场观感", content="", order=4, conditions=["has_observations"]),
            TemplateSection(id="benchmarks", title="五、行业基准对照", content="", order=5),
            TemplateSection(id="evaluation", title="六、多维评估", content="", order=6),
            TemplateSection(id="decision", title="七、适配性与决策路径", content="", order=7),
            TemplateSection(id="risks", title="八、风险与待核实清单", content="", order=8)
        ]
    
    def get_template(self, name: str) -> Optional[Template]:
        """获取模板"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[Dict[str, str]]:
        """列出所有模板"""
        return [
            {
                "name": t.name,
                "version": t.version,
                "description": t.description,
                "type": t.template_type.value
            }
            for t in self.templates.values()
        ]
    
    def load_template(self, file_path: str) -> Template:
        """从文件加载模板"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"模板文件不存在: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            template_data = yaml.safe_load(f)
        
        return self._parse_template_data(template_data)
    
    def _parse_template_data(self, data: Dict[str, Any]) -> Template:
        """解析模板数据"""
        sections = []
        for i, section_data in enumerate(data.get("sections", [])):
            section = TemplateSection(
                id=section_data["id"],
                title=section_data["title"],
                content=section_data.get("content", ""),
                required=section_data.get("required", True),
                order=section_data.get("order", i),
                conditions=section_data.get("conditions", []),
                variables=self.parser.extract_variables(section_data.get("content", ""))
            )
            sections.append(section)
        
        return Template(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            template_type=TemplateType(data.get("type", "custom")),
            sections=sections,
            metadata=data.get("metadata", {}),
            parent=data.get("parent")
        )
    
    def render_report(self, template_name: str, context: Dict[str, Any]) -> str:
        """渲染报告"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        return self.renderer.render(template, context)
    
    def save_template(self, template: Template, file_path: str):
        """保存模板到文件"""
        data = {
            "name": template.name,
            "version": template.version,
            "description": template.description,
            "type": template.template_type.value,
            "metadata": template.metadata,
            "parent": template.parent,
            "sections": [
                {
                    "id": s.id,
                    "title": s.title,
                    "content": s.content,
                    "required": s.required,
                    "order": s.order,
                    "conditions": s.conditions
                }
                for s in template.sections
            ]
        }
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
