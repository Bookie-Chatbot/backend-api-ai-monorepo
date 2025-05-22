# chains/alert_cancel_deadline.py
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from chatbot_contents.alert_cancel_deadline import AlertDispatchCancelDeadline

# CancelDeadlineDispatch 전용 파서
cancel_deadline_parser = PydanticOutputParser(pydantic_object=AlertDispatchCancelDeadline)

# 취소 마감일(cancel_deadline) 알림 설정을 위한 1차 질문 프롬프트
cancel_deadline_prompt = PromptTemplate.from_template(
    '''
예약 취소 마감일 알림을 설정해 드릴게요! 아래 스키마에 맞춰 `contents`를 반환해 주세요.
- intent: ALERT_DISPATCH_CANCEL_DEADLINE
- channel: email 또는 kakao
- userId: 사용자 ID
- message: "OO 예약의 취소 마감일이 YYYY-MM-DD 입니다. 알림을 원하시면 이메일(또는 카카오톡 ID)를 입력해주세요."
- payload: {{

    bookingId: "ABC123",
    deadline: "2025-06-10"
  }}

{format_instructions}
'''
)

cancel_deadline_chain = (
    cancel_deadline_prompt
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | cancel_deadline_parser
)
