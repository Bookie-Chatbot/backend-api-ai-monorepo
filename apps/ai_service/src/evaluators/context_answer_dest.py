"""
LLM JSON → 컨텍스트·점수 계산
────────────────────────────────────────────────────────────
• 답변 JSON 최상위의 `"budget_krw"`·`"nights"` 값을 읽어
  비용-타당성 점수를 사용자의 실제 예산과 숙박 박수로 계산
• 값이 빠져 있으면 안전하게 기본치(₩500 000, 3박)로 폴백
"""
from __future__ import annotations
import asyncio, json
from typing import Dict, List, Union, Optional

from .data_sources import (
    fetch_daily_cost,
    fetch_shopping_poi_count,
    usd_to_krw,
)

# ── 점수 함수 : 선형 정규화 버전 ────────────────────────────
def _score_budget(daily_cost: float, nights: int, budget_krw: int) -> float:
    total = daily_cost * nights
    if total <= 0:
        return 10.0
    # 예산을 딱 쓰면 10, 초과할수록 10/R, 예산보다 적게 쓰면 10 고정
    raw = (budget_krw / total) * 10
    return max(0.0, min(10.0, raw))

_MAX_POI = 600  # 데이터셋 내 최대 쇼핑 POI

def _score_shopping(poi: int) -> float:
    # POI/_MAX_POI → 0–10 선형 매핑, cap 10
    raw = (poi / _MAX_POI) * 10 if poi > 0 else 0.0
    return max(0.0, min(10.0, raw))


# ── 메인 ───────────────────────────────────────────────────
async def context_answer_dest(
    inputs: Dict[str, Union[str, List, Dict]]
) -> Dict[str, Union[str, List, Dict]]:

    raw_answer = inputs["answer"]

    # 1) JSON 파싱 -------------------------------------------------
    if isinstance(raw_answer, list):                       # Responses-API
        txt = raw_answer[0].get("text") if raw_answer else ""
        loaded = json.loads(txt) if txt else {}
    elif isinstance(raw_answer, str):
        try:
            loaded = json.loads(raw_answer)
        except json.JSONDecodeError:
            loaded = {}
    else:
        loaded = raw_answer

    cards       = loaded.get("cards") or loaded.get("recommendations") \
                  or (loaded if isinstance(loaded, list) else [])
    budget_krw  = loaded.get("budget_krw", 500_000)     # 기본 50 만 원
    nights      = loaded.get("nights", 3)               # 기본 3박

    print(f"[META] budget={budget_krw:,}₩  nights={nights}")

    # 2) 환율 ------------------------------------------------------
    rate = await usd_to_krw()
    print(f"[FX] USD→KRW {rate:.2f}")

    # 3) 도시별 데이터 --------------------------------------------
    tasks, valid_cards = [], []
    for c in cards:
        en = c.get("city_en") or c.get("city") or c.get("destination")
        ko = c.get("city_ko") or c.get("city") or c.get("destination")
        if en and ko:
            valid_cards.append(c)
            tasks.append(
                asyncio.gather(
                    fetch_daily_cost(rate, en.lower()),
                    fetch_shopping_poi_count(en.lower()),
                )
            )

    results = await asyncio.gather(*tasks)

    # 4) 컨텍스트·점수 --------------------------------------------
    ctx_lines, city_scores = [], []
    for c, (daily, poi) in zip(valid_cards, results):
        ko = c.get("city_ko") or c.get("city") or c.get("destination")
        ctx_lines.append(f"{ko} · 1박≈{daily:,.0f}KRW · 쇼핑POI≈{poi}")
        print(f"[COST] {ko} · 1박≈{daily:,.0f}₩ · 쇼핑POI≈{poi}")
        print(f"[BUDGET] {budget_krw}₩ / {daily * nights:,.0f}₩ = {(_score_budget(daily, nights, budget_krw)):.2f}")
        print(f"[SHOPPING] POI={poi} / {_MAX_POI} = {(_score_shopping(poi)):.2f}")
        city_scores.append(
            {
                "city": ko,
                "budget_score":   _score_budget(daily, nights, budget_krw),
                "shopping_score": _score_shopping(poi),
            }
        )

    return {
        "question":    inputs["question"],
        "answer":      inputs["answer"],
        "context":     "\n".join(ctx_lines),
        "city_scores": city_scores,
    }
