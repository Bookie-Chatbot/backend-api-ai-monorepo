import os
import sys
import json
import datetime as dt
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List

from app.service.dest_recommend.place_tools import SearchPlaceId, GetDestinationPhotos
from app.service.dest_recommend.hashtag_catalog import HASHTAGS
from .react_executor import make_react_executor
from .self_consistency_executor import make_self_consistency_executor
from .step_back_executor       import make_step_back_executor

from .prompts_and_scenarios import SCENARIOS

# ────────────────────────────────────────────────────────────────
# Ensure project root on path for imports
# ────────────────────────────────────────────────────────────────
SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

load_dotenv()

# Constants
NUM_CARDS = 3
PHOTO_PER_CITY = 1


"""
기본형 Executors 모음
────────────────────────────────────────────────────────────
• zero-shot / one-shot / few-shot / system / contextual / role / llm_config
• 사용자 입력에 항상 “예산(만원)·체류일수”가 포함된다고 가정
"""

WEST_EU_CITIES_EN: List[str] = [
    "paris","london","barcelona","berlin","rome","amsterdam",
    "lisbon","prague","vienna","munich","hamburg","frankfurt",
    "cologne","lyon","marseille","nice","toulouse","brussels",
    "antwerp","ghent","zurich","geneva","basel","porto","madrid",
    "valencia","seville","milan","naples","florence","copenhagen",
    "dublin","edinburgh","manchester",
]
_WEU_LIST_PRETTY = ", ".join(city.title() for city in WEST_EU_CITIES_EN)


# ─────────────────────────────────────────────────────────────────────
# Executor factories: one per prompting technique
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# ③ 공통 JSON 스키마 & 강제 규칙
# ─────────────────────────────────────────────────────────────
JSON_SCHEMA = """
{
  "budget_krw": 500000,      // 사용자가 명시한 총 예산(원)
  "nights": 3,               // 숙박 박수
  "cards": [
    {
      "city_ko": "파리",
      "city_en": "Paris",
      "country_ko": "프랑스",
      "country_en": "France",
      "highlights": ["쇼핑","미식"]
    }
  ]
}
"""

RULES = f"""
### HARD RULES
1. 반드시 다음 서유럽 도시 중 **정확히 3곳** 선택: {_WEU_LIST_PRETTY}.
2. 출력 JSON 최상위에 **budget_krw(정수, KRW)** 와 **nights(정수, 박)** 를
   그대로 포함한다.
3. 나머지 규칙·스키마는 아래 예시 준수(마크다운·여분 설명 금지):

{JSON_SCHEMA}

4. valid JSON (trailing comma ❌).
"""


# ─────────────────────────────────────────────────────────────────────
# Base ChatExecutor for non-ReAct flows (Responses API)
# ─────────────────────────────────────────────────────────────────────
class ChatExecutor:
    """Generic chat executor that can optionally enforce JSON_SCHEMA.

    Parameters
    ----------
    system_message: str
        Base prompt given to the model.
    temperature: float, default 0.0
    enforce_schema: bool, default True
        If True → RULES are appended **and** Responses API `response_format` is set
        to `{"type": "json_object"}` so the model must emit valid JSON.
        If False → RULES are omitted and normal text/markdown is allowed.
    """

    def __init__(self, system_message: str, temperature: float = 0.0, *, enforce_schema: bool = True):
        self.enforce_schema = enforce_schema

        # Build final system prompt
        if enforce_schema:
            full_system = system_message + RULES
        else:
            full_system = system_message  # no RULES appended

        # Initialise LLM – only force JSON when schema is required
        llm_kwargs = {}
        if enforce_schema:
            llm_kwargs = {"response_format": {"type": "json_object"}}

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            use_responses_api=True,
            model_kwargs=llm_kwargs,
        )
        self.system_message = full_system

    async def ainvoke(self, inputs: dict) -> dict:
        question = inputs["messages"][0]["content"]
        messages = [
            ("system", self.system_message),
            ("user", question),
        ]
        raw = self.llm.invoke(messages)
        return {"messages": [{"role": "assistant", "content": raw.content}]}




def make_llm_config_executor():
    # Ensure the system message includes 'json' for Responses API
    sys_msg = "<no-op> Please output your recommendations as JSON."
    return ChatExecutor(system_message=sys_msg, temperature=0.1)

def make_zero_shot_executor():
    msg = (
        "You are a concise Western-Europe travel recommender. "
        "Use the user’s budget(₩) and stay length to pick three cities."
    )
    return ChatExecutor(msg, 0.1)

# 2) JSON‑SCHEMA **비반영** 버전들 -----------------------------------------

def make_zero_shot_executor_no_schema():
    msg = (
        "You are a travel advisor. "
        "Answer concisely in plain Korean text without JSON formatting."
    )
    return ChatExecutor(system_message=msg, temperature=0.5, enforce_schema=False)

def make_one_shot_executor():
    example = (
        "예시\n"
        "입력: 예산 120만 원 / 4일 / 미식·쇼핑 선호 / 4월 초\n"
        "출력(JSON): {\"cards\":[{\"city_ko\":\"바르셀로나\",…}]}\n\n"
        "위 형식을 참고해 사용자 조건에 맞춰 답해라."
    )
    return ChatExecutor(example, 0.2)

def make_one_shot_executor_no_schema():
    example = (
        "예시\n"
        "입력: 예산 120만 원 / 4일 / 미식·쇼핑 선호 / 4월 초\n"
        "출력: 바르셀로나·포르투·니스\n\n"
        "위 형식을 참고해 사용자 조건에 맞춰 답해라."
    )
    return ChatExecutor(example, 0.2, enforce_schema=False)


def make_few_shot_executor():
    shots = (
        "예시1 … (120만/휴양/5월) → 바르셀로나·포르투·니스\n"
        "예시2 … (200만/문화/9월) → 파리·마드리드·비엔나\n\n"
        "두 예시의 패턴을 학습해 동일한 JSON을 출력해라."
    )
    return ChatExecutor(shots)

def make_few_shot_executor_no_schema():
    shots = (
        "예시1 … (120만/휴양/5월) → 바르셀로나·포르투·니스\n"
        "예시2 … (200만/문화/9월) → 파리·마드리드·비엔나\n\n"
        "두 예시의 패턴을 학습해 동일한 JSON을 출력해라."
    )
    return ChatExecutor(shots, enforce_schema=False)


def make_system_prompt_executor():
    msg = "You are a senior travel consultant producing structured JSON answers."
    return ChatExecutor(msg)

def make_contextual_prompt_executor():
    today = dt.date.today().isoformat()
    msg = f"오늘은 {today}. 현재 환율·계절을 고려해 최적 도시를 추천한다."
    return ChatExecutor(msg)

def make_role_prompt_executor():
    msg = "너는 여행사 직원이다. 친절한 톤으로 JSON만 출력해라."
    return ChatExecutor(msg)


def make_cot_executor() -> ChatExecutor:
    """Chain-of-Thought 버전"""
    sys_msg = (
        "너는 서유럽 여행 전문 컨설턴트야. "
        "조용히 단계별로 생각(Chain-of-Thought)한 뒤 "
        "위 JSON 스키마만 출력해."
    )
    return ChatExecutor(sys_msg, temperature=0.2)



# ─────────────────────────────────────────────────────────────────────
# Registry
 # "react": make_react_executor

# ─────────────────────────────────────────────────────────────────────
EXECUTORS = {
    "react": make_react_executor,
    "llm_config": make_llm_config_executor,
    "zero_shot": make_zero_shot_executor,
   # "zero_shot_no_schema": make_zero_shot_executor_no_schema,
    "one_shot": make_one_shot_executor,
    #"one_shot_no_schema": make_one_shot_executor_no_schema,
    "few_shot": make_few_shot_executor,
    #"few_shot_no_schema": make_few_shot_executor_no_schema,
    "system_prompt": make_system_prompt_executor,
    "contextual_prompt": make_contextual_prompt_executor,
    "role_prompt": make_role_prompt_executor,
    "step_back": make_step_back_executor,
    "cot_prompt": make_cot_executor,
    "self_consistency": make_self_consistency_executor,
}



