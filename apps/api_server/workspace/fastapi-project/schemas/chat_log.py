from pydantic import BaseModel
from typing import Any
from datetime import datetime


class ChatLogCreate(BaseModel):
    session_id: str
    role: str  # "user" or "bot"
    message: str

class ChatLogRead(BaseModel):
    session_id: int
    user_id: int
    message: str
    answer: Any
    created_at: datetime

    class Config:
        orm_mode = True

