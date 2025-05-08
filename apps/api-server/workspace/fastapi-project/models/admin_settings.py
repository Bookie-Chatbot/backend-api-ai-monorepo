from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class AdminSettings(Base):
    __tablename__ = 'admin_settings'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)