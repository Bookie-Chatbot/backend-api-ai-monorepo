from pydantic import BaseModel
from typing import Any
from datetime import datetime


class MessageCreate(BaseModel):
    user_id: int
    message: str

class MessageRead(BaseModel):
    session_id: int
    user_id: int
    message: str
    answer: Any
    created_at: datetime

    class Config:
        orm_mode = True
