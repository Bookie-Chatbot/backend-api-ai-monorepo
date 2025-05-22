"""
MCP-전용 서브체인 모음.
다른 코드에 영향 없도록 _INTENT_MAP 만 외부에 노출합니다.
"""
import asyncio, json
from langchain_core.runnables import RunnableLambda      # routing 용 :contentReference[oaicite:0]{index=0}
from langchain.output_parsers.pydantic import PydanticOutputParser  # :contentReference[oaicite:1]{index=1}
from chatbot_contents.common import (          # 이미 존재하는 Pydantic 모델
    PriceSearchContent,
    PriceAnalysisContent,
    CheapestDateContent,
    WeatherSummaryContent,
)
from runs.test.mcp_client import ask_mcp                 # 기존 async-ReAct 호출 래퍼

from langchain_core.messages import BaseMessage  # 타입힌트용

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv


load_dotenv()


# ── 1) 파서 선언 ──────────────────────────────────────────────────
price_search_parser   = PydanticOutputParser(pydantic_object=PriceSearchContent)
price_analysis_parser = PydanticOutputParser(pydantic_object=PriceAnalysisContent)
cheapest_date_parser  = PydanticOutputParser(pydantic_object=CheapestDateContent)
weather_parser        = PydanticOutputParser(pydantic_object=WeatherSummaryContent)

# ── 2) MCP → LLM(재포맷) → Pydantic 체인 팩토리 ───────────────────
def _mk_chain(parser: PydanticOutputParser):
    """
    ① ask_mcp → raw JSON
    ② LLM: format_instructions 주입, JSON → 스키마 정규화
    ③ parser.parse → Pydantic 강제 검증
    """
    # (a) ask_mcp 동기 래핑
    def _call_mcp(inputs: dict):
        return asyncio.run(
            ask_mcp(
                question            = inputs["question"],
               # chat_history        = inputs.get("chat_history", []),
              #  format_instructions = parser.get_format_instructions(),  # 전달
            )
        )

    # (b) LLM으로 한 번 더 포맷
    reformat_prompt = PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에, 2줄짜리 설명을 작성해주고, ‘부엉이 부키’라는 귀여운 부엉이처럼 대답하면서, 모든 답변 끝에 ‘부키!’를 붙여줘."
        "추천 도시 아래 JSON 스키마에 맞춰 반환해줘.\n"
        "아래의 JSON 응답을 주어진 스키마 지침에 출력해줘.\n"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
        "```json\n{raw_json}\n```"
    )
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)                 # :contentReference[oaicite:3]{index=3}
    llm_chain = reformat_prompt | llm

    # (c) 결과 파싱
    def _force_parse(text_or_dict):
        # llm_chain 은 문자열을 반환-예상
        return parser.parse(text_or_dict if isinstance(text_or_dict, str)
                            else json.dumps(text_or_dict, ensure_ascii=False))

    # 전체 Runnable 파이프
    return (
        RunnableLambda(_call_mcp)          # ① MCP 호출
        | llm_chain                        # ② LLM 재포맷
        | RunnableLambda(_force_parse)     # ③ Pydantic 강제
    )

# ── 3) Intent ↔ 체인 맵 ───────────────────────────────────────────
# mcp_sub_chains.py  ── 마지막 부분만 고치면 OK
MCP_INTENT_MAP = {
    "PRICE_SEARCH":   (_mk_chain(price_search_parser),   price_search_parser),
    "PRICE_ANALYSIS": (_mk_chain(price_analysis_parser), price_analysis_parser),
    "CHEAPEST_DATE":  (_mk_chain(cheapest_date_parser),  cheapest_date_parser),
    "WEATHER_SUMMARY":(_mk_chain(weather_parser),        weather_parser),
}
