# chains/alert_wx_risk.py
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from chatbot_contents.alert_wx_risk import AlertDispatchWxRisk

# WxRiskDispatch 전용 파서
wx_risk_parser = PydanticOutputParser(pydantic_object=AlertDispatchWxRisk)

# 기상 위험(wx_risk) 알림 설정을 위한 1차 질문 프롬프트
wx_risk_prompt = PromptTemplate.from_template(
    '''
여행 일정 중 기상 위험 알림을 설정해 드릴게요! 아래 스키마에 맞춰 `contents`를 반환해 주세요.
- intent: ALERT_DISPATCH_WX_RISK
- channel: email 또는 kakao
- userId: 사용자 ID
- message: "OO 지역에 위험 기상(태풍, 폭우 등)이 예상됩니다. 알림을 원하시면 이메일(또는 카카오톡 ID)를 입력해주세요."
- payload: {{
    location: "LAX",
    riskType: "typhoon",
    effectiveDate: "2025-06-20"
  }}

{format_instructions}
'''
)

wx_risk_chain = (
    wx_risk_prompt
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | wx_risk_parser
)