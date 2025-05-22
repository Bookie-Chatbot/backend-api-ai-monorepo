"""
MCP-전용 서브체인 모음.
다른 코드에 영향 없도록 _INTENT_MAP 만 외부에 노출합니다.
"""
import asyncio
import json
import os
from pprint import pprint
from dotenv import load_dotenv

from langchain_core.runnables import RunnableLambda
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from chatbot_contents.common import (
    PriceSearchContent,
    PriceAnalysisContent,
    CheapestDateContent,
    WeatherSummaryContent,
)
from runs.test.mcp_client import ask_mcp   # ← async wrapper around LangGraph ReAct agent

load_dotenv()

# ── 1) 파서 선언 ────────────────────────────────────────────── #
price_search_parser   = PydanticOutputParser(pydantic_object=PriceSearchContent)
price_analysis_parser = PydanticOutputParser(pydantic_object=PriceAnalysisContent)
cheapest_date_parser  = PydanticOutputParser(pydantic_object=CheapestDateContent)
weather_parser        = PydanticOutputParser(pydantic_object=WeatherSummaryContent)

# ── 2) MCP → LLM(재포맷) → Pydantic 체인 팩토리 ──────────────── #
def _mk_chain(parser: PydanticOutputParser):
    """
    ① ask_mcp → raw dict                            (network I/O)
    ② LLM: raw dict  → JSON ★스키마 정규화            (OpenAI)
    ③ parser.parse → Pydantic 강제 검증               (local)
    """

    # STEP-1: MCP 호출 + 디버깅 로그 + safe JSON-dump
    def _call_mcp(inputs: dict):
        raw = asyncio.run(ask_mcp(question=inputs["question"]))   # blocking→sync
        print("[_mk_chain] 🏗  ask_mcp raw ↓")
        pprint(raw, depth=2, compact=True, width=120)

        # datetime 객체를 ISO-8601 문자열로 변환해 직렬화 실패를 차단
        raw_json_str = json.dumps(raw, ensure_ascii=False, indent=2, default=str)

        return {
            "question":            inputs["question"],
            "chat_history":        inputs.get("chat_history", []),
            "format_instructions": inputs["format_instructions"],
            "raw_json":            raw_json_str,
        }

    # STEP-2: LLM 재포맷 → 의도별 JSON 스키마
    reformat_prompt = PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에 2줄 설명을 작성하고, 항상 ‘부키!’로 끝내. "
        "만약 intent가 WEATHER_SUMMARY이면 raw_json의 긴 메시지도 생략하지 말고 그대로 넣어줘.\n"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
        "아래 JSON을 스키마에 맞게 변환해:\n```json\n{raw_json}\n```"
    )
    llm_chain = reformat_prompt | ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0
    )

    # STEP-3: Pydantic 강제 파싱 (실패 시 예외 throw)
    def _force_parse(text: str):
        return parser.parse(text)

    # 전체 Runnable 파이프라인
    return (
        RunnableLambda(_call_mcp)   # dict with 4 keys
        | llm_chain                 # JSON string
        | RunnableLambda(_force_parse)
    )

# ── 3) Intent ↔ 체인 맵 ─────────────────────────────────────── #
MCP_INTENT_MAP = {
    "PRICE_SEARCH":    (_mk_chain(price_search_parser),   price_search_parser),
    "PRICE_ANALYSIS":  (_mk_chain(price_analysis_parser), price_analysis_parser),
    "CHEAPEST_DATE":   (_mk_chain(cheapest_date_parser),  cheapest_date_parser),
    "WEATHER_SUMMARY": (_mk_chain(weather_parser),        weather_parser),
}
