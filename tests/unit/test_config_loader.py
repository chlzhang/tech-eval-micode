"""
配置加载器单元测试
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

from src.config.loader import (
    ConfigLoader,
    AppConfig,
    PipelineConfig,
    SearchConfig,
    OutputConfig,
    QualityConfig,
    LoggingConfig,
    InputConfig,
    get_config,
    load_config
)


class TestConfigLoader:
    """配置加载器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_config_file(self, filename: str, content: dict):
        """创建配置文件"""
        file_path = self.config_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(content, f)
        return file_path
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        self._create_config_file("default.yaml", {
            "pipeline": {
                "timeout_minutes": 30,
                "max_parallel_agents": 2
            }
        })
        
        loader = ConfigLoader(str(self.config_dir))
        config = loader.load("development")
        
        assert config.pipeline.timeout_minutes == 30
        assert config.pipeline.max_parallel_agents == 2
    
    def test_load_with_environment_override(self):
        """测试环境配置覆盖"""
        self._create_config_file("default.yaml", {
            "pipeline": {
                "timeout_minutes": 30
            }
        })
        
        self._create_config_file("development.yaml", {
            "pipeline": {
                "timeout_minutes": 10
            }
        })
        
        loader = ConfigLoader(str(self.config_dir))
        config = loader.load("development")
        
        assert config.pipeline.timeout_minutes == 10
    
    def test_load_with_env_variables(self):
        """测试环境变量覆盖"""
        self._create_config_file("default.yaml", {
            "pipeline": {
                "timeout_minutes": 30
            }
        })
        
        loader = ConfigLoader(str(self.config_dir))
        
        with patch.dict(os.environ, {"APP_PIPELINE_TIMEOUT_MINUTES": "60"}):
            config = loader.load("development")
        
        assert config.pipeline.timeout_minutes == 60
    
    def test_validate_config_success(self):
        """测试配置验证成功"""
        self._create_config_file("default.yaml", {
            "pipeline": {
                "max_parallel_agents": 2,
                "timeout_minutes": 30
            },
            "search": {
                "max_queries": 7
            },
            "quality": {
                "min_quality_score": 60
            }
        })
        
        loader = ConfigLoader(str(self.config_dir))
        config = loader.load("development")
        
        assert loader.validate_config(config) is True
    
    def test_validate_config_failure(self):
        """测试配置验证失败"""
        self._create_config_file("default.yaml", {
            "pipeline": {
                "max_parallel_agents": -1
            }
        })
        
        loader = ConfigLoader(str(self.config_dir))
        config = loader.load("development")
        
        assert loader.validate_config(config) is False
    
    def test_missing_config_file(self):
        """测试配置文件不存在"""
        loader = ConfigLoader(str(self.config_dir))
        config = loader.load("development")
        
        # 应该返回默认配置
        assert config is not None
        assert isinstance(config, AppConfig)


class TestAppConfig:
    """应用配置测试"""
    
    def test_default_values(self):
        """测试默认值"""
        config = AppConfig()
        
        assert config.pipeline.max_parallel_agents == 2
        assert config.pipeline.timeout_minutes == 30
        assert config.search.max_queries == 7
        assert config.output.directory == "output"
        assert config.quality.min_quality_score == 60
        assert config.logging.level == "INFO"
        assert config.input.directory == "input"
    
    def test_pipeline_config(self):
        """测试流水线配置"""
        config = PipelineConfig(
            max_parallel_agents=4,
            timeout_minutes=60,
            retry_attempts=3
        )
        
        assert config.max_parallel_agents == 4
        assert config.timeout_minutes == 60
        assert config.retry_attempts == 3
    
    def test_search_config(self):
        """测试搜索配置"""
        config = SearchConfig(
            max_queries=10,
            timeout_seconds=60,
            recency_years=3
        )
        
        assert config.max_queries == 10
        assert config.timeout_seconds == 60
        assert config.recency_years == 3
    
    def test_output_config(self):
        """测试输出配置"""
        config = OutputConfig(
            directory="custom_output",
            formats=["docx", "html"],
            generate_html=True
        )
        
        assert config.directory == "custom_output"
        assert "docx" in config.formats
        assert config.generate_html is True
    
    def test_quality_config(self):
        """测试质量配置"""
        config = QualityConfig(
            enable_critic=True,
            enable_fact_checker=True,
            min_quality_score=80
        )
        
        assert config.enable_critic is True
        assert config.enable_fact_checker is True
        assert config.min_quality_score == 80


class TestConfigIntegration:
    """配置集成测试"""
    
    def test_full_config_loading(self):
        """测试完整配置加载"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            
            # 创建完整配置
            config_data = {
                "pipeline": {
                    "max_parallel_agents": 3,
                    "timeout_minutes": 45,
                    "retry_attempts": 2,
                    "enable_checkpoint": True
                },
                "search": {
                    "max_queries": 7,
                    "timeout_seconds": 30,
                    "recency_years": 2
                },
                "output": {
                    "directory": "output",
                    "formats": ["docx", "html", "json"],
                    "chart_library": "chartjs"
                },
                "quality": {
                    "enable_critic": True,
                    "enable_fact_checker": True,
                    "min_quality_score": 70
                },
                "logging": {
                    "level": "INFO",
                    "console": True
                },
                "input": {
                    "directory": "input",
                    "transcript": "input/transcript.md"
                }
            }
            
            config_file = config_dir / "default.yaml"
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(str(config_dir))
            config = loader.load()
            
            assert config.pipeline.max_parallel_agents == 3
            assert config.pipeline.timeout_minutes == 45
            assert config.search.max_queries == 7
            assert config.output.directory == "output"
            assert config.quality.min_quality_score == 70
            assert config.logging.level == "INFO"
            assert config.input.directory == "input"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
