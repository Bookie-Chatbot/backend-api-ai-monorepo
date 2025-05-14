#!/usr/bin/env python
import os, sys, json, datetime as dt, asyncio

# ─── 1) 루트 경로 세팅 ───────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.abspath(os.path.join(ROOT, "../../../packages")))

# ─── 2) 나머지 임포트 ───────────────────────────────
import json
from dotenv import load_dotenv
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader

from packages.core_backend.amadeus_client import get_client
from app.service.answer_prompt import build_answer
from app.service.intent_router import classify, regex_fallback
from app.service.service_utils.amadeus_params import to_amadeus_params
from app.service.dest_recommend.dest_reco_chain import dest_reco_executor

app = FastAPI()

# ─── 3) 초기화 ───────────────────────────────────────
load_dotenv()
AMA = get_client()

# Jinja2 환경 설정
TEMPLATE_DIR = os.path.join(ROOT, "tmp")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)


app = FastAPI()



# ─── 3) 초기화 ───────────────────────────────────────
load_dotenv()
AMA = get_client()

# HTML 렌더링 함수
def render_dest_reco_html(query: str, cards: list, out_path: str):
    template = jinja_env.get_template("dest_reco_full.html")
    html = template.render(query=query, cards=cards)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)



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
        return {"intent": "price_search", "arguments": fc["arguments"], "result": result, "answer": answer}

    if intent == "dest_reco":
        # AI 에이전트 호출
        states = await dest_reco_executor.ainvoke(
            {"messages":[{"role":"user","content":question}]},
            config={"max_rounds":25, "recursion_limit":60}
        )

        # HTML 생성

        # 2) 마지막 메시지에서 JSON 페이로드 추출 (이전 방식 그대로)
        import re
        raw = states.get("messages", [])[-1]
        if isinstance(raw.content, list):
            text = next((b["text"] for b in raw.content if b.get("type")=="text"), "")
        else:
            text = raw.content or ""
        m = re.search(r"\{.*\}", text, re.S)
        reco = json.loads(m.group(0)) if m else {"cards": [], "message": ""}

        # 3) HTML 조립 (이전 코드 복붙)
        html_parts = [
            "<!doctype html><html><head><meta charset='utf-8'><title>Destination Recommendations</title>"
            "<style>body{font-family:sans-serif}section{margin:8px;padding:8px;"
            "border:1px solid #ccc;width:320px;}img{width:140px;height:140px;"
            "object-fit:cover;margin:2px;border-radius:4px;}p{margin:6px 0;}</style>"
            "</head><body>",
            f"<h2>Query: {question}</h2><div style='display:flex;flex-wrap:wrap;'>",
        ]
        for card in reco["cards"]:
            html_parts.append(
                "<section>"
                f"<h3>{card['city']} (score {card['score']:.2f})</h3>"
            )
            # photos
            for url in card.get("photos", []):
                html_parts.append(
                    f"<img src='{url}'/>"
                )
            # description
            if card.get("description"):
                html_parts.append(
                    f"<p>{card['description']}</p>"
                )
            # hashtags
            if card.get("hashtags"):
                tags = " ".join(card["hashtags"])
                html_parts.append(
                    f"<p style='color:#777;font-size:0.9em;'>{tags}</p>"
                )
            html_parts.append("</section>")
        html_parts.append("</div></body></html>")

        html = "\n".join(html_parts)
        # 4) 파일로 저장
        tmp_path = "./tmp/dest_reco_test.html"
        os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(html)

        # 5) html_path 포함 응답
        return {
            "intent": "dest_reco",
            **reco,
            "html_path": tmp_path,
        }

    return {"intent": "unhandled", "message": "지원하지 않는 요청입니다."}

@app.post("/chat")
async def chat(req: Dict[str, str]):
    q = req.get("query", "")
    return JSONResponse(content=await reply_json(q))

# CLI
if __name__ == "__main__":
    print("✈️ AI Flight Assistant — ENTER 빈줄 종료\n")
    while True:
        q = input("🗨 질문: ").strip()
        if not q: break
        res = asyncio.run(reply_json(q))
        print(_json_safe(res), "\n")
        if res.get("intent") == "dest_reco":
            print(f"👉 HTML saved to {res.get('html_path')}")
