"""
Self-Consistency executor ― 서유럽(WEU) 전용
────────────────────────────────────────────────────────────
• 5-회 독립 추론 → 다수결 → 최종 JSON
• WEU 도시 allow-list를 절대 벗어나지 않음
"""
from __future__ import annotations
import random, asyncio
from typing import List, Dict
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

COMMON_SUFFIX = f"""
### HARD RULES
1. 추천은 반드시 다음 목록에서 **정확히 3개** 도시만 선택: {_WEU_PRETTY}.
2. 허구 정보·근거 없는 축약형 지명 금지.
3. 출력은 아래 JSON 스키마 **하나만**(설명·마크다운 없이):

   {{
          "budget_krw": 2000000,
          "nights": 7,
          "cards": [
            {{
              "city_ko": "파리",
              "city_en": "Paris",
              "country_ko": "프랑스",
              "country_en": "France",
              "highlights": ["미술관", "카페"],
              "description": "루브르 야간 개장으로 붐비지 않는 관람 후, 생제르맹 데 프레의 테라스 카페에서 크렘 브륄레를 맛보세요."
            }},
            {{
              "city_ko": "산토리니",
              "city_en": "Santorini",
              "country_ko": "그리스",
              "country_en": "Greece",
              "highlights": ["휴양", "경치"],
              "description": "이아 마을 일몰과 함께 인피니티 풀에서 와인을 즐기며 하루를 마무리할 수 있습니다."
            }},
            {{
              "city_ko": "바르셀로나",
              "city_en": "Barcelona",
              "country_ko": "스페인",
              "country_en": "Spain",
              "highlights": ["건축", "미식"],
              "description": "가우디의 사그라다 파밀리아 관람 뒤, 엘 보른 지구에서 타파스 바 호핑을 즐겨보세요."
            }}
          ]
        }}
4. 유효한 JSON (trailing comma ❌).
"""


# ── LLM wrapper ────────────────────────────────────────────
class _LLM:
    def __init__(self, temperature: float):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            use_responses_api=True,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

    def run(self, sys_msg: str, user_msg: str) -> str:
        raw = self.llm.invoke([("system", sys_msg), ("user", user_msg)])
        return raw.content

# ── Self-Consistency Executor ──────────────────────────────
class SelfConsistencyExecutor:
    _N = 5  # 투표 횟수

    def __init__(self):
        self._base_sys = (
            "ROLE: 친근하지만 전문적인 세계 여행 컨설턴트.\n"
            "TASK: Chain-of-Thought(조용히), 다양한 reasoning path 5회 생성 후 "
            "Self-Consistency로 가장 빈번한 결과를 선택.\n"
            "OUTPUT: HARD RULES & JSON 스키마만 준수. "
            "각 card.description 은 2문장, 사용자가 체감할 생생한 액티비티를 포함.\n"
        ) + COMMON_SUFFIX
        # 다양성 확보용 서로 다른 temperature
        self._llms = [_LLM(temperature=0.4 + 0.1 * random.random()) for _ in range(self._N)]

    async def ainvoke(self, inputs: Dict) -> Dict:
        question = inputs["messages"][0]["content"]

        async def _once(llm: _LLM) -> str:
            return llm.run(self._base_sys, question)

        drafts = await asyncio.gather(*[_once(l) for l in self._llms])

        def _to_text(raw) -> str:
            if isinstance(raw, str):
                return raw
            if isinstance(raw, list):
                # Responses-API 형식일 때
                return " ".join(
                    frag.get("text", str(frag)) if isinstance(frag, dict) else str(frag)
                    for frag in raw
                )
            return str(raw)

        freq: Dict[str, int] = {}
        for raw in drafts:
            txt = _to_text(raw).lower()
            for city in CITIES_EN:
                if city in txt:
                    freq[city] = freq.get(city, 0) + 1

        top3 = sorted(freq, key=freq.get, reverse=True)[:3]
        if len(top3) < 3:  # 예외적으로 등장 수가 모자라면 랜덤 보충
            remaining = [c for c in CITIES_EN if c not in top3]
            top3 += random.sample(remaining, 3 - len(top3))

        # ── 최종 결정적 JSON ────────────────────────────────
        final_sys = (
            "아래 도시 3개를 그대로 사용하라. "
            f"도시 리스트: {', '.join(top3)}. "
            "규칙을 위배하지 않는 JSON을 출력한다."
        ) + COMMON_SUFFIX

        decisive_llm = _LLM(temperature=0.0)
        final_json = decisive_llm.run(final_sys, question)

        return {"messages": [{"role": "assistant", "content": final_json}]}

def make_self_consistency_executor() -> SelfConsistencyExecutor:
    return SelfConsistencyExecutor()
