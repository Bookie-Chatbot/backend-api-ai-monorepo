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

# ────────── 0. 전역 설정 ──────────
ROOT          = Path(__file__).resolve().parent
WEATHER_PORT  = 8010
AMADEUS_PORT  = int(os.getenv("AMADEUS_PORT", 8020))

# ────────── 1. SCHEMA_MAP ──────────

SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "search-flights":       FlightOffersResponse,
    "find-cheapest-dates":  CheapestDateResult,
    "analyze-flight-prices": PriceAnalysisContent,
    "get-flight-details":   FlightDetailsResponse,
    "get_weather":          WeatherForecastResponse,   # ← 날씨 툴
}


# ────────── 2. JSON fence 제거 ──────────
def _strip_fence(txt: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", txt.strip(),
                  flags=re.IGNORECASE | re.MULTILINE)

# ────────── 3. ★ ToolMessage 검증 훅 ★ ──────────
def parse_and_validate_by_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """마지막 ToolMessage.content → SCHEMA_MAP 기준 Pydantic 검증."""
    msgs = state.get("messages", [])
    last_tool: ToolMessage | None = next(
        (m for m in reversed(msgs) if isinstance(m, ToolMessage)), None
    )
    if last_tool is None:
        return {}          # 검증할 ToolMessage 없음

    tool_name = last_tool.name
    raw_json = last_tool.content

    # ① content 추출 (Text / EmbeddedResource / str 모두 지원)
    if isinstance(raw_json, list) and raw_json:
        first = raw_json[0]
        if first.get("type") == "text":
            raw_json = first["text"]
        elif first.get("type") == "resource":
            raw_json = first["resource"]["text"]

    if isinstance(raw_json, str):
        raw_json = _strip_fence(raw_json)

    # ② JSON → Python
    try:
        parsed = json.loads(raw_json)
    except Exception as e:
        print(f"[parse_hook] JSON 파싱 실패 ⇒ {e}")
        return {}

    # ③ Pydantic 검증 (스키마 없으면 건너뜀)
    schema_cls = SCHEMA_MAP.get(tool_name)
    if not schema_cls:
        last_tool.content = parsed
        return {"messages": msgs}

    try:
        validated = schema_cls.model_validate(parsed)
        last_tool.content = validated
        print(f"[parse_hook] ✔️  {tool_name} 응답 검증 통과")
    except Exception as e:
        print(f"[parse_hook] ❌ {tool_name} 검증 오류: {e}")
        traceback.print_exc()
        last_tool.content = parsed  # 검증 실패해도 파싱 결과는 넣어 둠

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

    from .mcpFlight import FlightCard
    # 5) ToolMessage 검증 후 최종 메시지 추출
    state = parse_and_validate_by_tool(state)
   # final_msg = state["messages"][-1]
    last_tool: ToolMessage = state["messages"][-2]   # ToolMessage
    nl_msg: str        = state["messages"][-1].content  # 부키! 자연어
    print(f"[ask_mcp] 🗨️  요약 메시지: {nl_msg}")
    print(f"[ask_mcp] 🧩 원시 tool_result: {last_tool.content}")

    # 5️⃣ tool_result 직렬화 --------------------------------------------
    if isinstance(last_tool.content, BaseModel):
        tool_json = last_tool.content.model_dump()   # 안전 직렬화 :contentReference[oaicite:2]{index=2}
    else:
        tool_json = last_tool.content
    print(f"[ask_mcp] 🧩 직렬화된 tool_result: {tool_json}"
          f" ({type(tool_json)})")
    print()





    return {
        "message": nl_msg,
        "tool_result": tool_json
    }



    # 6) 출력 포맷 결정
   # if isinstance(content, (dict, list)):
    #    return json.dumps(content, ensure_ascii=False, indent=2)
    #return str(content)
