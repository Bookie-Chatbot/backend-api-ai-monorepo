from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

class Hotel(Base):
    __tablename__ = 'hotels'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    available_rooms = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)