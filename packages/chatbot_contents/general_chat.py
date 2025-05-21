from pydantic import BaseModel, Field
from typing import Literal



class ContentsList(BaseModel):
    message: str

class GeneralChatContent(BaseModel):
    intent: Literal["GENERAL_CHAT"]= Field(..., exclude=True)
    contents: ContentsList

{
  "intent": "GENERAL_CHAT",
  "contents": {
    "message": "안녕하세요! 무엇을 도와드릴까요?"
  }
}
