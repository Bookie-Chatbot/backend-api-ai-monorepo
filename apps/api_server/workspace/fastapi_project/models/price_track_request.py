# models/price_track_request.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class PriceTrackRequest(Base):
    __tablename__ = "price_track_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    origin = Column(String(10), nullable=False)
    destination = Column(String(10), nullable=False)
    departure_date = Column(String(20), nullable=False)
    threshold = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)                   #처리되면 active는 false다
    created_at = Column(DateTime, server_default=func.now())