# chatbot_contents/common.py
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Literal



# ── PRICE_SEARCH ───────────────────────────────
class FlightOption(BaseModel):
    origin: str
    destination: str
    departureDate: str
    returnDate: Optional[str]
    price: float
    currency: str
    bookingUrl: Optional[str]

class PriceSearchContentsList(BaseModel):
    message: str
    flights: List[FlightOption]


class PriceSearchContent(BaseModel):
    intent: Literal["PRICE_SEARCH"]
    contents : PriceSearchContentsList








# ── PRICE_ANALYSIS ─────────────────────────────
class Quartile(BaseModel):
    quartileRanking: str
    amount: float

#class PriceAnalysisContent(BaseModel):
#    intent: Literal["PRICE_ANALYSIS"] = "PRICE_ANALYSIS"
#    contents: dict                       # Amadeus 원본을 그대로 둠




class PriceMetricsList(BaseModel):
    quartileRanking: str
    amount: float  # 소수점을 허용하도록 float로 변경

class PriceAnalysisContentsList(BaseModel):
    message: str
    origin: str
    destination: str
    departureDate: str
    currencyCode: str
    oneWay: bool
    priceMetrics: List[PriceMetricsList]


class PriceAnalysisContent(BaseModel):
    intent: Literal["PRICE_ANALYSIS"]= "PRICE_ANALYSIS"
    contents: PriceAnalysisContentsList








class CheapDays(BaseModel):
    route: str
    carrier: str
    departure: str
    arrival: Optional[str]
    price: int


class CheapestDateContentsList(BaseModel):
    message: str
    cards: List[CheapDays]


class CheapestDateContent(BaseModel):
    intent: Literal["CHEAPEST_DATE"] = Field(..., exclude=True)
    contents: CheapestDateContentsList


# ── FLIGHT_DETAILS ────────────────────────────
class FlightDetailsContent(BaseModel):
    intent: Literal["FLIGHT_DETAILS"] = "FLIGHT_DETAILS"
    contents: dict



class WeatherContentsList(BaseModel):
    message: str


# ── WEATHER_SUMMARY ───────────────────────────
class WeatherSummaryContent(BaseModel):
    intent: Literal["WEATHER_SUMMARY"] = "WEATHER_SUMMARY"
    contents: WeatherContentsList


