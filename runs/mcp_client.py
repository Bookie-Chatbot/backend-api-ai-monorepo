import os
import json
import asyncio
from dotenv import load_dotenv

from typing import List, Dict, Type
from pydantic import BaseModel, ValidationError

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import ToolMessage
from chatbot_contents.weather_summary import WeatherSummaryContent, WeatherForecastResponse



class FlightOffer(BaseModel):
    airline: str
    flightNumber: str
    departureDate: str
    arrivalDate: str
    price: float
    currency: str

class FlightOffersResponse(BaseModel):
    offers: List[FlightOffer]

# MCP 툴 이름 → 스키마 매핑
SCHEMA_MAP: Dict[str, Type[BaseModel]] = {
    # 날씨 mcp 응답
    "get_weather": WeatherForecastResponse,
    # flight details 응답 
    "get-flight-details": FlightOffersResponse,
    # ... 필요 시 추가
}

# ──────────────────────────────────────────────────────────
# pre_model_hook: 중복된 tool_calls 제거
# ──────────────────────────────────────────────────────────
def dedupe_tool_calls(state: dict) -> dict:
    msgs = state.get("messages", [])
    if not msgs:
        return {}
    last = msgs[-1]
    calls = getattr(last, "tool_calls", None)
    if not calls:
        return {}
    seen, unique = set(), []
    for c in calls:
        key = (c["name"], json.dumps(c.get("args", {}), sort_keys=True))
        if key in seen:
            print(f"[DEBUG] 중복 제거: {c['name']} args={c.get('args')}")
        else:
            seen.add(key)
            unique.append(c)
    last.tool_calls = unique
    return {"messages": msgs}

# ──────────────────────────────────────────────────────────
# post_model_hook: 마지막 툴 실행 기반 JSON 파싱 + 스키마 검증
# ──────────────────────────────────────────────────────────
def parse_and_validate_by_tool(state: dict) -> dict:
    msgs = state.get("messages", [])
    # 마지막 ToolMessage 찾기
    last_tool = next((m for m in reversed(msgs) if isinstance(m, ToolMessage)), None)
    if not last_tool:
        print("[DEBUG] 실행된 툴을 찾을 수 없음.")
        return {}
    tool_name = last_tool.name
    schema = SCHEMA_MAP.get(tool_name)
    if not schema:
        print(f"[DEBUG] '{tool_name}' 스키마 없음.")
        return {}
    # 마지막 assistant 메시지
    assistant = msgs[-1]
    raw = assistant.content
    try:
        parsed = json.loads(raw)
        print(f"[DEBUG] '{tool_name}' JSON 파싱 성공: {parsed}")
    except json.JSONDecodeError:
        print(f"[DEBUG] '{tool_name}' JSON 파싱 실패.")
        return {}
    try:
        validated = schema.parse_obj(parsed)
        print(f"[DEBUG] '{tool_name}' 스키마 검증 성공")
        assistant.content = validated.dict()
    except ValidationError as e:
        print(f"[ERROR] '{tool_name}' 검증 실패:\n{e}")
    return {"messages": msgs}

# ──────────────────────────────────────────────────────────
# ask_mcp 함수: Main 에서 import 해서 사용
# ──────────────────────────────────────────────────────────
WEATHER_PORT = 8010
AMADEUS_PORT = int(os.getenv("AMADEUS_PORT", 8020))

async def ask_mcp(question: str):
    load_dotenv()
    # MCP 서버 연결 설정
    connections = {
        "weather": {"transport": "sse", "url": f"http://localhost:{WEATHER_PORT}/sse"},
        "amadeus": {"transport": "sse", "url": f"http://localhost:{AMADEUS_PORT}/sse"},
    }
    client = MultiServerMCPClient(connections)
    tools  = await client.get_tools()

    llm = ChatOpenAI(model_name="gpt-3.5-turbo")
    persona = "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. 모든 답변 끝에 ‘부키!’를 붙여줘."
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=persona,
        debug=True,
        version="v2",
        pre_model_hook=dedupe_tool_calls,
        post_model_hook=parse_and_validate_by_tool,
    )

    inputs = {"messages":[
        {"role":"system","content":persona},
        {"role":"user","content":question},
    ]}
    result = await agent.ainvoke(inputs)
    return result["messages"][-1].content
