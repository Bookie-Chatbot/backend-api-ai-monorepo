from sqlalchemy import Column, Integer, String, DateTime, JSON
from database import Base
from datetime import datetime

class AI_Response(Base):
    __tablename__ = "AI_responses"
    __table_args__ = {'extend_existing': True}


    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    intent = Column(String(50), nullable=False, index=True)
    contents = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)