"""
MCP 전용 서브체인 모음 – DEBUG 버전
────────────────────────────────────────────────────────────
• prints:  타입·repr·dict 변환 여부·json 직렬화 성공 여부
"""
from __future__ import annotations

# -- 표준 라이브러리 ─────────────────────────────────────────
import asyncio
import json
import os
import re
from pprint import pprint
from typing import Any, Dict
from chatbot_contents.intents import IntentOnly, Intent


# -- 서드파티 ────────────────────────────────────────────────
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# -- 우리 코드 ──────────────────────────────────────────────
from chatbot_contents.common import (
    PriceSearchContent,
    PriceAnalysisContent,
    CheapestDateContent,
    WeatherSummaryContent,
)
from runs.test.mcp_client import ask_mcp
from .utils import to_json

# ╭───────────────────────────╮
# │  전역 설정 &  헬퍼 함수   │
# ╰───────────────────────────╯
DEBUG_VERBOSE: bool = True  # 로그 토글


def dbg(label: str, value: Any) -> None:
    """간단한 디버그 프린터 – 타입 / id / 본문 프린트"""
    if not DEBUG_VERBOSE:
        return
    print(f"[DBG] {label}: type={type(value)} id={id(value)}")
    if isinstance(value, (dict, list)):
        pprint(value, depth=3, compact=True, width=110)
    else:
        print("      ", repr(value)[:500])


# ── fence 제거 & 평탄화 ──────────────────────────────────

def _to_plain(obj: Any) -> Any:
    if isinstance(obj, BaseMessage):
        return obj.content
    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}
    return obj


def strip_fence(txt: Any) -> Any:
    txt = _to_plain(txt)
    if not isinstance(txt, str):
        return txt
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", txt, flags=re.I | re.M)


# ── dumps 래퍼 – 어디서든 사용 ─────────────────────────────

def safe_dumps(obj: Any, *, label: str = "unknown") -> str:
    """json.dumps + 오류 위치를 상세히 로깅"""
    try:
        return json.dumps(obj, default=to_json, ensure_ascii=False, indent=2)
    except TypeError as err:
        print(f"[!!!] json.dumps 실패({label}) → {err}")
        if isinstance(obj, dict):
            for k, v in obj.items():
                try:
                    json.dumps(v, default=to_json)
                except TypeError as sub_err:
                    print(f" └─ key={k!r} bad_type={type(v)} err={sub_err}")
        raise


# ╭───────────────────────────╮
# │   파서 인스턴스 미리 생성 │
# ╰───────────────────────────╯
price_search_parser:  PydanticOutputParser = PydanticOutputParser(pydantic_object=PriceSearchContent)
price_analysis_parser: PydanticOutputParser = PydanticOutputParser(pydantic_object=PriceAnalysisContent)
cheapest_date_parser:  PydanticOutputParser = PydanticOutputParser(pydantic_object=CheapestDateContent)
weather_parser:        PydanticOutputParser = PydanticOutputParser(pydantic_object=WeatherSummaryContent)


# ╭───────────────────────────╮
# │   체인 생성 헬퍼          │
# ╰───────────────────────────╯

def _mk_chain(parser: PydanticOutputParser):
    """MCP 호출 → LLM 재포맷 → Pydantic 검증 파이프라인"""

    # STEP-1) LangGraph MCP 호출 -------------------------------------------------
    def _call_mcp(inputs: Dict[str, Any]) -> Dict[str, Any]:
        dbg("inputs(raw)", inputs)

        raw = asyncio.run(ask_mcp(question=inputs["question"]))
        dbg("ask_mcp(raw)", raw)

        txt = strip_fence(raw)
        dbg("ask_mcp(stripped)", txt)

        raw_json_str = safe_dumps(txt, label="txt")

        # chat_history 직렬화 안전화
        raw_hist = inputs.get("chat_history", [])
        dbg("chat_history(raw)", raw_hist)
        hist = [to_json(h) for h in raw_hist]
        dbg("chat_history(json-safe)", hist)
        _ = safe_dumps(hist, label="hist")  # 직렬화 성공 여부만 확인

        return {
            "question": inputs["question"],
            "chat_history": hist,
            "format_instructions": inputs["format_instructions"],
            "raw_json": raw_json_str,
        }

    # STEP-2) LLM: raw → 스키마 맞춤 JSON ---------------------------------------
    reformat_prompt = PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에 2줄 설명을 작성하고 항상 ‘부키!’로 끝내. "
        "intent 가 WEATHER_SUMMARY 면 raw_json 의 긴 메시지도 생략하지 말고 그대로 넣어.\n"
        "찾은 결과 : raw_json:을 가지고, 결과를 아래 JSON 스키마에 맞춰 반환해줘.\n"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
        "raw_json: {raw_json}\n"
    )
    llm_chain = reformat_prompt | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    # STEP-3) Pydantic 파싱 + 직렬화 검증 ---------------------------------------
    def _post_parse(text: str):
        dbg("LLM_output(raw str)", text)
        parsed = parser.parse(text)
        dbg("Pydantic(parsed)", parsed)

        # 직렬화 체크 (👉 이후 단계에서 또 실패 않는지 조기 확인용)
        json_blob = json.dumps(parsed, default=to_json, ensure_ascii=False)
        dbg("json_blob", json_blob)
        return parsed

    # Runnable 파이프라인 -------------------------------------------------------
    return (
        RunnableLambda(_call_mcp)   # network I/O
        | llm_chain                 # OpenAI re-formatting
        | StrOutputParser()         # AIMessage → str
        | RunnableLambda(_post_parse)
    )


# ╭───────────────────────────╮
# │   Intent → 체인 매핑      │
# ╰───────────────────────────╯
MCP_INTENT_MAP = {
    Intent.PRICE_SEARCH:    (_mk_chain(price_search_parser),   price_search_parser),
    Intent.PRICE_ANALYSIS:  (_mk_chain(price_analysis_parser), price_analysis_parser),
    Intent.CHEAPEST_DATE:   (_mk_chain(cheapest_date_parser),  cheapest_date_parser),
    Intent.WEATHER_SUMMARY: (_mk_chain(weather_parser),        weather_parser),
}


# .env 로드 (필요 시) -----------------------------------------------------------
load_dotenv()