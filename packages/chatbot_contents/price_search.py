# chatbot_contents/price_search.py

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# (기존 FlightOffer 모델 임포트)
# from .price_search_base import FlightOffer

class FlightOption(BaseModel):
    origin: str
    destination: str
    departureDate: str
    returnDate: Optional[str]
    price: float
    currency: str
    bookingUrl: Optional[str]


class PriceSearchContent(BaseModel):
    flights: List[FlightOption]

{
  "intent": "PRICE_SEARCH",
  "contents": {
    "flights": [
      {
        "origin": "ICN",
        "destination": "LAX",
        "departureDate": "2025-06-15",
        "returnDate": "2025-06-22",
        "price": 1250000.0,
        "currency": "KRW",
        "bookingUrl": "https://booking.example.com/ICN-LAX"
      },
      {
        "origin": "ICN",
        "destination": "LAX",
        "departureDate": "2025-06-15",
        "price": 1100000.0,
        "currency": "KRW",
        "bookingUrl": ""
      }
    ]
  }
}




""" 가격 검색 결과를 담는 모델
class PriceSearchContent(BaseModel):
    # — 고정 메타필드 —
    session_id: str
    request_id: str
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="요청 생성 시각"
    )
    origin: str
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    adults: int = 1
    children: int = 0
    cabin_class: Optional[str] = None
    result_count: int = Field(
        ...,
        description="offers 리스트에 담긴 결과 수"
    )

    # — 실제 Amadeus 응답 offers —
    offers: List[FlightOffer]

    # — 사용자가 원하는 추가 속성 —
    extras: Optional[Dict[str, Any]] = Field(
        None,
        description="사용자 지정 필터나 플래그를 key/value 형태로 추가"
    )

    class Config:
        schema_extra = {
            "example": {
                "session_id": "sess-1234",
                "request_id": "req-5678",
                "timestamp": "2025-05-20T08:30:00Z",
                "origin": "ICN",
                "destination": "LAX",
                "departure_date": "2025-11-05",
                "return_date": "2025-11-12",
                "adults": 2,
                "children": 1,
                "cabin_class": "ECONOMY",
                "result_count": 3,
                "offers": [
                    { "FlightOffer 인스턴스 JSON" }
                ],
                "extras": {
                    "max_budget": 1500000,
                    "min_connection_time_mins": 60
                }
            }
        }
"""