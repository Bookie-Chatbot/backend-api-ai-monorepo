from datetime import datetime, date
from typing import List, Optional, Dict, Any, Literal

from pydantic import BaseModel, Field

class SlotClarificationContent(BaseModel):
    intent: Literal["SLOT_CLARIFICATION"]= Field(..., exclude=True)
    message: str
    missingSlots: List[str]



{
  "intent": "SLOT_CLARIFICATION",
  "contents": {
    "message": "어느 구간의 항공권을 찾으시나요?",
    "missingSlots": ["origin","destination"]
  }
}
