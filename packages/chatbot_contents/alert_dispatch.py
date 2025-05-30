from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from typing_extensions import Literal



class AlertDispatchContent(BaseModel):
    intent: Literal["ALERT_DISPATCH"] = "ALERT_DISPATCH"
   # userId:
    channel: Literal["email", "kakao"]
    userId: Optional[str]
    payload: Dict[str, Any]  # payload는 PriceDropPayload로 정의할 수도 있지만, 유연성을 위해 Dict로 둠



"""
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
    intent: Literal["ALERT_DISPATCH_PRICE_DROP"] = "ALERT_DISPATCH_PRICE_DROP"
    channel: Literal["email", "kakao"]
    userId: str
    message: str
    payload: PriceDropPayload

"""