#!/usr/bin/env python
import os
import sys

# ─── 1) 루트 경로 세팅 ───────────────────────────────
# 이 파일이 있는 디렉터리: .../apps/ai_service/src
ROOT = os.path.dirname(os.path.abspath(__file__))

#  a) 앱 내부 src/ 를 파이썬 모듈 최상위로 추가 → 'import app.…' 가능
sys.path.insert(0, ROOT)

#  b) monorepo/packages/ 를 추가 → 'import core_backend.…' 가능
sys.path.insert(0, os.path.abspath(os.path.join(ROOT, "../../../packages")))

# ─── 2) 나머지 임포트 ───────────────────────────────
import json
from dotenv import load_dotenv
from typing import Dict, Any

from packages.core_backend.amadeus_client import get_client
from app.service.answer_prompt import build_answer

# intent 라우터
from app.service.intent_router import classify, regex_fallback



# 여러분이 만든 파라미터 변환기
from app.service.service_utils.amadeus_params import to_amadeus_params


# ─── 3) 초기화 ───────────────────────────────────────
load_dotenv()
AMA = get_client()


def search_price(slots: Dict[str, Any]) -> Dict[str, Any]:
    params = to_amadeus_params(slots)
    print("\n[DEBUG] ▶ 요청 파라미터:", json.dumps(params, indent=2, ensure_ascii=False))

    try:
        rsp = AMA.shopping.flight_offers_search.get(**params, max=3)
    except Exception as e:
        print("[DEBUG-ERROR] Amadeus 호출 실패:", e)
        if hasattr(e, "response") and e.response:
            body = e.response.body
            print("[DEBUG-ERROR-BODY]", body.decode() if isinstance(body, (bytes, bytearray)) else body)
        raise

    # ── Amadeus SDK 8.x~ : HTTP 메타는 1-depth ───────────────────
    print(f"[DEBUG] HTTP 상태: {rsp.status_code}")
    print(f"[DEBUG] Host: {rsp.request.host}")
    print(f"[DEBUG] Raw body 길이: {len(rsp.body)}")


    if not rsp.data:
        return {"error": "No flight offers"}

    cheapest = min(rsp.data, key=lambda x: float(x["price"]["grandTotal"]))
    seg = cheapest["itineraries"][0]["segments"][0]
    return {
        "route":     f"{seg['departure']['iataCode']}-{seg['arrival']['iataCode']}",
        "carrier":   seg["carrierCode"],
        "departure": seg["departure"]["at"],
        "arrival":   seg["arrival"]["at"],
        "price":     float(cheapest["price"]["grandTotal"]),
        "currency":  cheapest["price"]["currency"],
        "offer_id":  cheapest["id"],
    }


def reply_json(question: str) -> Dict[str, Any]:
    # ① intent/slots 추출
    fc = classify(question)
    if not fc["intent"]:
        fc = regex_fallback(question)

    if fc["intent"] != "price_search":
        return {"intent": "unhandled", "message": "지원하지 않는 요청입니다."}

    # ② Amadeus 파라미터 변환 → 최저가 조회
    try:
        result = search_price(fc["arguments"])
    except Exception as e:
        return {"intent": "price_search", "error": str(e)}

    # ③ GPT에게 “대화용 답변” 작성 요청
    answer = build_answer(question, result)

    return {
        "intent":   "price_search",
        "arguments": fc["arguments"],
        "result":    result,
        "answer":    answer,   # 프런트는 이 문자열만 표시해도 OK
    }

def main():
    print("✈️  AI Flight Assistant ― CTRL-C 이면 종료\n")
    print(get_client())
    while True:
        q = input("🗨  질문: ").strip()
        if not q:
            break
        print(json.dumps(reply_json(q), indent=2, ensure_ascii=False), "\n")

if __name__ == "__main__":
    main()
