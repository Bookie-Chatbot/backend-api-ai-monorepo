# chains/fallback.py
from langchain_core.runnables import RunnableLambda

# 1) 단순 fallback 응답 함수
def _fallback_run(inputs: dict) -> dict:
    return {
        "intent": "FALLBACK",
        "contents": {
            "message": "죄송해요, 해당 기능은 아직 지원하지 않습니다."
        }
    }

# 2) RunnableLambda으로 래핑
fallback_chain = RunnableLambda(_fallback_run)
