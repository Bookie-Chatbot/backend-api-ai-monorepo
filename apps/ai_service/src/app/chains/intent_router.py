# chains/intent_router.py

from langchain_core.runnables import RunnableLambda
from chatbot_contents.intents import IntentOnly, Intent
# for window
# from packages.chatbot_contents.intents import IntentOnly, Intent
from chains.price_search import price_search_chain, price_search_parser
from chains.dest_recommend import dest_recommend_chain, dest_recommend_parser
from chains.policy_qa import create_policy_chain, policy_qa_parser

# 지원하지 않는 intent 대응
def fallback_run(question: str):
    return {"message": "죄송해요, 아직 지원하지 않는 기능입니다."}

# Intent → (chain, parser) 맵
INTENT_CHAIN_MAP = {
    Intent.PRICE_SEARCH:   (price_search_chain,   price_search_parser),
    Intent.DEST_RECOMMEND: (dest_recommend_chain, dest_recommend_parser),
    Intent.POLICY_QA:      (create_policy_chain, policy_qa_parser)
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
