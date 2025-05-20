from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from typing_extensions import Literal

class AlertDispatchContent(BaseModel):
    intent: Literal["ALERT_DISPATCH"]= Field(..., exclude=True)
    eventType: Literal["price_drop","wx_risk","cancel_deadline"]
    channel: Literal["email","kakao"]
    userId: Optional[str]
    payload: dict


{
  "intent": "ALERT_DISPATCH",
  "contents": {
    "eventType": "price_drop",
    "channel": "email",
    "userId": "user-1234",
    "payload": {
      "route": "ICN→LAX",
      "oldPrice": 1300000,
      "newPrice": 1200000,
      "currency": "KRW",
      "dropPercent": 7.7
    }
  }
}
