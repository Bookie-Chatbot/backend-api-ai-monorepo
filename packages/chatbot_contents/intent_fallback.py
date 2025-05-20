from pydantic import BaseModel

class IntentFallbackContent(BaseModel):
    message: str


{
  "intent": "INTENT_FALLBACK",
  "contents": {
    "message": "죄송하지만, 요청을 이해하지 못했습니다. 다시 한 번 알려주시겠어요?"
  }
}
