"""
任务模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..core.database import Base


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    version = Column(String(20), default="compact")  # compact, full
    progress = Column(Float, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 关系
    user = relationship("User", back_populates="tasks")
    files = relationship("File", back_populates="task", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="task", cascade="all, delete-orphan")
