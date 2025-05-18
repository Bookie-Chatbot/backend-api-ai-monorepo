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

# 서유럽 + 동남·동아시아를 통합한 도시 리스트
CITIES_EN: List[str] = [
    # ── 서유럽
    "paris", "london", "barcelona", "berlin", "rome", "amsterdam",
    "lisbon", "prague", "vienna", "munich", "hamburg", "frankfurt",
    "cologne", "lyon", "marseille", "nice", "toulouse", "brussels",
    "antwerp", "ghent", "zurich", "geneva", "basel", "porto", "madrid",
    "valencia", "seville", "milan", "naples", "florence", "copenhagen",
    "dublin", "edinburgh", "manchester",

    # ── 동남아시아 & 인도차이나
    "bangkok", "singapore", "kuala_lumpur", "jakarta", "bali",
    "hanoi", "ho_chi_minh_city", "phuket", "chiang_mai",
    "siem_reap", "phnom_penh", "vientiane", "luang_prabang",
    "yangon",

    # ── 동아시아
    "seoul", "busan", "jeju", "tokyo", "osaka", "kyoto",
    "taipei", "hong_kong", "shanghai", "beijing",
    "guangzhou", "shenzhen",

    # ── 남아시아 & 몽골
    "new_delhi", "mumbai", "kathmandu", "ulaanbaatar",
]

_WEU_LIST_PRETTY = ", ".join(city.title() for city in CITIES_EN)


# ─────────────────────────────────────────────────────────────────────
# Executor factories: one per prompting technique
# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# ③ 공통 JSON 스키마 & 강제 규칙
# ─────────────────────────────────────────────────────────────
JSON_SCHEMA = """
{
  "budget_krw": integer,       // integer: 사용자 예산(원)
  "nights": integer,           // integer: 숙박 박수
  "answer": string,          // string: <부키의 자연어 추천 텍스트>
}
"""

RULES = f"""
### HARD RULES
1. 반드시 다음 도시 중 **정확히 3곳** 선택: {_WEU_LIST_PRETTY}.
2. 출력 JSON 최상위에 **budget_krw(정수, KRW)** 와 **nights(정수, 박)** 를
   그대로 포함한다.
3.JSON 키는 "budget_krw\", \"nights\", \"answer\"** 이 세 가지만 사용하세요.

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
           # model_kwargs=llm_kwargs,
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
    sys_msg = "<no-op>"
    return ChatExecutor(system_message=sys_msg, temperature=0.1)

def make_llm_config_executor2():
    # Ensure the system message includes 'json' for Responses API
    sys_msg = "<no-op> "
    return ChatExecutor(system_message=sys_msg, temperature=0.9)

def make_zero_shot_executor():
    msg = (
        "사용자의 예산, 취향, 여행 기간을 바탕으로 여행 목적지 TOP-3를 추천해줘."
    )
    return ChatExecutor(msg, 0.1)

# 2) JSON‑SCHEMA **비반영** 버전들 -----------------------------------------


def make_one_shot_executor():
    example = (
        "사용자의 예산, 취향, 여행 기간을 바탕으로 여행 목적지 TOP‑3를 추천해줘. "
        "예를 들어, 사용자가 '예산 120만 원, 4일 일정, 미식·쇼핑 선호, 4월 초 출발'이라면 아래와 같은 JSON을 출력하세요. 각 카드에 1‑2문장 `description` 포함.\n"
        """
        {
          "budget_krw": 1200000,
          "nights": 4,
          "cards": [
            {"city_ko": "바르셀로나", "city_en": "Barcelona", "country_ko": "스페인", "country_en": "Spain", "highlights": ["미식", "쇼핑"], "description": "현지 타파스 투어와 보케리아 시장 쇼핑을 하루에 모두 즐길 수 있어요."},
            {"city_ko": "피렌체", "city_en": "Florence", "country_ko": "이탈리아", "country_en": "Italy", "highlights": ["역사", "예술"], "description": "메디치 가문의 흔적을 따라 르네상스 미술관을 탐방해 보세요."},
            {"city_ko": "리스본", "city_en": "Lisbon", "country_ko": "포르투갈", "country_en": "Portugal", "highlights": ["풍경", "문화"], "description": "노란 트램을 타고 알파마 언덕을 오르며 파두 선율을 느껴보세요."}
          ]
        }
        """
    )
    return ChatExecutor(example)


def make_few_shot_executor():
    shots = (
        """당신은 **‘부키’라는 귀여운 여행 메이트 부엉이**입니다.
사용자의 예산, 일정, 테마를 받아 **TOP-3 여행지**를 추천해 주세요.

🦉 부키의 ‘두근두근 극한 사례’ 예시:

[엣지 케이스 A]
• 입력: 예산 0KRW 초과 ~ 100 000 KRW 이하 / 숙박 1박 / 테마 “문화 충격 주세요!”
→ 추천: 없음
  (부키: “…죄송해요. 1만 원으로는 실제 여행 준비가 어려워요…
   마음만이라도 함께 떠나볼까요? 💧”)

[엣지 케이스 B]
• 입력: 예산 10 000 000 000 KRW 이상 / 숙박 7박 / 테마 “왕처럼 올인클루시브 휴양”
→ 추천: 니스, 산토리니, 발리
  (부키: “전세기 띄우고 프라이빗 섬 리조트에서 올인클루시브를 마음껏 즐겨보세요😵‍💫”)

[엣지 케이스 C]
• 입력: 예산 0 KRW / 숙박 0박 / 테마 “가장 로컬한 경험”
→ 추천: 없음
  (부키: “…아무 것도 준비할 수 없어서 너무 슬퍼요…
   하지만 꿈속 여행은 언제든 무료랍니다💔”)

↘ 위 예시와 **같은 형식**으로 사용자 질문에 답하고,
   • **TOP-3 여행지** (불가능할 땐 ‘없음’)
   • **부키의 귀엽고 전문적인 멘트 + 이모지**
   """

    )
    return ChatExecutor(shots)



def make_system_prompt_executor():
    msg = ("너는 여행 추천을 전문으로 하는 AI 챗봇이야."
"사용자의 예산, 취향, 여행 기간에 따라 최적의 목적지를 추천해줘."
"추천은 신뢰할 수 있는 정보에 기반해야하고, 과장하거나 허구의 정보의 생성은 삼가해줘."
"추천은 JSON 형식으로 출력해야 해."
)
    return ChatExecutor(msg)

def make_contextual_prompt_executor():
    today = dt.date.today().isoformat()
    msg = (
        "사용자가 급하게 해외 여행을 다녀오려고 해."
        f"오늘은 {today}. 실시간 환율과 계절을 고려해 사용자의 자유로운 요청을 분석한 뒤, \n"
        "조건에 맞는 3개 도시를 추천하고 모든 카드에 `description`을 써 주세요."
    )
    return ChatExecutor(msg)

def make_role_prompt_executor():
    msg = ( "너는 친절하면서 전문적인 여행사 직원이이."
        "사용자의 예산, 취향, 여행 기간을 바탕으로 여행 목적지 TOP-3를 추천해줘."
         "각 `description`에는 부드러운 조언·포인트를 1‑2문장으로 담아줘."

         )
    return ChatExecutor(msg)


def make_cot_executor() -> ChatExecutor:
    """Chain-of-Thought 버전"""
    sys_msg = (
        "너는 세계 여행 전문 컨설턴트야. "
        "사용자의 예산, 취향, 여행 기간을 바탕으로 단계별로 생각(Chain-of-Thought)한 뒤 "
        " 여행 목적지 TOP-3를 추천해서 JSON으로 출력해줘.\n"

    )
    return ChatExecutor(sys_msg, temperature=0.2)



# ─────────────────────────────────────────────────────────────────────
# Registry
 # "react": make_react_executor

# ─────────────────────────────────────────────────────────────────────
EXECUTORS = {
   # "react": make_react_executor,
   # "llm_config": make_llm_config_executor,
   # "llm_config2": make_llm_config_executor2,
   # "zero_shot": make_zero_shot_executor,
   # "zero_shot_no_schema": make_zero_shot_executor_no_schema,
   # "one_shot": make_one_shot_executor,
    #"one_shot_no_schema": make_one_shot_executor_no_schema,
   "few_shot": make_few_shot_executor,
    #"few_shot_no_schema": make_few_shot_executor_no_schema,
   # "system_prompt": make_system_prompt_executor,
   # "contextual_prompt": make_contextual_prompt_executor,
   # "role_prompt": make_role_prompt_executor,
   # "step_back": make_step_back_executor,
   # "cot_prompt": make_cot_executor,
   # "self_consistency": make_self_consistency_executor,
}



