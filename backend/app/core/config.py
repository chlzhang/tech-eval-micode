"""
应用配置
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "技术交流评估报告生成器"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/eval.db")
    
    # 文件存储
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./output")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # CORS配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # 管理员账号
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    class Config:
        env_file = ".env"


settings = Settings()


# 确保目录存在
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path("data").mkdir(parents=True, exist_ok=True)
