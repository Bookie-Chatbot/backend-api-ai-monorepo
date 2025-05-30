from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

class SearchParams(BaseModel):
    origin: str
    destination: str
    departure_date: str
    currency: Optional[str] = "KRW"  # 선택 항목은 Optional로 처리 가능

class PriceTrackBase(BaseModel):
    user_id: int
    search_params: SearchParams  # 예: {"origin": "ICN", "destination": "HND", "departure_date": "2025-06-01", "currency": "KRW"}
    price_threshold: int

class PriceTrackCreate(PriceTrackBase):
    pass

class PriceTrackResponse(PriceTrackBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy 모델과 호환되도록 함