from datetime import datetime, date
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class HotelSummary(BaseModel):
    name: str
    rating: float
    freeCancellation: bool
    summary: str
    bookingUrl: Optional[str]
    price: Optional[float]


class HotelSummaryContent(BaseModel):
    intent: Literal["HOTEL_SUMMARY"]= Field(..., exclude=True)
    hotels: List[HotelSummary]

