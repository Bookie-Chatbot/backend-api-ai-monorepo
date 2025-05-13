#!/usr/bin/env python
import os, sys, json, datetime as dt, asyncio

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



# 파라미터 변환기
from app.service.service_utils.amadeus_params import to_amadeus_params



from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.service.dest_recommend.dest_reco_chain import dest_reco_executor

app = FastAPI()



# ─── 3) 초기화 ───────────────────────────────────────
load_dotenv()
AMA = get_client()

def _json_safe(obj: Any):
    """LangChain Message 객체 등을 str로 바꿔 JSON 직렬화."""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except TypeError:
        # dict이지만 message 내부에 HumanMessage 같은 객체가 있을 때
        def convert(o):
            if isinstance(o, list):
                return [convert(i) for i in o]
            if isinstance(o, dict):
                return {k: convert(v) for k, v in o.items()}
            return str(o)
        return json.dumps(convert(obj), ensure_ascii=False, indent=2)

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


async def reply_json(question: str) -> Dict[str, Any]:
    fc = classify(question) or regex_fallback(question)
    intent = fc.get("intent")

    if intent == "price_search":
        try:
            result = search_price(fc["arguments"])
        except Exception as e:
            return {"intent": "price_search", "error": str(e)}
        answer = build_answer(question, result)
        return {
            "intent": "price_search",
            "arguments": fc["arguments"],
            "result": result,
            "answer": answer,
        }

    if intent == "dest_reco":
        # 1) agent 실행 후 raw 상태(state) 획득
        state = await dest_reco_executor.ainvoke(
            {"messages": [{"role": "user", "content": question}]}
        )

        # 2) 마지막 AI 메시지에서 JSON 페이로드 파싱
        import re, json
        msgs = state.get("messages", [])
        raw = msgs[-1] if msgs else None

        text = ""
        if hasattr(raw, "content"):
            # Responses API인 경우 content가 블록 리스트일 수 있음
            if isinstance(raw.content, list):
                for block in raw.content:
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        break
            else:
                text = raw.content
        else:
            text = str(raw)

        m = re.search(r"\{.*\}", text, re.S)
        if m:
            reco = json.loads(m.group(0))
        else:
            reco = {"cards": [], "message": ""}

        # 3) HTML 미리보기 생성
        html_parts = [
            "<!doctype html><html><head><meta charset='utf-8'><title>Destination Recommendations</title></head><body>",
            f"<h2>Query: {question}</h2><div style='display:flex;flex-wrap:wrap;'>",
        ]
        for card in reco.get("cards", []):
            html_parts.append(
                f"<section style='margin:8px;padding:8px;border:1px solid #ccc;width:320px;'>"
                f"<h3>{card['city']} (score {card['score']:.2f})</h3>"
            )
            for url in card.get("photos", []):
                html_parts.append(
                    f"<img src='{url}' style='width:140px;height:140px;object-fit:cover;margin:2px;'/>"
                )
            html_parts.append("</section>")
        html_parts.append("</div></body></html>")

        html = "\n".join(html_parts)
        tmp_path = "./tmp/dest_reco_test.html"
        os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(html)

        # 4) html_path를 포함해 반환
        return {
            "intent": "dest_reco",
            **reco,
            "html_path": tmp_path,
        }





# ─── 6) FastAPI 엔드포인트 ─────────────────────────────────
@app.post("/chat")
async def chat(req: Dict[str, str]):
    q = req.get("query", "")
    return JSONResponse(content=await reply_json(q))

# Debug 전용 HTML 프리뷰
@app.post("/dest/reco")
async def dest_reco(req: Dict[str, str], request: Request):
    q = req.get("query", "")
    res = await dest_reco_executor.ainvoke({"messages": [{"role": "user", "content": q}]})
    payload = {"intent": "dest_reco", **res}

    # 2) HTML 생성
    html_parts = [
        "<!doctype html><html><head><meta charset='utf-8'><title>Destination Recommendations</title></head><body>",
        f"<h2>Query: {q}</h2><div style='display:flex;flex-wrap:wrap;'>",
    ]
    for card in res.get("cards", []):
        html_parts.append(
            f"<section style='margin:8px;padding:8px;border:1px solid #ccc;width:320px;'>"
            f"<h3>{card['city']} (score {card['score']:.2f})</h3>"
        )
        for url in card.get("photos", []):
            html_parts.append(
                f"<img src='{url}' style='width:140px;height:140px;object-fit:cover;margin:2px;'/>"
            )
        html_parts.append("</section>")
    html_parts.append("</div></body></html>")

    html = "\n".join(html_parts)
    # 3) 파일로 저장
    tmp_path = "./tmp/dest_reco_test.html"
    # 디렉터리 없으면 생성
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(html)

    # 4) JSON 응답에 파일 경로 추가
    payload["html_path"] = tmp_path

    return JSONResponse(content=payload)

# ─── 7) CLI (동기) ─────────────────────────────────────────
def cli_loop():
    print("✈️ AI Flight Assistant — ENTER 빈줄 종료\n")
    while True:
        q = input("🗨 질문: ").strip()
        if not q:
            break
        res = asyncio.run(reply_json(q))
        # 안전 직렬화 + 즉시 확인 가능한 디버그 출력
        print(_json_safe(res), "\n")

if __name__ == "__main__":
    cli_loop()