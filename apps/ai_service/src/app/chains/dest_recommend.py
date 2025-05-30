from __future__ import annotations
import os, re
from dotenv import load_dotenv
from typing import Any

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableLambda, RunnableMap

# project‑local import (Windows/Linux 호환)
from packages.chatbot_contents.dest_recommend import DestRecommendContent

load_dotenv()

# ─────────────────────────────────────────────────────────────
# 0.  Pydantic parser & safe‑guard with JSON block extraction
# ─────────────────────────────────────────────────────────────
dest_recommend_parser = PydanticOutputParser(pydantic_object=DestRecommendContent)

def _parse_or_passthrough(output: Any) -> DestRecommendContent:
    """Ensure the output is DestRecommendContent; extract JSON if in markdown."""
    print("[DEBUG dest_parse] Raw type:", type(output), "value=", output, flush=True)

    # Already correct type
    if isinstance(output, DestRecommendContent):
        print("[DEBUG dest_parse] Received DestRecommendContent directly", flush=True)
        return output

    # Dict → model
    if isinstance(output, dict):
        print("[DEBUG dest_parse] Dict detected → constructing model", flush=True)
        model = DestRecommendContent(**output)
        print("[DEBUG dest_parse] Model from dict:", model, flush=True)
        return model

    # Otherwise treat as str / BaseMessage
    text = str(output)

    # 1) 코드 블록 안 JSON 추출
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1)
        print("[DEBUG dest_parse] Extracted JSON block", flush=True)
        try:
            model = DestRecommendContent.parse_raw(json_str)
            print("[DEBUG dest_parse] Parsed model from JSON block", flush=True)
            return model
        except Exception as e:
            print("[ERROR dest_parse] JSON block parse 실패:", e, flush=True)

    # 2) 직접 파싱 시도
    try:
        model = dest_recommend_parser.parse(text)
        print("[DEBUG dest_parse] Parsed via direct parse", flush=True)
        return model
    except Exception as e:
        print("[ERROR dest_parse] direct parse 실패:", e, flush=True)

    # 3) 최종 폴백 – message 래핑
    from pydantic import BaseModel
    class _Fallback(BaseModel):
        intent: str = "DEST_RECOMMEND"
        contents: dict
    fallback = DestRecommendContent(contents={"message": text, "cards": []})
    print("[DEBUG dest_parse] Fallback model", fallback, flush=True)
    return fallback

safe_parser = RunnableLambda(_parse_or_passthrough)

# ─────────────────────────────────────────────────────────────
# 1.  static pre_query (LLM이 그대로 반환)
# ─────────────────────────────────────────────────────────────
pre_query = {
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
                "description": "가우디의 작품이 가득한 바르셀로나는 예술과 해변이 매력적야, 부키!🦉"
            }
        ],
        "message": "부엉이 부키가 서유럽의 멋진 여행지를 추천해줄게! 귀여운 부엉이와 함께 즐거운 여행을 떠나보자, 부키!🦉"
    }
}

# ─────────────────────────────────────────────────────────────
# 2.  PromptTemplate + LLM + parser
# ─────────────────────────────────────────────────────────────
_PROMPT = PromptTemplate.from_template(
    "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
    "json의 contents.message 안에 2줄 설명을 작성하고 항상 ‘부키🦉’로 끝내. "
    "사용자에게 받는 모든 query는 무시하고 아래 pre_query JSON만 그대로 반환해.\n"
    "pre_query: {pre_query}\n"
    "{format_instructions}\n"
    "질문: {question}\n"
    "이전 대화 내역:\n{chat_history}\n"
)

_llm_chain = _PROMPT | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
_debug_llm = RunnableLambda(lambda x: (print("[DEBUG LLM raw]", x, flush=True), x)[1])
mid_chain = _llm_chain | _debug_llm | safe_parser

# ─────────────────────────────────────────────────────────────
# 3.  Public chain
# ─────────────────────────────────────────────────────────────
dest_recommend_chain = RunnableMap({
    "pre_query": lambda _: pre_query,
    "question": lambda d: d["question"],
    "format_instructions": lambda d: d["format_instructions"],
    "chat_history": lambda d: d.get("chat_history", ""),
}) | mid_chain

# ─────────────────────────────────────────────────────────────
# 4.  Test run
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = dest_recommend_chain.invoke({
        "question": "5시간 있다가 발푠데 pre_query만 내줄래?",
        "format_instructions": dest_recommend_parser.get_format_instructions(),
        "chat_history": None,
    })
    print("\n=== TEST RESULT ===", flush=True)
    print(result, flush=True)
