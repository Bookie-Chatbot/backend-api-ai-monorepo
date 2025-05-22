from sqlalchemy import Column, Integer, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from database import Base

class PriceTrackRequestModel(Base):
    __tablename__ = "price_track_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    search_params = Column(JSON, nullable=False)  # 예: {origin: "ICN", destination: "HND", departure_date: "2025-06-01", currency: "KRW"}
    price_threshold = Column(Integer, nullable=False) 
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())