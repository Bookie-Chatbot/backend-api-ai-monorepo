from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class AdminSettings(Base):
    __tablename__ = 'admin_settings'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)