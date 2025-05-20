from typing import List, Literal
from pydantic import BaseModel

class DestRecommendCard(BaseModel):
    city: str
    score: float
    photos: List[str]
    description: str
    hashtags: List[str]

class DestRecommendContent(BaseModel):
    intent: Literal["DEST_RECOMMEND"]
    cards: List[DestRecommendCard]
    message: str

# 예시
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

    content = DestRecommendContent.parse_obj(raw["contents"])
    print(content.cards[0].city)  # 제주도
