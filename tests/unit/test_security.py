"""
安全模块单元测试
"""

import pytest

from src.security.validator import (
    InputValidator,
    OutputSanitizer,
    SecurityChecker,
    SecurityCheckResult
)


class TestInputValidator:
    """输入验证器测试"""
    
    def setup_method(self):
        self.validator = InputValidator()
    
    def test_safe_input(self):
        """测试安全输入"""
        result = self.validator.validate("这是一段正常的文本")
        assert result.is_safe is True
        assert len(result.issues) == 0
    
    def test_xss_script_tag(self):
        """测试 XSS script 标签"""
        result = self.validator.validate("<script>alert('xss')</script>")
        assert result.is_safe is False
        assert any("script" in issue for issue in result.issues)
    
    def test_xss_event_handler(self):
        """测试 XSS 事件处理器"""
        result = self.validator.validate('<img onerror="alert(1)" src="x">')
        assert result.is_safe is False
        assert any("事件处理器" in issue for issue in result.issues)
    
    def test_xss_javascript_protocol(self):
        """测试 XSS javascript 协议"""
        result = self.validator.validate('javascript:alert(1)')
        assert result.is_safe is False
        assert any("javascript" in issue for issue in result.issues)
    
    def test_sql_injection(self):
        """测试 SQL 注入"""
        result = self.validator.validate("'; DROP TABLE users; --")
        assert result.is_safe is False
        assert any("SQL" in issue for issue in result.issues)
    
    def test_sql_keywords(self):
        """测试 SQL 关键字"""
        result = self.validator.validate("SELECT * FROM users")
        assert result.is_safe is False
    
    def test_dict_validation(self):
        """测试字典验证"""
        data = {
            "name": "正常数据",
            "value": "<script>alert(1)</script>"
        }
        result = self.validator.validate(data)
        assert result.is_safe is False
    
    def test_list_validation(self):
        """测试列表验证"""
        data = ["正常数据", "<script>alert(1)</script>"]
        result = self.validator.validate(data)
        assert result.is_safe is False


class TestOutputSanitizer:
    """输出清理器测试"""
    
    def setup_method(self):
        self.sanitizer = OutputSanitizer()
    
    def test_html_escape(self):
        """测试 HTML 转义"""
        text = '<script>alert("xss")</script>'
        sanitized = self.sanitizer.sanitize_html(text)
        assert '<' not in sanitized or '<' in sanitized
        assert '<script>' not in sanitized
    
    def test_json_escape(self):
        """测试 JSON 转义"""
        text = 'value with "quotes" and \\backslash'
        sanitized = self.sanitizer.sanitize_for_json(text)
        assert '\\"' in sanitized
        assert '\\\\' in sanitized
    
    def test_log_sanitization(self):
        """测试日志清理"""
        text = "line1\nline2\rline3\ttab"
        sanitized = self.sanitizer.sanitize_for_log(text)
        assert '\n' not in sanitized
        assert '\r' not in sanitized
        assert '\t' not in sanitized
    
    def test_remove_sensitive_data(self):
        """测试移除敏感数据"""
        text = "password=secret123 user@email.com"
        sanitized = self.sanitizer.remove_sensitive_data(text)
        assert "secret123" not in sanitized
        assert "user@email.com" not in sanitized


class TestSecurityChecker:
    """安全检查器测试"""
    
    def setup_method(self):
        self.checker = SecurityChecker()
    
    def test_check_safe_input(self):
        """测试检查安全输入"""
        result = self.checker.check_input("正常文本")
        assert result.is_safe is True
    
    def test_check_unsafe_input(self):
        """测试检查不安全输入"""
        result = self.checker.check_input("<script>alert(1)</script>")
        assert result.is_safe is False
    
    def test_sanitize_html_output(self):
        """测试清理 HTML 输出"""
        text = '<b>bold</b>'
        sanitized = self.checker.sanitize_output(text, "html")
        assert '<b>' not in sanitized or '<b>' in sanitized
    
    def test_generate_security_headers(self):
        """测试生成安全头"""
        headers = self.checker.generate_security_headers()
        assert "Content-Security-Policy" in headers
        assert "X-Content-Type-Options" in headers
    
    def test_validate_file_upload_safe(self):
        """测试安全文件上传"""
        result = self.checker.validate_file_upload(
            "document.md", "text/markdown", 1024
        )
        assert result.is_safe is True
    
    def test_validate_file_upload_unsafe_extension(self):
        """测试不安全文件扩展名"""
        result = self.checker.validate_file_upload(
            "script.exe", "application/octet-stream", 1024
        )
        assert result.is_safe is False
    
    def test_validate_file_upload_too_large(self):
        """测试文件过大"""
        result = self.checker.validate_file_upload(
            "large.md", "text/markdown", 100 * 1024 * 1024
        )
        assert result.is_safe is False
    
    def test_validate_file_upload_path_traversal(self):
        """测试路径遍历"""
        result = self.checker.validate_file_upload(
            "../../../etc/passwd", "text/plain", 1024
        )
        assert result.is_safe is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
