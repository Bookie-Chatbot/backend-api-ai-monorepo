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
### ALLOW_LIST : {_WEU_PRETTY}.
"""


# ── LLM wrapper ────────────────────────────────────────────
class _LLM:
    def __init__(self, temperature: float):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            use_responses_api=True,
           # model_kwargs={"response_format": {"type": "json_object"}},
        )

    def run(self, sys_msg: str, user_msg: str) -> str:
        raw = self.llm.invoke([("system", sys_msg), ("user", user_msg)])
        return raw.content

# ── Self-Consistency Executor ──────────────────────────────
class SelfConsistencyExecutor:
    _N = 5  # 투표 횟수

    def __init__(self):
        self._base_sys = (
"""
[ROLE]: 세계 여행 컨설턴트 부키🦉 (장난+전문 반반).

[SELF-CONSISTENCY]: 서로 다른 5개의 추론 경로를 **Temperature=0.8**로 생성하고,
각 경로에서 **Self-Consistency**를 통해 가장 빈번한 결과를 선택합니다.

[RULES]:

- ALLOW_LIST 밖의 도시는 ‘삐악!’ 경고 후 무시
- 각 CoT 샘플은 “Path 1: …”, “Path 2: …” 형태로 구분
- 최종 **Self-Vote**로 도시별 득표수 집계 (“Paris 4표 / Rome 3표 / …”)

[OUTPUT]:

1. **5개 CoT 샘플** (Path 1–5)
2. **투표 결과 tally**
3. **최빈 3개 도시**에 대한 2문단 요약 (매력 포인트·예산 대비 만족도)
"""
        ) + COMMON_SUFFIX
        # 다양성 확보용 서로 다른 temperature
        self._llms = [_LLM(temperature=0.4 + 0.1 * random.random()) for _ in range(self._N)]

    async def ainvoke(self, inputs: Dict) -> Dict:
        question = inputs["messages"][0]["content"]

        async def _once(llm: _LLM) -> str:
            return llm.run(self._base_sys, question)

        # ① CoT 샘플 5개 생성
        drafts = await asyncio.gather(*[_once(l) for l in self._llms])


        # ② 디버깅: 각 Path의 원본 CoT 출력
        for i, raw in enumerate(drafts, 1):
            print(f"\n--- Path {i} 원본 CoT ---\n{raw}\n")

        # ③ 이후 텍스트 정제·투표 로직 진행
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
      # ── 최종 결정적 JSON ────────────────────────────────────────────────
        final_sys = (
          "🎉 부키 최종 라운드입니다! SELF-VOTE에서 승리한 3개 도시는: "
           f"{', '.join(top3)} 입니다.\n\n"
           "승리한 3개의 도시를 그대로 사용해주세요. "
       "– 이제 다음 지침을 모두 준수해 답변을 작성하세요:\n"
    "  1) 여행 포인트를 2문장씩 요약\n"
    "  2) 마지막 문단에 “부키🦉 총예산 ≈ … KRW” 형태로 산출\n"
    "  3) 자연어 텍스트 안에 아래 JSON 객체를 **반드시** 포함할 것\n\n"
    "```json\n"
    "{\n"
    "  \"budget_krw\": <총 예산 KRW 정수>,\n"
    "  \"nights\": <숙박 일수 정수>,\n"
    "  \"answer\": \"<부키의 자연어 추천 텍스트>\"\n"
    "}\n"
    "```\n\n"
    "– JSON 키는 **\"budget_krw\", \"nights\", \"answer\"** 이 세 가지만 사용하세요."
  ) + COMMON_SUFFIX


        decisive_llm = _LLM(temperature=0.0)
        final_json = decisive_llm.run(final_sys, question)

        return {"messages": [{"role": "assistant", "content": final_json}]}

def make_self_consistency_executor() -> SelfConsistencyExecutor:
    return SelfConsistencyExecutor()
