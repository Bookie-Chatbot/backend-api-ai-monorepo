from pydantic import BaseModel
from typing import Dict, Any

class ai_responseCreate(BaseModel):
    user_id: int
    intent: str
    contents: Dict[str, Any]