from pydantic import BaseModel, Field
from typing import Literal



class ContentsList(BaseModel):
    message: str

class IntentFallbackContent(BaseModel):
    intent: Literal["INTENT_FALLBACK"]= Field(..., exclude=True)
    contents: ContentsList


{
  "intent": "INTENT_FALLBACK",
  "contents": {
    "message": "죄송하지만, 요청을 이해하지 못했습니다. 다시 한 번 알려주시겠어요?"
  }
}
