"""
报告模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..core.database import Base


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String(200))
    tech_topic = Column(String(100))
    version = Column(String(20))
    html_path = Column(String(500))
    docx_path = Column(String(500))
    data_path = Column(String(500))
    quality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    task = relationship("Task", back_populates="reports")
