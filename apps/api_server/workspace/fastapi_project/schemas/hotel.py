from pydantic import BaseModel
from datetime import datetime

class HotelCreate(BaseModel):
    name: str
    location: str
    price: float
    available_rooms: int

class HotelResponse(BaseModel):
    id: int
    name: str
    location: str
    price: float
    available_rooms: int
    last_updated: datetime

    class Config:
        orm_mode = True