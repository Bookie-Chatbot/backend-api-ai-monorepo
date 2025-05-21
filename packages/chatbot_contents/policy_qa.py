from datetime import datetime, date
from typing import List, Optional, Dict, Any,Literal

from pydantic import BaseModel, Field

class PolicyReference(BaseModel):
    source: str   # ex. PDF 파일명 또는 URL
    page: Optional[int]


class PolicyQA(BaseModel):
    intent: Literal["POLICY_QA"]= Field(..., exclude=True)
    question: str
    answer: str
    references: List[PolicyReference]


class ContentsList(BaseModel):
    message: str
    cards: List[PolicyQA]

class PolicyQAContent(BaseModel):
    intent: Literal["POLICY_QA"]= Field(..., exclude=True)
    contents: ContentsList



{
  "contents": {
    "message": "구매 후 24시간 이내에는 전액 환불이 가능하며, 출발 7일 전까지는 30,000원, 7일 이내에는 50,000원의 변경 수수료가 부과됩니다. 환불 요청 시에는 영업일 기준 5~7일 내에 결제하신 카드사로 환불이 완료됩니다.",
    "cards": [
      {
        "question": "항공권을 구매 후 24시간 이내에 취소하면 환불이 가능한가요?",
        "answer": "네, 항공권 구매 후 24시간 이내에 취소 요청 시 전액 환불이 가능합니다. 단, 구매 시점 기준 운임 규정에 별도 예외 조항이 없는 경우에 한합니다.",
        "references": [
          {
            "source": "flight_policy.pdf",
            "page": 3
          }
        ]
      },
      {
        "question": "예약한 항공권의 출발 날짜를 변경하려면 수수료가 있나요?",
        "answer": "출발 7일 전까지 변경 요청 시 30,000원, 출발 7일 이내에는 50,000원의 변경 수수료가 부과됩니다.",
        "references": [
          {
            "source": "flight_policy.pdf",
            "page": 5
          }
        ]
      },
      {
        "question": "항공권 환불 처리 기간은 얼마나 걸리나요?",
        "answer": "취소 요청일로부터 영업일 기준 5~7일 이내에 결제하신 카드사로 환불이 완료됩니다.",
        "references": [
          {
            "source": "https://airline.example.com/policy/refund",
            "page": ""
          }
        ]
      }
    ]
  }
}
