from typing import Union
from pydantic import BaseModel, Field

# import intents and individual content models
from .price_search import PriceSearchContent
from .price_prediction import PricePredictionContent
from .price_analysis import PriceAnalysisContent
from .policy_qa import PolicyQAContent
from .dest_recommend import DestRecommendContent
from .hotel_summary import HotelSummaryContent
from .weather_summary import WeatherSummaryContent
from .alert_dispatch import AlertDispatchContent
from .general_chat import GeneralChatContent
from .intent_fallback import IntentFallbackContent
from .slot_clarification import SlotClarificationContent
from .session import SessionNewContent, SessionContinueContent
from ..intents import Intent

# Discriminated Union 모델
class ChatbotMessage(BaseModel):
    intent: Intent = Field(..., description="어떤 Intent인지")
    contents: Union[
        PriceSearchContent,
        PricePredictionContent,
        PriceAnalysisContent,
        PolicyQAContent,
        DestRecommendContent,
        HotelSummaryContent,
        WeatherSummaryContent,
        AlertDispatchContent,
        GeneralChatContent,
        IntentFallbackContent,
        SlotClarificationContent,
        SessionNewContent,
        SessionContinueContent,
    ] = Field(..., discriminator="intent")

# 예시 파싱
if __name__ == "__main__":
    raw = {
        "intent": "DEST_RECOMMEND",
        "contents": {
            "cards": [
                {
                    "city": "제주도",
                    "score": 0.9,
                    "photos": ["https://..."],
                    "description": "제주도 설명",
                    "hashtags": ["#korea", "#travel"]
                }
            ],
            "message": "인스타그램 핫플레이스..."
        }
    }

    msg = ChatbotMessage.parse_obj(raw)
    assert isinstance(msg.contents, DestRecommendContent)
    print(msg.intent)  # → "DEST_RECOMMEND"
    print(msg.contents)
    print(msg.contents.cards[0].city)  # → "제주도"
