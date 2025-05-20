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


{
  "intent": "HOTEL_SUMMARY",
  "contents": {
    "hotels": [
      {
        "name": "Seoul Grand Hotel",
        "rating": 4.5,
        "freeCancellation": "true",
        "summary": "도심에 위치, 무료 조식 및 무료 취소 가능",
        "bookingUrl": "https://hotel.example.com/seoul-grand"
      },
      {
        "name": "Myeongdong Inn",
        "rating": 4.0,
        "freeCancellation": "false",
        "summary": "명동 쇼핑가 근처, 저렴한 가격대",
        "bookingUrl": ""
      }
    ]
  }
}
