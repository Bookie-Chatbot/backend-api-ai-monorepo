from datetime import datetime, date
from typing import List, Optional, Dict, Any, Literal

from pydantic import BaseModel, Field

class PriceAnalysisContent(BaseModel):
    intent: Literal["PRICE_ANALYSIS"]
    message: str
    origin: str
    destination: str
    departureDate: str
    currencyCode: str
    oneWay: bool
    priceMetrics: List[dict]

{
    "intent": "PRICE_ANALYSIS",
    "contents": {
        "message": "가격 분석 결과입니다.",
        "origin": "ICN",
        "destination": "LAX",
        "departureDate": "2025-06-15",
        "currencyCode": "KRW",
        "oneWay": "false",
        "priceMetrics": [
            {
                "metricName": "averagePrice",
                "metricValue": 1200000.0
            },
            {
                "metricName": "lowestPrice",
                "metricValue": 1000000.0
            },
            {
                "metricName": "highestPrice",
                "metricValue": 1500000.0
            }
        ]
    }
}