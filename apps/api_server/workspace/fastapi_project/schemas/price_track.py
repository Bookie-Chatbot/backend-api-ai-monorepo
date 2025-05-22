from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PriceTrackCreate(BaseModel):
    user_id: int
    origin: str
    destination: str
    departure_date: str  # YYYY-MM-DD 형식
    threshold: int

class PriceTrackRead(BaseModel):
    id: int
    user_id: int
    origin: str
    destination: str
    departure_date: str
    threshold: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True