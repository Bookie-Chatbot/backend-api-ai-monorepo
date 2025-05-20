from pydantic import BaseModel

class GeneralChatContent(BaseModel):
    message: str
