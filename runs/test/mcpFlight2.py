# models_amadeus.py
from __future__ import annotations

from datetime import datetime
from typing import List, Union, Literal

from pydantic import BaseModel, Field, RootModel


# ───────── 1. search-flights ─────────


class FlightItinerary(BaseModel):
    type: str
    duration: str
    stops: str
    segments: str


class FlightOfferSummary(BaseModel):
    price: str
    bookableSeats: Union[int, str]
    airlines: str
    itineraries: List[FlightItinerary]


class FlightOffersResponse(RootModel[List[FlightOfferSummary]]):  # ✅
    pass


# ───────── 2. find-cheapest-dates ─────────
class CheapestDateResult(BaseModel):
    route: str
    carrier: str
    departure: str
    arrival: str
    price: str
    offer_id: str


# ───────── 3. analyze-flight-prices ─────────
class PriceMetric(BaseModel):
    quartileRanking: str
    amount: float


class PriceAnalysisContent(BaseModel):
    message: str
    origin: str
    destination: str
    departureDate: str
    currencyCode: str
    oneWay: bool
    priceMetrics: List[PriceMetric]


# ───────── 4. get-flight-details ─────────
class SegmentDetail(BaseModel):
    from_: str = Field(..., alias='from')
    to: str
    carrier: str


class FlightDetailsResponse(BaseModel):
    price: str
    bookableSeats: Union[int, str]
    airlines: str
    segments: List[SegmentDetail]


# ───────── 5. weather (기존 유지) ─────────
class WeatherItem(BaseModel):
    id: int
    main: str
    description: str
    icon: str


class Clouds(BaseModel):
    all: int


class Wind(BaseModel):
    speed: float
    deg: int
    gust: float


class SysPod(BaseModel):
    pod: Literal["d", "n"]


class MainInfo(BaseModel):
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    sea_level: int
    grnd_level: int
    humidity: int
    temp_kf: float


class ForecastEntry(BaseModel):
    dt: int
    main: MainInfo
    weather: List[WeatherItem]
    clouds: Clouds
    wind: Wind
    visibility: int
    pop: float
    sys: SysPod
    dt_txt: datetime


class Coord(BaseModel):
    lat: float
    lon: float


class CityInfo(BaseModel):
    id: int
    name: str
    coord: Coord
    country: str
    population: int
    timezone: int
    sunrise: int
    sunset: int


class WeatherForecastResponse(BaseModel):
    cod: str
    message: int
    cnt: int
    list: List[ForecastEntry]
    city: CityInfo


# ───────── 6. SCHEMA_MAP ─────────

SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "search-flights": FlightOffersResponse,
    "find-cheapest-dates": CheapestDateResult,
    "analyze-flight-prices": PriceAnalysisContent,
    "get-flight-details": FlightDetailsResponse,
    "get_weather": WeatherForecastResponse,
}
