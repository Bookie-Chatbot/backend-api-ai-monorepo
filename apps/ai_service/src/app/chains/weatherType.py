from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


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