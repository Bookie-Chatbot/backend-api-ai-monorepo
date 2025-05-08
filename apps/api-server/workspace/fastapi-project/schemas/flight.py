from pydantic import BaseModel
from datetime import datetime

class FlightCreate(BaseModel):
    airline: str
    departure: str
    arrival: str
    departure_time: datetime
    arrival_time: datetime
    price: float
    available_seats: int

class FlightResponse(BaseModel):
    id: int
    airline: str
    departure: str
    arrival: str
    departure_time: datetime
    arrival_time: datetime
    price: float
    available_seats: int

    class Config:
        from_attributes = True  # FastAPI V2에서 'orm_mode' 대신 사용