# chains/alert_dispatch_router.py
"""
from langchain_core.runnables import RunnableLambda
from chains.alert_price_drop import price_drop_chain
from chains.alert_wx_risk import wx_risk_chain
from chains.alert_cancel_deadline import cancel_deadline_chain

def route_alert_dispatch(inputs: dict):
    # inputs에는 이미 intent, question, chat_history 등이 포함되어 있고,
    # eventType은 classification 단계에서 채워진 상태라고 가정
    eventType = inputs["contents"]["eventType"]
    if eventType == "price_drop":
        return price_drop_chain.invoke(inputs)
    if eventType == "wx_risk":
        return wx_risk_chain.invoke(inputs)
    if eventType == "cancel_deadline":
        return cancel_deadline_chain.invoke(inputs)
    # fallback
    return {
        "intent": "ALERT_DISPATCH",
        "contents": {
            "message": "죄송해요, 처리할 수 없는 알림 유형이에요."
        }
    }

alert_dispatch_router = RunnableLambda(route_alert_dispatch)
"""
