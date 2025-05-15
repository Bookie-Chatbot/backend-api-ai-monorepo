"""
Step-Back executor ― 서유럽(WEU) 전용
────────────────────────────────────────────────────────────
1) 1-문장 추상화(“step-back question”) → 2) 후보 도시 shortlist
3) 원 질문 + 추상화 모두 고려해 최종 JSON
"""
from __future__ import annotations
from typing import List
from langchain_openai import ChatOpenAI

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
_WEU_PRETTY = ", ".join(c.title() for c in CITIES_EN)

JSON_SCHEMA = """
  {
          "budget_krw": 2000000,
          "nights": 7,
          "cards": [
            {
              "city_ko": "파리",
              "city_en": "Paris",
              "country_ko": "프랑스",
              "country_en": "France",
              "highlights": ["미술관", "카페"],
              "description": "루브르 야간 개장으로 붐비지 않는 관람 후, 생제르맹 데 프레의 테라스 카페에서 크렘 브륄레를 맛보세요."
            },
            {
              "city_ko": "산토리니",
              "city_en": "Santorini",
              "country_ko": "그리스",
              "country_en": "Greece",
              "highlights": ["휴양", "경치"],
              "description": "이아 마을 일몰과 함께 인피니티 풀에서 와인을 즐기며 하루를 마무리할 수 있습니다."
            },
            {
              "city_ko": "바르셀로나",
              "city_en": "Barcelona",
              "country_ko": "스페인",
              "country_en": "Spain",
              "highlights": ["건축", "미식"],
              "description": "가우디의 사그라다 파밀리아 관람 뒤, 엘 보른 지구에서 타파스 바 호핑을 즐겨보세요."
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
        #  ① Step-Back 추상화 : 고유명·숫자 제거 → 핵심 제약 도출 :contentReference[oaicite:2]{index=2}

        step_back_prompt = (
            "다음 사용자의 요구를 한 문장으로 더 일반화해라. "
            "도시·숫자·고유명은 빼고, 핵심 제약만 남긴다.\n\n"
            f"User Request: «{q}»"
        )
        abstract = self._reason_llm.invoke(step_back_prompt).content.strip()

        # 2) allow-list 중 추상화 조건과 잘 맞는 후보 6개
        # ② 추상화 → 후보 도시 brainstorm (최대 6) + 근거 키워드 포함

        shortlist_prompt = (
            "STEP-BACK 2/2 ▸ 위 추상화 조건으로 적합 도시·근거 키워드 6쌍 brainstorm.\n"
            f"ALLOW-LIST: {_WEU_PRETTY}\n"
            f"Abstract: {abstract}\n\n"
            "반환 형식 예: ['Paris|문화유산','Bangkok|액티비티', …]"
        )
        shortlist_raw = self._reason_llm.invoke(shortlist_prompt).content
        shortlist = [c.strip(" '\"") for c in shortlist_raw.strip("[]\n").split(",")][:6]

        # 3) 원 질문 + shortlist → 최종 3개 선정 & JSON
        final_sys = (
            "ROLE: 따뜻한 톤의 전문 여행 가이드.\n"
            "TASK: shortlist를 검토하여 사용자 요구에 가장 부합하는 3개 도시를 선정.\n"
            "각 card.description 은 가이드가 직접 말하는 듯한 2문장, 최근 트렌드 (12개월) + 액티비티 포함.\n"
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
