from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.tools import tool
from typing import List, Dict, Any
import random, datetime as dt
from openai import OpenAI
from dotenv import load_dotenv

import os
import sys


load_dotenv()

SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from .place_tools_safe import SearchPlaceId, GetDestinationPhotos
from app.service.dest_recommend.hashtag_catalog import HASHTAGS


# 서유럽 allow-list (CSV와 동일)
WEU_EN: List[str] = [
    "paris","london","barcelona","berlin","rome","amsterdam",
    "lisbon","prague","vienna","munich","hamburg","frankfurt",
    "cologne","lyon","marseille","nice","toulouse","brussels",
    "antwerp","ghent","zurich","geneva","basel","porto","madrid",
    "valencia","seville","milan","naples","florence","copenhagen",
    "dublin","edinburgh","manchester",
]
WEU_PRETTY = ", ".join(c.title() for c in WEU_EN)
NUM_CARDS = 3          # 카드 개수 고정 값
PHOTO_PER_CITY = 1



def web_search_preview(query: str) -> str:
    """실시간 웹 서치 → Responses API 래핑."""
    client = OpenAI()
    resp = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=query,
    )
    return resp.output_text

    return "Handled by Responses API"

SYS_MSG = f"""
You are a step-by-step ReAct travel agent.

## ALLOW-LIST (반드시 여기서만 선택)
{WEU_PRETTY}

## Tools
1. web_search_preview(query, context) → text
2. search_place_id(query [,country]) → place_id
3. get_destination_photos(place_id, limit={PHOTO_PER_CITY}) → photos[]

## For **exactly {NUM_CARDS}** cities
・Pick 3 *distinct* cities from the ALLOW-LIST that best satisfy the user’s constraints.
・Gather one photo via Place ID.
・Write a 4-line Korean description that includes **why** it matches + **one event/trend** in the last 12 months (proper noun + date).

## FINAL OUTPUT (JSON only)
* 최상위에 사용자의 **budget_krw**(KRW, int) & **nights**(박, int) 포함
* cards 배열은 정확히 {NUM_CARDS}개
* 예시 JSON 스키마:

{{{{
  "budget_krw": 600000,
  "nights": 4,
  "cards": [
    {{{{
      "city_ko": "파리",
      "city_en": "Paris",
      "country_ko": "프랑스",
      "country_en": "France",
      "highlights": ["미식","쇼핑"],
      "photos": ["https://…"],
      "description": "…"
   }}}}
  ]
}}}}
"""
# Prompt template with placeholder for messages
PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYS_MSG),
    MessagesPlaceholder(variable_name="messages"),
])

# 1) Instantiate base LLM with JSON mode and Responses API enabled
base_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=2000,
  #  use_responses_api=True,
    model_kwargs={"response_format": {"type": "json_object"}},
)

tool_defs = [web_search_preview, SearchPlaceId, GetDestinationPhotos]
llm_with_tools = base_llm.bind_tools(tool_defs, strict=True)

_react_graph = create_react_agent(
    model=llm_with_tools,
    tools=tool_defs,     # ← **같은 리스트 전달**
    prompt=PROMPT,
)


# ────────────────────────────────────────────────────────────
# 4) 래퍼 클래스 (ainvoke 호환)
# ────────────────────────────────────────────────────────────
class ReactExecutor:
    def __init__(self):
        self._graph = _react_graph

    async def ainvoke(self, inputs: Dict[str, Any], **kwargs) -> Dict:
        """
        LangSmith 호환 비동기 호출 래퍼.
        - inputs: {"messages": [{"role": "user", "content": <question>}]}
        - kwargs : ReAct용 추가 설정 (예: max_rounds, recursion_limit)
        반환값:
        {"messages": [{"role": "assistant", "content": <JSON string>}]}
        """
        result = await self._graph.ainvoke(inputs, **kwargs)
        return {"messages": [{"role": "assistant", "content": result}]}

def make_react_executor() -> ReactExecutor:
    return ReactExecutor()