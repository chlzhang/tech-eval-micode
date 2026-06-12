"""
文件模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..core.database import Base


class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    filename = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    upload_time = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    task = relationship("Task", back_populates="files")
