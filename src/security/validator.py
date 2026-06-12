"""
安全模块

提供输入验证和输出转义功能：
1. 输入验证
2. XSS 防护
3. 内容清理
4. 安全检查
"""

import re
import html
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SecurityCheckResult:
    """安全检查结果"""
    is_safe: bool
    issues: List[str]
    sanitized_input: Any = None


class InputValidator:
    """输入验证器"""
    
    # 危险模式
    DANGEROUS_PATTERNS = [
        (r'<script[^>]*>.*?</script>', "XSS: script标签"),
        (r'javascript:', "XSS: javascript协议"),
        (r'on\w+\s*=', "XSS: 事件处理器"),
        (r'<iframe[^>]*>.*?</iframe>', "XSS: iframe标签"),
        (r'<object[^>]*>.*?</object>', "XSS: object标签"),
        (r'<embed[^>]*>', "XSS: embed标签"),
        (r'<form[^>]*>.*?</form>', "XSS: form标签"),
        (r'expression\s*\(', "XSS: CSS表达式"),
        (r'url\s*\(', "XSS: CSS url"),
        (r'<svg[^>]*>.*?</svg>', "XSS: SVG标签"),
    ]
    
    # SQL注入模式
    SQL_INJECTION_PATTERNS = [
        (r"('|(\\')|(;)|(--)|(/\*)|(\*/))", "SQL注入: 特殊字符"),
        (r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b', "SQL注入: SQL关键字"),
    ]
    
    def __init__(self, check_xss: bool = True, check_sql: bool = True):
        self.check_xss = check_xss
        self.check_sql = check_sql
    
    def validate(self, input_data: Any) -> SecurityCheckResult:
        """验证输入数据"""
        issues = []
        
        if isinstance(input_data, str):
            if self.check_xss:
                xss_issues = self._check_xss(input_data)
                issues.extend(xss_issues)
            
            if self.check_sql:
                sql_issues = self._check_sql_injection(input_data)
                issues.extend(sql_issues)
        
        elif isinstance(input_data, dict):
            for key, value in input_data.items():
                result = self.validate(value)
                issues.extend(result.issues)
        
        elif isinstance(input_data, list):
            for item in input_data:
                result = self.validate(item)
                issues.extend(result.issues)
        
        return SecurityCheckResult(
            is_safe=len(issues) == 0,
            issues=issues
        )
    
    def _check_xss(self, text: str) -> List[str]:
        """检查 XSS 攻击"""
        issues = []
        for pattern, description in self.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                issues.append(description)
        return issues
    
    def _check_sql_injection(self, text: str) -> List[str]:
        """检查 SQL 注入"""
        issues = []
        for pattern, description in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(description)
        return issues


class OutputSanitizer:
    """输出清理器"""
    
    def __init__(self):
        # 使用 html.escape 直接处理，不需要手动映射
        pass
    
    def sanitize_html(self, text: str) -> str:
        """清理 HTML 内容"""
        return html.escape(text)
    
    def sanitize_for_json(self, text: str) -> str:
        """清理 JSON 输出"""
        # 转义特殊字符
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        return text
    
    def sanitize_for_log(self, text: str) -> str:
        """清理日志输出"""
        # 移除可能的日志注入
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        text = text.replace('\t', ' ')
        return text
    
    def remove_sensitive_data(self, text: str) -> str:
        """移除敏感数据"""
        # 移除可能的密钥、令牌等
        patterns = [
            (r'(?:password|passwd|pwd|secret|token|key|api_key)\s*[=:]\s*\S+', '[REDACTED]'),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
            (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]'),
            (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]'),
        ]
        
        sanitized = text
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized


class SecurityChecker:
    """安全检查器"""
    
    def __init__(self):
        self.validator = InputValidator()
        self.sanitizer = OutputSanitizer()
    
    def check_input(self, data: Any) -> SecurityCheckResult:
        """检查输入安全性"""
        return self.validator.validate(data)
    
    def sanitize_output(self, text: str, output_type: str = "html") -> str:
        """清理输出"""
        if output_type == "html":
            return self.sanitizer.sanitize_html(text)
        elif output_type == "json":
            return self.sanitizer.sanitize_for_json(text)
        elif output_type == "log":
            return self.sanitizer.sanitize_for_log(text)
        else:
            return text
    
    def generate_security_headers(self) -> Dict[str, str]:
        """生成安全头"""
        return {
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com;"
            ),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    def validate_file_upload(self, filename: str, content_type: str, 
                            file_size: int, max_size: int = 10 * 1024 * 1024) -> SecurityCheckResult:
        """验证文件上传"""
        issues = []
        
        # 检查文件扩展名
        allowed_extensions = ['.md', '.pdf', '.docx', '.txt', '.json']
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            issues.append(f"不允许的文件类型: {filename}")
        
        # 检查文件大小
        if file_size > max_size:
            issues.append(f"文件大小超过限制: {file_size} > {max_size}")
        
        # 检查文件名
        if '..' in filename or '/' in filename or '\\' in filename:
            issues.append("文件名包含非法字符")
        
        return SecurityCheckResult(
            is_safe=len(issues) == 0,
            issues=issues
        )
