from datetime import datetime, date
from typing import List, Optional, Dict, Any, Literal

from pydantic import BaseModel, Field


class ContentsList(BaseModel):
    message: str
    missingSlots: List[str]

class SlotClarificationContent(BaseModel):
    intent: Literal["SLOT_CLARIFICATION"]= "SLOT_CLARIFICATION"
    contents: ContentsList


{
  "intent": "SLOT_CLARIFICATION",
  "contents": {
    "message": "출발 도시를 알려주세요! 예: 서울, 부산, 제주도",
    "missingSlots": ["origin"]
  }
}
