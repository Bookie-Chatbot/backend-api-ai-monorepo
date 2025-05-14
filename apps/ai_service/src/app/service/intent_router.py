# apps/ai_service/src/app/service/intent_router.py
from __future__ import annotations
import json, datetime as dt, re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

TODAY = dt.date.today().isoformat()

# 1) LLM이 반드시 채워야 할 키 2개만 정의
response_schemas = [
  ResponseSchema(name="intent",
                 description="'price_search' 또는 'dest_reco' 중 하나"),
  ResponseSchema(name="arguments",
                 description="intent가 price_search일 때는, 항공권 검색 파라미터(JSON) /  intent가 dest_reco일 때는 추천 키워드")
]

parser = StructuredOutputParser.from_response_schemas(response_schemas)

# 2) 프롬프트

# intent → price_search | dest_reco

PROMPT_TMPL = (
    "너는 항공권/여행지 추천 챗봇의 '의도·슬롯 추출기'다.\n"
    "규칙\n"
    "0. 의도는 price_search | dest_reco 중 하나이다.\n"
    "1. 반드시 JSON 한 줄만 출력 (주석·개행 불가)\n"
    "2. IATA 코드는 3-글자 대문자(예: ICN, LHR). 두 글자 약칭(CN) → ICN 추론\n"
    "3. 예산 ‘…만원 이하/이상’ → maxPrice(정수, KRW)\n"
    "4. ‘논스톱·직항·non_stop’ → nonStop(Boolean)\n"
    "5. 날짜·기간은 ISO-8601 (YYYY-MM-DD)\n\n"
    "### 예시 (price_search)\n"
    "1) \"ICN-LHR 2025-11-05 편도, non_stop true, 200만 원 이하\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"LHR\",\"departureDate\":\"2025-11-05\",\"maxPrice\":2000000,\"nonStop\":true}}}}\n"
    "2) \"CN-LHR 2025-11-05 편도, non_stop true, 200만 원 이하\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"LHR\",\"departureDate\":\"2025-11-05\",\"maxPrice\":2000000,\"nonStop\":true}}}}\n"
    "3) \"인천→도쿄 편도 5월 15일, 50만원 이하\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"HND\",\"departureDate\":\"2025-05-15\",\"maxPrice\":500000}}}}\n"
    "4) \"인천에서 뉴욕 가는 왕복 항공권 200만원 이하로 2025년 8월 중에 찾아줘\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"JFK\",\"departureDate\":\"2025-08-01\",\"returnDate\":\"2025-08-31\",\"maxPrice\":2000000}}}}\n"
    "5) \"ICN-SEA 2025-10-05 출발, 2025-10-20 돌아오는 편도로 150만 원 이하로 부탁해\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"SEA\",\"departureDate\":\"2025-10-05\",\"returnDate\":\"2025-10-20\",\"maxPrice\":1500000}}}}\n"
    "6) \"ICN→HND 2025/06/10 편도 30만 원 이하\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"HND\",\"departureDate\":\"2025-06-10\",\"maxPrice\":300000}}}}\n"
    "7) \"인천에서 파리 비즈니스석 왕복으로 6월 중 최대 500만원까지 추천해줘\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"CDG\",\"departureDate\":\"2025-06-01\",\"returnDate\":\"2025-06-30\",\"maxPrice\":5000000,\"travelClass\":\"BUSINESS\"}}}}\n"
    "8) \"ICN-FRA 비즈니스 클래스 2025-07-01부터 2025-07-10까지, 400만 원 이하\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"FRA\",\"departureDate\":\"2025-07-01\",\"returnDate\":\"2025-07-10\",\"maxPrice\":4000000,\"travelClass\":\"BUSINESS\"}}}}\n"
    "9) \"인천에서 로스앤젤레스 가는 2025-09-01 왕복, 성인 2·어린이 1·유아 1, 300만원 이하\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"LAX\",\"departureDate\":\"2025-09-01\",\"returnDate\":\"2025-09-15\",\"maxPrice\":3000000,\"adults\":2,\"children\":1,\"infants\":1}}}}\n"
    "10) \"ICN-LAX 2025-12-15→2025-12-30, adults=1 children=2 infants=1, 700만원 이하로 찾아줘\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"LAX\",\"departureDate\":\"2025-12-15\",\"returnDate\":\"2025-12-30\",\"maxPrice\":7000000,\"adults\":1,\"children\":2,\"infants\":1}}}}\n"
    "11) \"인천에서 런던까지 논스톱으로 8월 중 150만원 이하\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"LHR\",\"departureDate\":\"2025-08-01\",\"returnDate\":\"2025-08-31\",\"maxPrice\":1500000,\"nonStop\":true}}}}\n"
    "12) \"ICN-LHR 2025-11-05 편도, non_stop true, 200만 원 이하\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"LHR\",\"departureDate\":\"2025-11-05\",\"maxPrice\":2000000,\"nonStop\":true}}}}\n"
    "13) \"인천에서 방콕 가는 왕복, 대한항공 포함해서 100만원 이하로\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"BKK\",\"departureDate\":\"2025-06-01\",\"returnDate\":\"2025-06-10\",\"maxPrice\":1000000,\"includedAirlineCodes\":\"KE\"}}}}\n"
    "14) \"ICN-BKK 2025-10-10 편도, 제외 항공사: KE, 30만 원 이하\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"BKK\",\"departureDate\":\"2025-10-10\",\"maxPrice\":300000,\"excludedAirlineCodes\":\"KE\"}}}}\n"
    "15) \"다음 주 토요일에 인천에서 상하이 가는 제일 저렴한 티켓 보여줘\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\n"
    "\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"PVG\",\n"
    "\"departureDate\":\"${{TODAY}}\"}}}}\n"
    "16) \"내일 출발 ICN-SIN이 20만원 안 되는 항공편 있을까?\"\n"
    "   ➜ {{\"intent\":\"price_search\",\"arguments\":{{\n"
    "\"originLocationCode\":\"ICN\",\"destinationLocationCode\":\"SIN\",\n"
    "\"departureDate\":\"${{TODAY}}\",\"maxPrice\":200000}}}}\n\n"
    "### 예시 (dest_reco)\n"
    "16) \"유럽에서 맛집 많은 도시 어디 갈까?\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"region\":\"europe\",\"tag\":\"foodie\"}} }}\n"
    "17) \"5월에 1인 50만원 이하로 해변 추천해줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"month\":\"2025-05\",\"budget\":500000,\"tag\":\"beachlife\"}} }}\n"
    "18) \"가족 여행으로 갈 만한 도시는 어디가 좋을까?\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"familytravel\"}} }}\n"
    "19) \"혼자 가기 좋은 도시 추천해줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"solotravel\"}} }}\n"
    "20) \"휴식할 수 있는 럭셔리 여행지 알려줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"luxurytravel\",\"mood\":\"relaxation\"}} }}\n"
    "\n"
    "# — 기본 추천 요청\n"
    "21) \"동유럽에서 혼자 여행하기 좋은 도시 추천해 줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"region\":\"easterneurope\",\"tag\":\"solotravel\"}} }}\n"
    "22) \"가족 여행으로 갈 만한 유럽 도시 어디 있을까?\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"region\":\"europe\",\"tag\":\"familytravel\"}} }}\n"
    "23) \"5월에 예산 50만 원으로 갈 만한 해변 휴양지 추천해 줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"month\":\"2025-05\",\"budget\":500000,\"tag\":\"beachlife\"}} }}\n"
    "24) \"미식가를 위한 맛집 많은 유럽 도시 알려줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"region\":\"europe\",\"tag\":\"foodie\"}} }}\n"
    "25) \"럭셔리 여행으로 휴식하기 좋은 도시 추천 부탁해\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"luxurytravel\",\"mood\":\"relaxation\"}} }}\n"
    "\n"
    "# — 테마·무드 기반\n"
    "26) \"자연 경관이 아름다운 휴양지 추천해 줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"nature\",\"mood\":\"scenic\"}} }}\n"
    "27) \"역사·문화 체험하기 좋은 도시 어디야?\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"culturetrip\"}} }}\n"
    "28) \"사진 찍기 좋은 인스타그램 핫플레이스 여행지 추천해 줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"instagrammable\"}} }}\n"
    "29) \"와이너리 투어 즐길 수 있는 유럽 도시 알려줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"region\":\"europe\",\"tag\":\"winerytour\"}} }}\n"
    "30) \"웰니스·요가 리트릿 할 만한 여행지 추천해 줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"wellness\"}} }}\n"
    "\n"
    "# — 예산·기간·특수 조건\n"
    "31) \"여름 피서를 갈 만한 국내외 여행지 추천해 줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"summergetaway\"}} }}\n"
    "32) \"한 달 머무르기에 좋은 디지털 노마드 도시 있을까?\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"digitalnomad\",\"duration\":\"P1M\"}} }}\n"
    "33) \"저예산(30만 원 이하)으로 여행할 수 있는 동남아 도시 추천해 줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"region\":\"southeastasia\",\"budget\":300000,\"tag\":\"budgettravel\"}} }}\n"
    "34) \"어린이 동반 가족이 안전하게 갈 수 있는 여행지 알려줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"familytravel\",\"safety\":true}} }}\n"
    "35) \"2인 커플이 갈 만한 로맨틱 여행지 추천해 줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"romantic\"}} }}\n"
    "\n"
    "# — 언어·안전·환경\n"
    "36) \"영어 못 해도 안전하게 돌아다닐 수 있는 도시 추천해 줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"language\":\"nonenglish\",\"safety\":true}} }}\n"
    "37) \"친환경(Eco-travel) 숙박·활동이 가능한 여행지 알려줘\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"ecotravel\"}} }}\n"
    "38) \"치안이 좋아 여성 혼자 가기에도 안전한 도시 어디야?\"\n"
    "   ➜ {{ \"intent\":\"dest_reco\", \"arguments\":{{\"tag\":\"safetravel\",\"audience\":\"female\"}} }}\n"
    "{format_instructions}\n\n질문: {question}"
)


llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0,
    model_kwargs={       # 경고 제거
        "response_format":{"type": "json_object"}
    }
)

def classify(question: str) -> Dict[str, Any]:
    """자연어 → {intent, arguments}"""
    prompt = PROMPT_TMPL.format(
        question=question,
        format_instructions=parser.get_format_instructions()
    )
    try:
        raw = llm.invoke([("user", prompt)])
        return json.loads(raw.content)
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
