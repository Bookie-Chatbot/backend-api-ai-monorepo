from pydantic import BaseModel

class ChatLogCreate(BaseModel):
    session_id: str
    role: str  # "user" or "bot"
    message: str