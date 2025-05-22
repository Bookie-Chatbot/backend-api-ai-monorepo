# ── chains/mcp_sub_chains.py  ────────────────────────────────────────────────
import asyncio, json, re
from typing import Dict, Any, Callable
from langchain_core.runnables import RunnableLambda
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_core.messages import BaseMessage

# ▸ 1. MCP 툴별 Pydantic 모델 --------------------------------------------------
from chatbot_contents.price_search     import PriceSearchContent          # PRICE_SEARCH
from chatbot_contents.price_analysis   import PriceAnalysisContent        # PRICE_ANALYSIS
from chatbot_contents.cheapest_date    import CheapestDateResult          # CHEAPEST_DATE
from chatbot_contents.flight_details   import FlightDetailsResponse       # FLIGHT_DETAILS
from chatbot_contents.weather_summary  import WeatherSummaryContent       # WEATHER_SUMMARY
# intent ⇢ 파서 매핑
PARSER_MAP: dict[str, PydanticOutputParser] = {
    "PRICE_SEARCH":     PydanticOutputParser(pydantic_object=PriceSearchContent),
    "PRICE_ANALYSIS":   PydanticOutputParser(pydantic_object=PriceAnalysisContent),
    "CHEAPEST_DATE":    PydanticOutputParser(pydantic_object=CheapestDateResult),
    "FLIGHT_DETAILS":   PydanticOutputParser(pydantic_object=FlightDetailsResponse),
    "WEATHER_SUMMARY":  PydanticOutputParser(pydantic_object=WeatherSummaryContent),
}


# ▸ 2. ask_mcp  (시그니처 확장) ----------------------------------------------
from runs.test.mcp_client import ask_mcp   # 기존 모듈 그대로 두고 아래처럼 시그니처만 확장하세요

# mcp_client.py 안에서 ...
# async def ask_mcp(question: str,
#                   chat_history: list[BaseMessage] | str = "",
#                   format_instructions: str = "") -> str:

# (기존 구현 +) ───────────────────────────────────────────────────────────────
# agent = create_react_agent(
#     ...
#     prompt=(
#        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
#        "아래 JSON 스키마를 반드시 지켜서 답변해줘.\n"
#        f"{format_instructions or ''}"
#        "\n(get_weather 시 city는 반드시 대문자로!)"
#     ),
#     ...
# )
# messages = [{"role": "system", "content": "… ‘부키!’"}]
# if chat_history:
#     messages.extend(chat_history)       # 과거 기록 삽입
# messages.append({"role": "user", "content": question})
# …

# ▸ 3.  JSON → Pydantic 으로 강제 변환 ---------------------------------------
def _strip_fence(txt: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", txt.strip(),
                  flags=re.IGNORECASE | re.MULTILINE)

def dynamic_parse(text: str | Dict[str, Any]) -> Any:
    """
    ① str → dict 로드 → intent 추출
    ② intent 로 PARSER_MAP 선택 & 검증
    ③ 실패 시 그대로 반환 (서버 로그에만 경고)
    """
    raw = text
    if isinstance(text, str):
        try:
            raw = json.loads(_strip_fence(text))
        except Exception:
            return text                 # JSON 아님 → 그대로
    intent = raw.get("intent")
    parser = PARSER_MAP.get(intent)
    if not parser:
        return raw                      # 알 수 없는 intent
    return parser.pydantic_object.model_validate(raw)

safe_parser = RunnableLambda(dynamic_parse)



# ▸ 4.  서브-체인 생성 유틸 ----------------------------------------------------
def build_mcp_sub_chain() -> Callable[[Dict[str, Any]], Any]:
    """
    입력 키:
        question            : str
        chat_history        : list[BaseMessage] | str
        format_instructions : str  (필수! parser.get_format_instructions())
    반환 :
        Pydantic 모델 인스턴스  (ex. PriceSearchContent)  또는 raw
    """
    # Step-1 : MCP 비동기 호출
    async def _invoke(inputs: Dict[str, Any]) -> str:
        return await ask_mcp(
            question=inputs["question"],
            chat_history=inputs.get("chat_history", ""),
            format_instructions=inputs.get("format_instructions", "")
        )
    invoke = RunnableLambda(lambda inp: asyncio.run(_invoke(inp)))

    # 체인 = invoke → safe_parser
    return invoke | safe_parser


# ▸ 5.  실제 서브-체인 인스턴스 ----------------------------------------------
mcp_sub_chain = build_mcp_sub_chain()

# 사용 예시 -------------------------------------------------------------------
# >>> from langchain_core.messages import HumanMessage, AIMessage
# >>> inputs = {
#         "question": "인천에서 뉴욕까지 8월에 200만원 이하 왕복 찾아줘",
#         "chat_history": [
#               HumanMessage(content="지난번 질문…"),
#               AIMessage(content="지난번 답변…")
#         ],
#         "format_instructions": PARSER_MAP["PRICE_SEARCH"].get_format_instructions()
#     }
# >>> result = mcp_sub_chain.invoke(inputs)
# >>> print(result)
# PriceSearchContent(
#     intent='PRICE_SEARCH',
#     contents=ContentsList(
#         message='부엉이 부키가 추천하는… 부키!',
#         flights=[FlightOption(...), ...]
#     )
# )
# ---------------------------------------------------------------------------
