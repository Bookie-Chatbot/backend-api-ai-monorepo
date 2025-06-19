# ── chains/alert_price_drop.py ──────────────────────────────────
from __future__ import annotations

import json
from typing import Any, Dict

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableMap
from langchain_core.messages import BaseMessage

# Pydantic 스키마
from packages.chatbot_contents.alert_dispatch import AlertDispatchContent

load_dotenv()

# ────────────────────────────────────────────────────────────────
# 0. 파서 & 헬퍼
# ────────────────────────────────────────────────────────────────
price_drop_parser = PydanticOutputParser(pydantic_object=AlertDispatchContent)

def _strip_fence(txt: str) -> str:
    # 혹시 ```json … ``` 로 감싸져 있으면 제거
    return txt.strip().lstrip("```json").rstrip("```").strip()

def _post_parse(text: str) -> AlertDispatchContent:
    """
    1) 코드펜스 제거
    2) Pydantic 파싱
    3) JSON 직렬화 테스트
    """
    cleaned = _strip_fence(text)
    parsed = price_drop_parser.parse(cleaned)
    # 직렬화 가능 여부 확인
    json.dumps(parsed.model_dump(mode="python"), ensure_ascii=False)
    return parsed

# ────────────────────────────────────────────────────────────────
# 1. RunnableMap: 입력값 추출
# ────────────────────────────────────────────────────────────────
price_drop_chain = (
    RunnableMap({
        "question": lambda inp: inp["question"],
        "format_instructions": lambda inp: inp["format_instructions"],
        "chat_history": lambda inp: inp.get("chat_history", []),
    })
    # ────────────────────────────────────────────────────────────────
    # 2. Prompt → LLM 호출
    # ────────────────────────────────────────────────────────────────
    | PromptTemplate.from_template(
       "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
"json의 contents.message 안에 설명을 작성해주고, ‘부엉이 부키’라는 귀여운 부엉이처럼 대답하면서, 모든 답변 끝에 ‘부키!’를 붙여줘."
"사용자가 본인이 원하는 price_threshold를 제시하지 않으면, selling_price에서 10% 할인된 가격을 100의 자리에서 내린 값을 default price_threshold로 생각해."
"channel은 사용자의 query와 상관 없이 무조건 email이야."
"origin과 dest에는 공항 코드를 ICN / KIX / HND / LAX와 같이 제공해주고,"
"selling_price에는 만약, dest가 KUL이면, 168000원으로 해주고, KIX면, 37800원으로 고정해줘. chat history에서, 가장 최근 timestamp cheapest date intent 기록에서 응답으로 온 항공권의 price를 기입해줘"
"price_threshold에는 사용자가 현재 question으로 준 임계치 가격을 추가해줘(예시 : 사용자 질문 : 7월 1일 오사카행 비행기가 3만원 이하로 떨어지면 알림해줘 ->  price_threshold는 30000원으로 설정한다."
"departure_date는, 사용자가 question에서 준 data를 추가해줘 년도는 무조건 2025년이고 형식은 2025-MM-DD야"
        "{format_instructions}\n"
        "사용자의 현재 질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
    )
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    # ────────────────────────────────────────────────────────────────
    # 3. AIMessage → str
    # ────────────────────────────────────────────────────────────────
    | StrOutputParser()
    # ────────────────────────────────────────────────────────────────
    # 4. str → Pydantic 모델
    # ────────────────────────────────────────────────────────────────
    | RunnableLambda(lambda text: _post_parse(text))
)

# ────────────────────────────────────────────────────────────────
# 테스트용 진입점
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    example = price_drop_chain.invoke({
        "question": "맨 마지막거 50만원 아래로 떨어지면 알려줘",
        "format_instructions": price_drop_parser.get_format_instructions(),
        "chat_history": [
            {"role": "assistant", "content": "여행지 카드를 추천해드렸어요. 다음 중 원하는 게 있나요?"}
        ],
    })
    # Pydantic 모델이므로 .contents 접근이 안전합니다.
    print("Intent:  ", example.intent)
    print("Message: ", example.contents.message)
    print("Channel: ", example.contents.channel)
    print("Payload: ", example.contents.payload)
