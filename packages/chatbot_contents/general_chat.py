from pydantic import BaseModel

class GeneralChatContent(BaseModel):
    message: str

{
  "intent": "GENERAL_CHAT",
  "contents": {
    "message": "안녕하세요! 무엇을 도와드릴까요?"
  }
}
