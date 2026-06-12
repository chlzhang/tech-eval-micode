"""
模板系统单元测试
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.template.engine import (
    Template,
    TemplateSection,
    TemplateType,
    TemplateParser,
    TemplateRenderer,
    TemplateManager
)


class TestTemplateParser:
    """模板解析器测试"""
    
    def setup_method(self):
        self.parser = TemplateParser()
    
    def test_extract_variables(self):
        """测试提取变量"""
        content = "Hello {{name}}, your age is {{age}}"
        variables = self.parser.extract_variables(content)
        
        assert "name" in variables
        assert "age" in variables
        assert len(variables) == 2
    
    def test_extract_nested_variables(self):
        """测试提取嵌套变量"""
        content = "{{user.name}} lives in {{user.city}}"
        variables = self.parser.extract_variables(content)
        
        assert "user.name" in variables
        assert "user.city" in variables
    
    def test_parse_template(self):
        """测试解析模板"""
        content = """
        {% if show_title %}
        # {{title}}
        {% endif %}
        
        {% for item in items %}
        - {{item.name}}
        {% endfor %}
        """
        
        result = self.parser.parse(content)
        
        assert "variables" in result
        assert "conditions" in result
        assert "loops" in result


class TestTemplate:
    """模板测试"""
    
    def test_create_template(self):
        """测试创建模板"""
        template = Template(
            name="test",
            version="1.0.0",
            description="测试模板",
            template_type=TemplateType.COMPACT,
            sections=[
                TemplateSection(
                    id="section1",
                    title="第一章",
                    content="内容1",
                    order=1
                ),
                TemplateSection(
                    id="section2",
                    title="第二章",
                    content="内容2",
                    order=2
                )
            ]
        )
        
        assert template.name == "test"
        assert len(template.sections) == 2
    
    def test_get_section(self):
        """测试获取章节"""
        template = Template(
            name="test",
            version="1.0.0",
            description="测试模板",
            template_type=TemplateType.COMPACT,
            sections=[
                TemplateSection(id="s1", title="第一章", content="内容1", order=1),
                TemplateSection(id="s2", title="第二章", content="内容2", order=2)
            ]
        )
        
        section = template.get_section("s1")
        assert section is not None
        assert section.title == "第一章"
    
    def test_get_ordered_sections(self):
        """测试获取有序章节"""
        template = Template(
            name="test",
            version="1.0.0",
            description="测试模板",
            template_type=TemplateType.COMPACT,
            sections=[
                TemplateSection(id="s2", title="第二章", content="内容2", order=2),
                TemplateSection(id="s1", title="第一章", content="内容1", order=1)
            ]
        )
        
        ordered = template.get_ordered_sections()
        assert ordered[0].id == "s1"
        assert ordered[1].id == "s2"


class TestTemplateRenderer:
    """模板渲染器测试"""
    
    def setup_method(self):
        self.renderer = TemplateRenderer()
    
    def test_render_variables(self):
        """测试渲染变量"""
        template = Template(
            name="test",
            version="1.0.0",
            description="测试模板",
            template_type=TemplateType.COMPACT,
            sections=[
                TemplateSection(
                    id="s1",
                    title="测试",
                    content="Hello {{name}}, welcome to {{place}}!",
                    order=1
                )
            ]
        )
        
        context = {"name": "Alice", "place": "Beijing"}
        result = self.renderer.render(template, context)
        
        assert "Hello Alice, welcome to Beijing!" in result
    
    def test_render_nested_variables(self):
        """测试渲染嵌套变量"""
        template = Template(
            name="test",
            version="1.0.0",
            description="测试模板",
            template_type=TemplateType.COMPACT,
            sections=[
                TemplateSection(
                    id="s1",
                    title="测试",
                    content="{{user.name}} is {{user.age}} years old",
                    order=1
                )
            ]
        )
        
        context = {"user": {"name": "Bob", "age": 25}}
        result = self.renderer.render(template, context)
        
        assert "Bob is 25 years old" in result
    
    def test_render_conditions(self):
        """测试渲染条件"""
        template = Template(
            name="test",
            version="1.0.0",
            description="测试模板",
            template_type=TemplateType.COMPACT,
            sections=[
                TemplateSection(
                    id="s1",
                    title="测试",
                    content="{% if show_greeting %}Hello!{% endif %}World",
                    order=1
                )
            ]
        )
        
        # 条件为真
        result = self.renderer.render(template, {"show_greeting": True})
        assert "Hello!" in result
        assert "World" in result
        
        # 条件为假
        result = self.renderer.render(template, {"show_greeting": False})
        assert "Hello!" not in result
        assert "World" in result
    
    def test_render_loops(self):
        """测试渲染循环"""
        template = Template(
            name="test",
            version="1.0.0",
            description="测试模板",
            template_type=TemplateType.COMPACT,
            sections=[
                TemplateSection(
                    id="s1",
                    title="测试",
                    content="Items:\n{% for item in items %}- {{item.name}}\n{% endfor %}",
                    order=1
                )
            ]
        )
        
        context = {
            "items": [
                {"name": "Apple"},
                {"name": "Banana"},
                {"name": "Cherry"}
            ]
        }
        result = self.renderer.render(template, context)
        
        assert "Apple" in result
        assert "Banana" in result
        assert "Cherry" in result
    
    def test_render_section_conditions(self):
        """测试渲染章节条件"""
        template = Template(
            name="test",
            version="1.0.0",
            description="测试模板",
            template_type=TemplateType.COMPACT,
            sections=[
                TemplateSection(
                    id="s1",
                    title="第一章",
                    content="内容1",
                    order=1
                ),
                TemplateSection(
                    id="s2",
                    title="第二章",
                    content="内容2",
                    order=2,
                    conditions=["show_section2"]
                )
            ]
        )
        
        # 条件为真
        result = self.renderer.render(template, {"show_section2": True})
        assert "内容1" in result
        assert "内容2" in result
        
        # 条件为假
        result = self.renderer.render(template, {"show_section2": False})
        assert "内容1" in result
        assert "内容2" not in result


class TestTemplateManager:
    """模板管理器测试"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = TemplateManager(self.temp_dir)
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_builtin_templates(self):
        """测试内置模板"""
        templates = self.manager.list_templates()
        
        # 应该有 compact 和 full 两个内置模板
        template_names = [t["name"] for t in templates]
        assert "compact" in template_names
        assert "full" in template_names
    
    def test_get_template(self):
        """测试获取模板"""
        template = self.manager.get_template("compact")
        
        assert template is not None
        assert template.name == "compact"
        assert template.template_type == TemplateType.COMPACT
    
    def test_render_report(self):
        """测试渲染报告"""
        context = {
            "summary": {
                "content": "这是一份测试报告",
                "judgment": "技术可行",
                "reasons": "理由1、理由2",
                "value": "潜在价值高",
                "obstacles": "无重大障碍"
            },
            "background": {
                "counterpart": {
                    "name": "测试公司",
                    "business": "环保技术"
                },
                "meeting": {
                    "form": "线上会议",
                    "time": "2024-12-15"
                },
                "tech_topic": "餐厨垃圾处理"
            },
            "claims": {
                "principle": "高温消毒+固态发酵",
                "parameters": [
                    {"name": "灭菌温度", "claimed": "135°C", "benchmark": "133°C", "analysis": "符合"}
                ],
                "maturity": "中试阶段"
            },
            "conclusion": {
                "findings": [
                    {"title": "技术可行", "content": "符合行业标准"}
                ],
                "recommendation": {"content": "建议试点"},
                "decision_nodes": [],
                "exit_conditions": [],
                "risks": [],
                "verification_list": []
            }
        }
        
        result = self.manager.render_report("compact", context)
        
        assert "这是一份测试报告" in result
        assert "技术可行" in result
        assert "测试公司" in result
    
    def test_save_and_load_template(self):
        """测试保存和加载模板"""
        # 创建自定义模板
        template = Template(
            name="custom",
            version="1.0.0",
            description="自定义模板",
            template_type=TemplateType.CUSTOM,
            sections=[
                TemplateSection(
                    id="s1",
                    title="第一章",
                    content="Hello {{name}}!",
                    order=1
                )
            ]
        )
        
        # 保存模板
        file_path = Path(self.temp_dir) / "custom.yaml"
        self.manager.save_template(template, str(file_path))
        
        # 验证文件存在
        assert file_path.exists()
        
        # 加载模板
        loaded = self.manager.load_template(str(file_path))
        
        assert loaded.name == "custom"
        assert len(loaded.sections) == 1
        assert loaded.sections[0].content == "Hello {{name}}!"
    
    def test_list_templates(self):
        """测试列出模板"""
        templates = self.manager.list_templates()
        
        assert len(templates) >= 2  # 至少有 compact 和 full
        
        for t in templates:
            assert "name" in t
            assert "version" in t
            assert "description" in t
            assert "type" in t


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
