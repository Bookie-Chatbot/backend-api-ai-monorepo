# models_amadeus.py  ── 신규(또는 기존 models.py에 합쳐도 OK)
from typing import List, Union
from pydantic import BaseModel, Field


# ─────────────── 1. search-flights ───────────────
class FlightItinerary(BaseModel):
    type: str                # "Outbound" | "Return"
    duration: str            # "14h 35m"
    stops: str               # "Non-stop" or "1 stop"
    segments: str            # 문자열 하나에 모든 구간을 파이프(|)로 연결

class FlightOfferSummary(BaseModel):
    price: str               # "912000 KRW"
    bookableSeats: Union[int, str]
    airlines: str            # "KE, DL"
    itineraries: List[FlightItinerary]

class FlightOffersResponse(BaseModel):
    """search-flights 결과 = offer 리스트"""
    __root__: List[FlightOfferSummary]


# ─────────────── 2. find-cheapest-dates ───────────────
class CheapestDateResult(BaseModel):
    route: str               # "ICN-LAX"
    carrier: str             # "KE"
    departure: str           # ISO 8601
    arrival: str             # ISO 8601
    price: str               # "840000 KRW"
    offer_id: str


# ─────────────── 3. analyze-flight-prices ───────────────
class PriceMetric(BaseModel):
    quartileRanking: str     # MINIMUM | FIRST | MEDIUM | THIRD | MAXIMUM
    amount: float

class PriceAnalysisContent(BaseModel):
    message: str
    origin: str
    destination: str
    departureDate: str
    currencyCode: str
    oneWay: bool
    priceMetrics: List[PriceMetric]


# ─────────────── 4. get-flight-details ───────────────
class SegmentDetail(BaseModel):
    from_: str = Field(..., alias="from")   # "ICN @ 2025-06-03T20:00"
    to:   str                               # "LAX @ 2025-06-03T15:20"
    carrier: str                            # "KE17"

class FlightDetailsResponse(BaseModel):
    price: str                              # "912000 KRW"
    bookableSeats: Union[int, str]
    airlines: str
    segments: List[SegmentDetail]


# ─────────────── 5. SCHEMA_MAP 확장 ───────────────
SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "search-flights":       FlightOffersResponse,
    "find-cheapest-dates":  CheapestDateResult,
    "analyze-flight-prices": PriceAnalysisContent,
    "get-flight-details":   FlightDetailsResponse,
}
SCHEMA_MAP.update({
    "search-flights":       FlightOffersResponse,
    "find-cheapest-dates":  CheapestDateResult,
    "analyze-flight-prices": PriceAnalysisContent,
    "get-flight-details":   FlightDetailsResponse,
})
