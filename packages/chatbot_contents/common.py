# chatbot_contents/common.py
from typing import List, Optional
from pydantic import BaseModel, Field
from typing_extensions import Literal

# ── PRICE_SEARCH ───────────────────────────────
class FlightOption(BaseModel):
    origin: str
    destination: str
    departureDate: str
    returnDate: Optional[str] = ""
    price: float
    currency: str
    bookingUrl: Optional[str] = ""

class PriceSearchContent(BaseModel):
    intent: Literal["PRICE_SEARCH"] = "PRICE_SEARCH"
    contents: "PriceSearchBody"

class PriceSearchBody(BaseModel):
    message: str
    flights: List[FlightOption]

# ── PRICE_ANALYSIS ─────────────────────────────
class Quartile(BaseModel):
    quartileRanking: str
    amount: float

class PriceAnalysisContent(BaseModel):
    intent: Literal["PRICE_ANALYSIS"] = "PRICE_ANALYSIS"
    contents: dict                       # Amadeus 원본을 그대로 둠

# ── CHEAPEST_DATE ─────────────────────────────
class CheapestDateContent(BaseModel):
    intent: Literal["CHEAPEST_DATE"] = "CHEAPEST_DATE"
    contents: List[dict]

# ── FLIGHT_DETAILS ────────────────────────────
class FlightDetailsContent(BaseModel):
    intent: Literal["FLIGHT_DETAILS"] = "FLIGHT_DETAILS"
    contents: dict

# ── WEATHER_SUMMARY ───────────────────────────
class WeatherSummaryContent(BaseModel):
    intent: Literal["WEATHER_SUMMARY"] = "WEATHER_SUMMARY"
    contents: dict           # {location,date,summary,alerts}