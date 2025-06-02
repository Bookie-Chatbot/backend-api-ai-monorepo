from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


class MessageCreate(BaseModel):
    user_id: int
    message: str

class MessageRead(BaseModel):
    session_id: int
    user_id: int
   # message: str
    message: str = Field(strip_whitespace=True)
    answer: Any
    timestamp: datetime
    class Config:
        from_attributes = True  # FastAPI V2에서 'orm_mode' 대신 사용

class MessagesRead(BaseModel):
    user_id: int
    messages: list[MessageRead]

    class Config:
        from_attributes = True  # FastAPI V2에서 'orm_mode' 대신 사용
