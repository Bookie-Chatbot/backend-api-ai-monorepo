from pydantic import BaseModel, Field
from typing import Literal

class GeneralChatContent(BaseModel):
    intent: Literal["GENERAL_CHAT"]= Field(..., exclude=True)
    message: str

{
  "intent": "GENERAL_CHAT",
  "contents": {
    "message": "안녕하세요! 무엇을 도와드릴까요?"
  }
}
