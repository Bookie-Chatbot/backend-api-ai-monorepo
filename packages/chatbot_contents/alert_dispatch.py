from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from typing_extensions import Literal
from datetime import date

class PayloadList(BaseModel):
    origin: str
    dest: str
    departure_date: str
    selling_price: int
    price_threshold: int
    deadline: Optional[str] = None  # Optional로 변경, 기본값은 None

class ContentList(BaseModel):
    message: str
    eventType: Literal["price_drop","wx_risk","cancel_deadline"]
    channel: Literal["email","kakao"]
    userId: str
    emailId: str
    payload: PayloadList

class AlertDispatchContent(BaseModel):
    intent: Literal["ALERT_DISPATCH"]
    contents: ContentList




if __name__ == "__main__":
    raw = {"intent": "ALERT_DISPATCH",
           "eventType": "price_drop",
           "channel": "email",
           "userId": "user-1234",
           "emailId": "hello@gmail.com",
           "message": "1300000원 이하로 떨어지면 알림을 받으시길 원하시나요?",
           "payload": {
              "origin": "서울",
              "dest": "뉴욕",
              "departure_date": "2025-06-25",
              "selling_price": 15000000,
              "price_threshold": 1300000,
              "deadline": "2025-06-18"
            }
    }

    content = AlertDispatchContent.model_validate(raw)
    print(content.payload)



# class PriceDropPayload(BaseModel):
#     route: str               # ex. "ICN→LAX"
#     oldPrice: float          # 기존 가격
#     newPrice: float          # 현재(혹은 목표) 가격
#     currency: str            # ex. "KRW"
#     dropPercent: float       # ex. 7.7

# class AlertDispatchPriceDrop(BaseModel):
#     intent: Literal["ALERT_DISPATCH_PRICE_DROP"] = Field(..., exclude=True)
#     channel: Literal["email", "kakao"]
#     userId: str
#     message: str
#     payload: PriceDropPayload

