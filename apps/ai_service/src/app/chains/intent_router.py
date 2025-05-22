# chains/intent_router.py

from langchain_core.runnables import RunnableLambda
from chatbot_contents.intents import IntentOnly, Intent
from chains.price_search import price_search_chain, price_search_parser
from chains.dest_recommend import dest_recommend_chain, dest_recommend_parser
from chains.policy_qa import policy_qa_chain, policy_qa_parser
#from chains.alert_dispatch_router import alert_dispatch_router
#from chains.weather_summary import weather_summary_chain, weather_parser


# 지원하지 않는 intent 대응
def fallback_run(question: str):
    return {"message": "죄송해요, 아직 지원하지 않는 기능입니다."}

# Intent → (chain, parser) 맵
INTENT_CHAIN_MAP = {
    Intent.PRICE_SEARCH:   (price_search_chain,   price_search_parser),
    Intent.DEST_RECOMMEND: (dest_recommend_chain, dest_recommend_parser),
    Intent.POLICY_QA:         (policy_qa_chain, policy_qa_parser)
  #  Intent.ALERT_DISPATCH: (alert_dispatch_router, None),
   # Intent.WEATHER_SUMMARY: (weather_summary_chain, weather_parser),



}

def route_and_run(inputs: dict) -> any:
    """
    inputs: {
      intent_only: IntentOnly,
      question: str
    }
    """
    intent_only = inputs["intent_only"]
    question    = inputs["question"]
    history     = inputs.get("chat_history", [])

    chain, parser = INTENT_CHAIN_MAP.get(intent_only.intent, (None, None))
    if not chain:
        return fallback_run(question)

    # 서브체인 실행
    return chain.invoke({
        "question": question,
        "format_instructions": parser.get_format_instructions(),
        "chat_history": history,
    })

# RunnableLambda 에 넘겨주면 classification_chain + question → 바로 결과 반환
router = RunnableLambda(route_and_run)


""""
{
  "intent_only": { "intent": "WEATHER_SUMMARY" },
  "question": "부산의 오늘 날씨 요약과 주의보가 뭐야?",
  "chat_history": [ … ]
}

{
  "intent": "WEATHER_SUMMARY",
  "contents": {
    "location": "Busan",
    "date": "2025-05-21",
    "summary": "구름 조금, 최고 23°C / 최저 15°C",
    "alerts": ["강풍 주의", "해상 풍랑 경보"]
  }
}


"""