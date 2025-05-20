from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SlotClarificationContent(BaseModel):
    message: str
    missingSlots: List[str]


{
  "intent": "SLOT_CLARIFICATION",
  "contents": {
    "message": "어느 구간의 항공권을 찾으시나요?",
    "missingSlots": ["origin","destination"]
  }
}
