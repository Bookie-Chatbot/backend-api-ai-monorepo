from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PricePredictionContent(BaseModel):
    origin: str
    destination: str
    departureDate: str
    predictionDate: str
    currency: str
    predictedPrice: float
    lowerBound: float
    upperBound: float
    confidence: float  # 0.0–1.0

{
  "intent": "PRICE_PREDICTION",
  "contents": {
    "origin": "ICN",
    "destination": "JFK",
    "departureDate": "2025-07-01",
    "predictionDate": "2025-05-20",
    "currency": "KRW",
    "predictedPrice": 980000.0,
    "lowerBound": 900000.0,
    "upperBound": 1100000.0,
    "confidence": 0.82
  }
}
