 # chains/alert_price_drop.py
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
#rom chatbot_contents.alert_price_drop import AlertDispatchPriceDrop
"""
# PriceDropDispatch 전용 파서
price_drop_parser = PydanticOutputParser(pydantic_object=AlertDispatchPriceDrop)

# 가격 알림(price_drop) 설정을 위한 1차 질문 프롬프트

price_drop_prompt = PromptTemplate.from_template(
    '''
항공권 가격 알림을 설정해 드릴게요! 아래 스키마에 맞춰 `contents`를 반환해 주세요.
- intent: ALERT_DISPATCH_PRICE_DROP (자동 설정)
- channel: email 또는 kakao
- userId: 사용자 ID
- message: "OO원 이하로 떨어지면 알림을 받으시길 원하시나요? 알림을 받을 이메일(또는 카카오톡 ID)를 입력해주세요."
- payload: {{
    route: "ICN→LAX",
    targetPrice: 1200000,
    currency: "KRW"
  }}

{format_instructions}
'''
)

price_drop_chain = (
    price_drop_prompt
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | price_drop_parser
)
"""