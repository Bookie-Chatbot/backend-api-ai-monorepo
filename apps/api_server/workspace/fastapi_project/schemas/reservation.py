from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReservationCreate(BaseModel):
    user_id: int
    hotel_id: Optional[int] = None
    flight_id: Optional[int] = None
    status: str

class ReservationResponse(BaseModel):
    id: int
    user_id: int
    hotel_id: Optional[int] = None
    flight_id: Optional[int] = None
    status: str
    reservation_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # FastAPI V2에서 orm_mode 대신 사용