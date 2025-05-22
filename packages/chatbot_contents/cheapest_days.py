from typing import List, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class CheapDays(BaseModel):
    route: str
    carrier: str
    departure: datetime
    arrival: datetime
    price: int


class ContentsList(BaseModel):
    message: str
    cards: List[CheapDays]


class CheapestDaysContent(BaseModel):
    intent: Literal["CHEAPEST_DAYS"] = Field(..., exclude=True)
    contents: ContentsList