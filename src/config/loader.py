"""
配置加载器

支持：
1. YAML 配置文件加载
2. 环境变量覆盖
3. 配置验证
4. 多环境配置合并
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PipelineConfig:
    """流水线配置"""
    max_parallel_agents: int = 2
    timeout_minutes: int = 30
    retry_attempts: int = 2
    enable_checkpoint: bool = True
    checkpoint_interval: int = 300


@dataclass
class SearchConfig:
    """搜索配置"""
    max_queries: int = 7
    timeout_seconds: int = 30
    min_results_threshold: int = 3
    recency_years: int = 2
    engine: str = "websearch"
    search_depth: str = "advanced"


@dataclass
class OutputConfig:
    """输出配置"""
    directory: str = "output"
    formats: list = field(default_factory=lambda: ["docx", "html", "json"])
    chart_library: str = "chartjs"
    generate_html: bool = True
    generate_chart_data: bool = True


@dataclass
class QualityConfig:
    """质量保障配置"""
    enable_critic: bool = True
    enable_fact_checker: bool = True
    min_quality_score: int = 60
    numerical_tolerance: float = 0.05


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    file: str = "output/evaluation.log"
    console: bool = True
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class InputConfig:
    """输入配置"""
    directory: str = "input"
    transcript: str = "input/transcript.md"
    counterpart: str = "input/counterpart/"
    benchmark: str = "input/benchmark/"
    supported_formats: list = field(default_factory=lambda: ["md", "pdf", "docx"])


@dataclass
class AppConfig:
    """应用配置"""
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    input: InputConfig = field(default_factory=InputConfig)


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._config = None
    
    def load(self, environment: str = None) -> AppConfig:
        """
        加载配置
        
        Args:
            environment: 环境名称（development/production），默认根据环境变量判断
        
        Returns:
            AppConfig: 配置对象
        """
        # 加载默认配置
        config_data = self._load_yaml("default.yaml")
        
        # 加载环境配置
        if environment is None:
            environment = os.getenv("APP_ENV", "development")
        
        env_config_path = f"{environment}.yaml"
        if (self.config_dir / env_config_path).exists():
            env_config = self._load_yaml(env_config_path)
            config_data = self._merge_configs(config_data, env_config)
        
        # 应用环境变量覆盖
        config_data = self._apply_env_overrides(config_data)
        
        # 转换为配置对象
        self._config = self._dict_to_config(config_data)
        
        return self._config
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            return {}
        
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """合并配置"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict) -> Dict:
        """应用环境变量覆盖"""
        # 环境变量格式：APP_PIPELINE_TIMEOUT_MINUTES=60
        # 映射到配置：pipeline.timeout_minutes
        
        env_mappings = {
            "APP_PIPELINE_TIMEOUT_MINUTES": ("pipeline", "timeout_minutes", int),
            "APP_PIPELINE_MAX_PARALLEL": ("pipeline", "max_parallel_agents", int),
            "APP_SEARCH_MAX_QUERIES": ("search", "max_queries", int),
            "APP_OUTPUT_DIRECTORY": ("output", "directory", str),
            "APP_LOGGING_LEVEL": ("logging", "level", str),
            "APP_QUALITY_MIN_SCORE": ("quality", "min_quality_score", int),
        }
        
        for env_var, (section, key, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                if section not in config:
                    config[section] = {}
                config[section][key] = value_type(env_value)
        
        return config
    
    def _dict_to_config(self, data: Dict) -> AppConfig:
        """将字典转换为配置对象"""
        return AppConfig(
            pipeline=PipelineConfig(**data.get("pipeline", {})),
            search=SearchConfig(**data.get("search", {})),
            output=OutputConfig(**data.get("output", {})),
            quality=QualityConfig(**data.get("quality", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            input=InputConfig(**data.get("input", {}))
        )
    
    def get_config(self) -> Optional[AppConfig]:
        """获取当前配置"""
        return self._config
    
    def validate_config(self, config: AppConfig) -> bool:
        """验证配置"""
        errors = []
        
        # 验证流水线配置
        if config.pipeline.max_parallel_agents < 1:
            errors.append("pipeline.max_parallel_agents 必须大于 0")
        
        if config.pipeline.timeout_minutes < 1:
            errors.append("pipeline.timeout_minutes 必须大于 0")
        
        # 验证搜索配置
        if config.search.max_queries < 1:
            errors.append("search.max_queries 必须大于 0")
        
        # 验证质量配置
        if config.quality.min_quality_score < 0 or config.quality.min_quality_score > 100:
            errors.append("quality.min_quality_score 必须在 0-100 之间")
        
        if errors:
            print("配置验证失败：")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True


# 全局配置实例
_config_loader = ConfigLoader()
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = _config_loader.load()
    return _config


def load_config(environment: str = None) -> AppConfig:
    """加载配置"""
    global _config
    _config = _config_loader.load(environment)
    return _config


def reload_config():
    """重新加载配置"""
    global _config
    _config = _config_loader.load()
    return _config
