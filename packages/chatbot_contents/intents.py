# chatbot_contents/intents.py
from pydantic import BaseModel
from enum import Enum

class Intent(str, Enum):
    PRICE_SEARCH        = "PRICE_SEARCH"
    PRICE_PREDICTION    = "PRICE_PREDICTION"
    PRICE_ANALYSIS      = "PRICE_ANALYSIS"
    POLICY_QA           = "POLICY_QA"
    DEST_RECOMMEND      = "DEST_RECOMMEND"
    HOTEL_SUMMARY       = "HOTEL_SUMMARY"
    WEATHER_SUMMARY     = "WEATHER_SUMMARY"
    ALERT_DISPATCH      = "ALERT_DISPATCH"
    GENERAL_CHAT        = "GENERAL_CHAT"
    INTENT_FALLBACK     = "INTENT_FALLBACK"
    SLOT_CLARIFICATION  = "SLOT_CLARIFICATION"
   # SESSION_NEW         = "SESSION_NEW"
  #  SESSION_CONTINUE    = "SESSION_CONTINUE"

# chatbot_contents/intents.py
class IntentOnly(BaseModel):
    intent: Intent

    # (1) json.dumps 가 바로 먹히도록 key/value 를 yield
    def __iter__(self):
        # {"intent": "PRICE_SEARCH"} 처럼 직렬화되도록
        yield from {"intent": self.intent.value}.items()

    # (2) pydantic 의 V1 · V2 모두를 위해 json_encoders 도 명시
    model_config = {
        "json_encoders": {Intent: lambda v: v.value}
    }
