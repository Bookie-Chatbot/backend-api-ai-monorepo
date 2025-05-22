from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from typing_extensions import Literal

class AlertDispatch(BaseModel):
    intent: Literal["ALERT_DISPATCH"]= Field(..., exclude=True)
    eventType: Literal["price_drop","wx_risk","cancel_deadline"]
    channel: Literal["email","kakao"]
    userId: Optional[str]
    payload: dict

class ContentsList(BaseModel):
    message: str
    contents : AlertDispatch


class AlertDispatchContent(BaseModel):
    intent: Literal["ALERT_DISPATCH"]= Field(..., exclude=True)
    contents: ContentsList



    def validate_payload(self) -> bool:
      required_keys = {"route", "oldPrice", "newPrice", "currency", "dropPercent"}
      return required_keys.issubset(self.contents.payload.keys())

{
  "intent": "ALERT_DISPATCH",
  "contents": {
    "userId": "user-1234",
    "eventId": "1",
    "message": "알림을 받으실 이메일을 입력해주세요.",
    "eventType": "price_drop",
    "channel": "email",
    "payload": {
      "route": "ICN→LAX",
      "oldPrice": 1300000,
      "newPrice": 1200000,
      "currency": "KRW",
      "dropPercent": 7.7
    }
  }
}



class PriceDropPayload(BaseModel):
    route: str               # ex. "ICN→LAX"
    oldPrice: float          # 기존 가격
    newPrice: float          # 현재(혹은 목표) 가격
    currency: str            # ex. "KRW"
    dropPercent: float       # ex. 7.7

class AlertDispatchPriceDrop(BaseModel):
    intent: Literal["ALERT_DISPATCH_PRICE_DROP"] = Field(..., exclude=True)
    channel: Literal["email", "kakao"]
    userId: str
    message: str
    payload: PriceDropPayload

