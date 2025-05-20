from datetime import datetime, date
from typing import List, Optional, Dict, Any,Literal

from pydantic import BaseModel, Field

class PolicyReference(BaseModel):
    source: str   # ex. PDF 파일명 또는 URL
    page: Optional[int]


class PolicyQAContent(BaseModel):
    intent: Literal["POLICY_QA"]
    question: str
    answer: str
    references: List[PolicyReference]


{
  "intent": "POLICY_QA",
  "contents": {
    "question": "수하물 초과 수수료는 얼마인가요?",
    "answer": "초과 수하물 1kg당 35,000 KRW가 부과됩니다.",
    "references": [
      {
        "source": "koreanair.pdf",
        "page": 42
      }
    ]
  }
}
