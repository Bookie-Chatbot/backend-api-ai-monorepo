# ── mcp_client.py ───────────────────────────────────────────
import json, re, traceback, os
from pathlib import Path
from typing import Any, Dict

from langchain_core.messages import ToolMessage
from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# ✈️✈️ 당신이 이미 선언해 둔 모델/SCHEMA_MAP 임포트
from .mcpFlight2 import (
    FlightOffersResponse,
    CheapestDateResult,
    PriceAnalysisContent,
    FlightDetailsResponse,
)
from .mcpWeather import WeatherForecastResponse
from langchain_core.messages import AIMessage, BaseMessage

def _to_plain(obj: Any) -> Any:
    """
    ✅  AIMessage            → obj.content
    ✅  list[ ... ]          → 각 원소 재귀 변환
    ✅  dict / pydantic Base → value 재귀 변환
    나머지는 그대로 반환
    """
    if isinstance(obj, AIMessage):
        return obj.content

    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]

    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}

    # pydantic BaseModel 도 dict 로 내려치기
    if isinstance(obj, BaseModel):
        return _to_plain(obj.model_dump())

    return obj


# ────────── 0. 전역 설정 ──────────
ROOT          = Path(__file__).resolve().parent
WEATHER_PORT  = 8010
AMADEUS_PORT  = int(os.getenv("AMADEUS_PORT", 8020))

from datetime import datetime
from pprint import pprint

def _to_serializable(obj):
    """datetime → ISO 문자열, 기타 중첩 구조 재귀 처리"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, list):
        return [_to_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    return obj

# ────────── 1. SCHEMA_MAP ──────────

SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "search-flights":       FlightOffersResponse,
    "find-cheapest-dates":  CheapestDateResult,
    "analyze-flight-prices": PriceAnalysisContent,
    "get-flight-details":   FlightDetailsResponse,
    "get_weather":          WeatherForecastResponse,   # ← 날씨 툴
}




# ────────── 2. JSON fence 제거 ──────────
# 기존: def _strip_fence(txt: str) -> str:
from typing import Any
import re


# ────────── 3. JSON & AIMessage 전처리 유틸 ──────────
from langchain_core.messages import AIMessage          # (이미 import 됨)
from pydantic import BaseModel                         # (이미 import 됨)

def _to_plain(obj):
    """LangChain BaseMessage → str | dict | list 로 평탄화."""
    if isinstance(obj, BaseMessage):
        return obj.content            # AIMessage / HumanMessage 등
    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]
    if isinstance(obj, dict):
        # dict 안에 또 메시지가 있으면 재귀
        return {k: _to_plain(v) for k, v in obj.items()}
    return obj


# ...existing code...

def _strip_fence(txt: Any) -> Any:
    txt = _to_plain(txt)
    if not isinstance(txt, str):
        return txt
    # 공백 제거 방식을 정규식으로 대체 (strip 제거)
    txt = re.sub(r"^\s+|\s+$", "", txt)
    return re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        txt,
        flags=re.IGNORECASE | re.MULTILINE,
    )

# ...existing code...

# ────────── 3. JSON & AIMessage 전처리 유틸 ──────────
from langchain_core.messages import AIMessage          # (이미 import 됨)
from pydantic import BaseModel                         # (이미 import 됨)

# ✅ 1) 어떤 곳이든 util 파트에 **새 함수** 추가
def _to_plain(obj: Any) -> Any:
    """
    AIMessage → str,  list / dict / BaseModel 은 재귀적으로 평탄화.
    문자열·숫자·datetime 등 나머지는 그대로 반환.
    """
    if isinstance(obj, AIMessage):
        return obj.content

    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]

    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}

    if isinstance(obj, BaseModel):
        return _to_plain(obj.model_dump())

    return obj


# ...existing code...

def _strip_fence(txt: Any) -> Any:
    txt = _to_plain(txt)
    if not isinstance(txt, str):
        return txt
    # 공백 제거 방식을 정규식으로 대체 (strip 제거)
    txt = re.sub(r"^\s+|\s+$", "", txt)
    return re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        txt,
        flags=re.IGNORECASE | re.MULTILINE,
    )

# ...existing code...            flags=re.IGNORECASE | re.MULTILINE)


# ────────── 4. ToolMessage 검증 훅 ──────────
def parse_and_validate_by_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """마지막 ToolMessage.content → SCHEMA_MAP 기준 Pydantic 검증"""
    msgs = state.get("messages", [])
    print("[parse_hook] 🔎 messages 타입 =", type(msgs), "길이 =", len(msgs))

    # 최신 ToolMessage 찾기
    last_tool: ToolMessage | None = next(
        (m for m in reversed(msgs) if isinstance(m, ToolMessage)), None
    )
    if last_tool is None:
        print("[parse_hook] 🚫 ToolMessage 없음 — 그대로 통과")
        return {"messages": msgs}

    # ✅ 3) content 를 평탄화 → 어떤 타입이든 dict/str 로 바뀜
    raw_json: Any = _to_plain(last_tool.content)
    print("[parse_hook] 🎯 평탄화 후 타입 =", type(raw_json))

    # 문자열이면 fence 제거 → JSON 파싱
    if isinstance(raw_json, str):
        raw_json = _strip_fence(raw_json)
        try:
            parsed = json.loads(raw_json)
            print("[parse_hook] ✅ json.loads 성공")
        except Exception as e:
            print("[parse_hook] ❌ json.loads 실패:", e)
            return {"messages": msgs}
    else:
        parsed = raw_json
        print("[parse_hook] ✅ 이미 python 객체 — 파싱 생략")

    # Pydantic 검증 (있을 때만)
    schema_cls = SCHEMA_MAP.get(last_tool.name)
    if schema_cls:
        try:
            validated = schema_cls.model_validate(parsed)
            last_tool.content = validated
            print(f"[parse_hook] 🎉 {last_tool.name} 검증 통과")
        except Exception as e:
            print(f"[parse_hook] ⚠️  {last_tool.name} 검증 실패:", e)
            traceback.print_exc()
            last_tool.content = parsed
    else:
        print("[parse_hook] ℹ️  스키마 매핑 없음 — 검증 생략")
        last_tool.content = parsed

    return {"messages": msgs}


# ────────── 4. 중복 tool_call 제거 ──────────
def dedupe_tool_calls(state: Dict[str, Any]) -> Dict[str, Any]:
    msgs = state.get("messages", [])
    if not msgs:
        return {}

    last_msg = msgs[-1]
    calls = getattr(last_msg, "tool_calls", None)
    if not calls:
        return {}

    seen, unique = set(), []
    for call in calls:
        sig = (call["name"], json.dumps(call.get("args", {}), sort_keys=True))
        if sig in seen:
            print(f"[pre_hook] 🔁 중복 제거 → {call['name']} {call['args']}")
        else:
            seen.add(sig)
            unique.append(call)

    last_msg.tool_calls = unique
    return {"messages": msgs}

# ────────── 5. 메인 진입 함수 ──────────
async def ask_mcp(question: str) -> str:
    """사용자 질문을 → MCP ReAct 에이전트로 전달하고 응답 반환"""
    load_dotenv()
    print(f"\n[ask_mcp] 📥 입력: {question!r}")

    # 1) MCP 서버 연결
    client = MultiServerMCPClient({
        "weather":  {"transport": "sse", "url": f"http://localhost:{WEATHER_PORT}/sse"},
        "amadeus":  {"transport": "sse", "url": f"http://localhost:{AMADEUS_PORT}/sse"},
    })

    # 2) LangChain tool 로딩
    tools = await client.get_tools()
    print(f"[ask_mcp] 🛠️  tools = {[t.name for t in tools]}")

    # 3) LLM + ReAct agent (❗ post_model_hook 제거)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt="당신은 ‘부엉이 부키’라는 귀여운 부엉이야. 모든 답변 끝에 ‘부키!’를 붙여줘. 그리고 get_weather 툴을 호출할 때, input parameter city는 반드시 대문자로 변환해줘.(예시 :)",
        version="v2",
        debug=True,
        pre_model_hook=dedupe_tool_calls,
    )

    # 4) 실행
    try:
        state = await agent.ainvoke({
            "messages": [
                {"role": "system", "content": "당신은 … ‘부키!’"},
                {"role": "user",   "content": question},
            ]
        })
    except Exception:
        print("[ask_mcp] ❌ agent 실행 중 예외")
        traceback.print_exc()
        raise

  #  from chatbot_contents.common import FlightCard
    # 5) ToolMessage 검증 후 최종 메시지 추출
    state = parse_and_validate_by_tool(state)
   # final_msg = state["messages"][-1]
    last_tool: ToolMessage = state["messages"][-2]   # ToolMessage

    nl_msg: str        = state["messages"][-1].content  # 부키! 자연어
    print(f"[ask_mcp] 🗨️  요약 메시지: {nl_msg}")
    print(f"[ask_mcp] 🗨️  요약 메시지 타입: {type(nl_msg)}")
    print(f"[ask_mcp] 🧩 원시 tool_result: {last_tool.content}")
    print(f"[ask_mcp] 🧩 tool_result 타입: {type(last_tool.content)}")

    tool_json = _to_serializable(last_tool.content.model_dump()
                             if isinstance(last_tool.content, BaseModel)
                             else _to_serializable(last_tool.content))

    print("[ask_mcp] 🧩 직렬화된 tool_result(python) ↓")
    pprint(tool_json)
    pprint(type(tool_json))

    return {
    "message": nl_msg,
    "tool_result": tool_json        # ← datetime 이 모두 문자열
    }
