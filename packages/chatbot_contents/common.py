# chatbot_contents/common.py
from typing import List, Optional
from pydantic import BaseModel, Field
from typing_extensions import Literal
from datetime import datetime


# ── PRICE_SEARCH ───────────────────────────────
class FlightOption(BaseModel):
    origin: str
    destination: str
    departureDate: str
    returnDate: Optional[str]
    price: float
    currency: str
    bookingUrl: Optional[str]

class ContentsList(BaseModel):
    message: str
    flights: List[FlightOption]


class PriceSearchContent(BaseModel):
    intent: Literal["PRICE_SEARCH"]
    contents : ContentsList








# ── PRICE_ANALYSIS ─────────────────────────────
class Quartile(BaseModel):
    quartileRanking: str
    amount: float

class PriceAnalysisContent(BaseModel):
    intent: Literal["PRICE_ANALYSIS"] = "PRICE_ANALYSIS"
    contents: dict                       # Amadeus 원본을 그대로 둠




class CheapDays(BaseModel):
    route: str
    carrier: str
    departure: datetime
    arrival: datetime
    price: int


class ContentsList(BaseModel):
    message: str
    cards: List[CheapDays]


class CheapestDateContent(BaseModel):
    intent: Literal["CHEAPEST_DAYS"] = Field(..., exclude=True)
    contents: ContentsList


# ── FLIGHT_DETAILS ────────────────────────────
class FlightDetailsContent(BaseModel):
    intent: Literal["FLIGHT_DETAILS"] = "FLIGHT_DETAILS"
    contents: dict



class WeatherContentsList(BaseModel):
    message: str


# ── WEATHER_SUMMARY ───────────────────────────
class WeatherSummaryContent(BaseModel):
    intent: Literal["WEATHER_SUMMARY"] = Field(..., exclude=True)
    contents: WeatherContentsList


