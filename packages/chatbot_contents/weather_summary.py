from typing import Optional, Literal, List
from pydantic import BaseModel, Field


class WeatherSummaryContent(BaseModel):
    intent: Literal["WEATHER_SUMMARY"]= Field(..., exclude=True)
    location: str
    date: str
    summary: str
    alerts: Optional[List[str]]


{
  "intent": "WEATHER_SUMMARY",
  "contents": {
    "location": "Busan",
    "date": "2025-05-21",
    "summary": "구름 조금, 최고 23°C / 최저 15°C",
    "alerts": ["강풍 주의", "해상 풍랑 경보"]
  }
}
