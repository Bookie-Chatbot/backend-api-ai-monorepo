# ── intent_router.py  ― “질문 → 의도/슬롯 JSON” ─────────────
from __future__ import annotations
import json, datetime as dt, re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage


TODAY = dt.date.today().isoformat()

# ❶  예시(few-shot) + 오늘 날짜 포함 시스템 프롬프트
# intent_router.py  (SYSTEM 프롬프트 부분만)

TODAY = dt.date.today().isoformat()

SYS = f"""
너는 항공권 챗봇의 '의도·슬롯 추출기'야.
- **오늘 날짜**: {TODAY}
- 사용자가 ‘얼마 이하’, ‘이번주·다음달’ 식으로 말할 때 → ISO-8601 `YYYY-MM-DD` 로 변환
- 가능한 의도는 오직 하나: `price_search`
- 응답은 **JSON 한 줄**

### 예시
json

{{"intent":"price_search","arguments":{{"originLocationCode":"ICN","destinationLocationCode":"FRA","departureDate":"{TODAY[:-2]}06-20","maxPrice":700000}}}}

"""

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=SYS), 
("human", "{question}") ])


llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

def classify(question: str) -> Dict[str, Any]:
    """question → {"intent":…, "arguments":…}  (JSON)"""
   # ChatPromptTemplate 은 messages 리스트를 돌려줘야 하므로 ↓ 이렇게!
    messages = prompt.format_messages(question=question)
    resp = llm.invoke(messages)
    try:
        return json.loads(resp.content)
    except Exception:
        return {"intent": None, "arguments": {}}

# ── 긴급 Fallback (정규식) ― 기존 로직 유지 ───────────────
def regex_fallback(question: str) -> Dict[str, Any]:
    pat_iata = r"\b[A-Z]{3}\b"
    pat_date = r"\b20\d{2}[./-]\d{2}[./-]\d{2}\b"
    codes  = re.findall(pat_iata,  question)
    dates  = re.findall(pat_date, question)
    if len(codes) >= 2 and dates:
        return {
            "intent": "price_search",
            "arguments": {
                "originLocationCode":  codes[0],
                "destinationLocationCode": codes[1],
                "departureDate": dates[0].replace(".", "-").replace("/", "-")
            },
        }
    return {"intent": None, "arguments": {}}
