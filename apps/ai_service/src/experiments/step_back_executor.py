"""
Step-Back executor ― 서유럽(WEU) 전용
────────────────────────────────────────────────────────────
1) 1-문장 추상화(“step-back question”) → 2) 후보 도시 shortlist
3) 원 질문 + 추상화 모두 고려해 최종 JSON
"""
from __future__ import annotations
from typing import List
from langchain_openai import ChatOpenAI

WEST_EU_CITIES_EN: List[str] = [
    "paris","london","barcelona","berlin","rome","amsterdam",
    "lisbon","prague","vienna","munich","hamburg","frankfurt",
    "cologne","lyon","marseille","nice","toulouse","brussels",
    "antwerp","ghent","zurich","geneva","basel","porto","madrid",
    "valencia","seville","milan","naples","florence","copenhagen",
    "dublin","edinburgh","manchester",
]
_WEU_PRETTY = ", ".join(c.title() for c in WEST_EU_CITIES_EN)


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

COMMON_SUFFIX = f"""
### HARD RULES
1. 서유럽 allow-list → {_WEU_PRETTY}
2. 최상위에 budget_krw, nights 포함.
3. **최종 출력은 JSON 스키마 하나만**(trailing comma 금지)
{JSON_SCHEMA}
"""

# ── LLM helpers ────────────────────────────────────────────
_llm_json = lambda temp=0.0: ChatOpenAI(
    model="gpt-4o-mini",
    temperature=temp,
    use_responses_api=True,
    model_kwargs={"response_format": {"type": "json_object"}},
)
_llm_text = lambda temp=0.0: ChatOpenAI(model="gpt-4o-mini", temperature=temp)

# ── Executor ───────────────────────────────────────────────
class StepBackExecutor:
    def __init__(self):
        # text-mode for reasoning steps, json-mode for final answer
        self._reason_llm = _llm_text(0.2)
        self._answer_llm = _llm_json(0.0)

    async def ainvoke(self, inputs: dict) -> dict:
        q = inputs["messages"][0]["content"]

        # 1) 추상화 질문 생성
        step_back_prompt = (
            "다음 사용자의 요구를 한 문장으로 더 일반화해라. "
            "도시·숫자·고유명은 빼고, 핵심 제약만 남긴다.\n\n"
            f"User Request: «{q}»"
        )
        abstract = self._reason_llm.invoke(step_back_prompt).content.strip()

        # 2) allow-list 중 추상화 조건과 잘 맞는 후보 6개 
        shortlist_prompt = (
            "너는 서유럽 여행 전문가다. 추상화 문장을 바탕으로 "
            "목록 중 적합 도시를 최대 6개 brainstorm하라. "
            f"목록: {_WEU_PRETTY}\n\n"
            f"Abstract: {abstract}\n\n"
            "Return as Python-list string (예: ['Paris','Rome',…])"
        )
        shortlist_raw = self._reason_llm.invoke(shortlist_prompt).content
        shortlist = [c.strip(" '\"") for c in shortlist_raw.strip("[]\n").split(",")][:6]

        # 3) 원 질문 + shortlist → 최종 3개 선정 & JSON
        final_sys = (
            "너는 서유럽 여행 컨설턴트다. "
            "shortlist 중에서 사용자 원 질문까지 고려해 **정확히 3개** 도시를 고르고 "
            "JSON 스키마만 출력한다."
            + COMMON_SUFFIX
        )
        user_msg = (
            f"# Shortlist: {', '.join(shortlist)}\n\n"
            f"# Original Request:\n{q}"
        )
        final_json = self._answer_llm.invoke([("system", final_sys), ("user", user_msg)]).content
        return {"messages": [{"role": "assistant", "content": final_json}]}

def make_step_back_executor() -> StepBackExecutor:
    return StepBackExecutor()
