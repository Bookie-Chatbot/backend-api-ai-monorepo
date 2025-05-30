# ── DEST_RECOMMEND 서브체인 ──────────────────────────────────
from __future__ import annotations

import json, os, re
from typing import Any, Dict

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableMap, RunnableLambda

# 프로젝트-로컬
from packages.chatbot_contents.dest_recommend import DestRecommendContent

load_dotenv()

# ─────────────────────────────────────────────────────────────
# 0.  Pydantic 파서 & 헬퍼
# ─────────────────────────────────────────────────────────────
dest_recommend_parser = PydanticOutputParser(pydantic_object=DestRecommendContent)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.I | re.M)


def _strip_fence(txt: str) -> str:
    return _FENCE_RE.sub("", txt).strip()


def _post_parse(text: str) -> DestRecommendContent:
    """코드블럭·개행을 걷어낸 뒤 Pydantic 파싱 + 폴백."""
    clean = _strip_fence(text)
    try:
        return dest_recommend_parser.parse(clean)
    except Exception:
        # 최후 보루 – message 에 그대로 집어넣기
        return DestRecommendContent(contents={"message": clean, "cards": []})


post_parse = RunnableLambda(_post_parse)

# ─────────────────────────────────────────────────────────────
# 1.  고정 pre_query – 카드 목록 샘플
# ─────────────────────────────────────────────────────────────
_PRE_QUERY: Dict[str, Any] = {
    "contents": {
        "cards": [
            {
                "city": "파리",
                "score": 9.5,
                "photos": [
                    "https://asset-prod.france.fr/xlarge_Eiffel_Tower_at_sunset_in_Paris_France_Romantic_travel_background_Man79_Adobe_Stock_8aa81830ce.jpeg",
                    "https://res.klook.com/image/upload/c_fill,w_1265,h_712/q_80/w_80,x_15,y_15,g_south_west,l_Klook_water_br_trans_yhcmh3/activities/cg79lzqlojzwcshghlo6.webp"
                ],
                "hashtags": ["#파리", "#여행", "#에펠탑"],
                "description": "사랑의 도시, 파리는 에펠탑과 루브르 박물관으로 유명해!"
            },
            {
                "city": "로마",
                "score": 9.0,
                "photos": [
                    "https://d1blyo8czty997.cloudfront.net/tour-photos/20431/800x800/171866544647398194.87345398862.jpg",
                    "https://res.klook.com/image/upload/c_fill,w_1265,h_712/q_80/w_80,x_15,y_15,g_south_west,l_Klook_water_br_trans_yhcmh3/activities/hozvdaykwbjkjc0jl5nz.webp"
                ],
                "hashtags": ["#로마", "#역사", "#여행"],
                "description": "역사와 문화가 가득한 로마는 콜로세움과 바티칸으로 유명해!"
            },
            {
                "city": "바르셀로나",
                "score": 8.8,
                "photos": [
                    "https://www.agoda.com/wp-content/uploads/2024/09/View-of-the-Sea-in-Barcelona-1244x700.jpg",
                    "https://cdn.tripzaza.com/ko/destinations/wp-content/uploads/2017/09/Barcelona-1-Sagrada_Fam--lia-e1504419641187.jpg"
                ],
                "hashtags": ["#바르셀로나", "#가우디", "#예술"],
                "description": "가우디의 작품이 가득한 바르셀로나는 예술과 해변이 매력적이야!"
            }
        ],
        "message": "서유럽의 멋진 여행지를 추천해줄게! 부키!🦉"
    }
}

# ─────────────────────────────────────────────────────────────
# 2.  프롬프트 & 체인
# ─────────────────────────────────────────────────────────────
_PROMPT = PromptTemplate.from_template(
    "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
    "아래 pre_query JSON을 그대로 사용하되, "
    "contents.message 를 두 줄 설명으로 갱신하고 항상 ‘부키!🦉’로 끝내. "
    "마크다운 코드블럭을 쓰지 말고 **순수 JSON** 만 반환해. \n"
    "{format_instructions}\n"
    "pre_query: {pre_query}\n"
)

_llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

dest_recommend_chain = (
    RunnableMap({
        "pre_query": lambda _: json.dumps(_PRE_QUERY, ensure_ascii=False),
        "format_instructions": lambda _: dest_recommend_parser.get_format_instructions(),
    })
    | _PROMPT
    | _llm
    | StrOutputParser()
    | post_parse
)

# 테스트 실행
if __name__ == "__main__":
    result = dest_recommend_chain.invoke({"question": "유럽 여행지 추천해줘"})
    print(json.dumps(result.model_dump(mode="python"), indent=2, ensure_ascii=False))
