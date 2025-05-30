# chains/alert_price_drop.py
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
# from chatbot_contents.alert_price_drop import AlertDispatchPriceDrop

from packages.chatbot_contents.alert_dispatch import AlertDispatchContent
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda, RunnableMap

# PriceDropDispatch 전용 파서
price_drop_parser = PydanticOutputParser(pydantic_object=AlertDispatchContent)

def parse_or_passthrough(text: str):
    try:
        return price_drop_parser.parse(text)
    except Exception:
        return text

safe_parser = RunnableLambda(parse_or_passthrough)

price_drop_chain = ({
    "question": lambda x: x["question"],
    "format_instructions": lambda x: x["format_instructions"],
    "chat_history": lambda x: x.get("chat_history", None), }
    | PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에 설명을 작성해주고, ‘부엉이 부키’라는 귀여운 부엉이처럼 대답하면서, 모든 답변 끝에 ‘부키!’를 붙여줘."
        "가장 최신 대화내역을 최대 5개까지 확인해서 사용자가 알림을 요청하는 항공편에 대해 알림 요청 처리해줘."
        "사용자가 본인이 원하는 price_threshold를 제시하지 않으면, selling_price에서 10% 할인된 가격을 100의 자리에서 내린 값을 default price_threshold로 생각해."
        "channel은 사용자의 query와 상관 없이 무조건 email이야."
        "사용자가 원하는 price_threshold보다 selling_price가 낮으면(if payload.price_threshold > payload.selling_price), 즉시 '해당 항공편은 이미 목표 가격 아래입니다. 바로 예약 진행할까요?' 로 message 출력해줘"
        "예시 1. 사용자: 마지막에서 두 번째거 150000아래로 떨어지면 알림줘. 부키: 아래 항공편 가격이 150000이하로 떨어지면 이메일로 알려드릴까요?"
        "예시 2. 사용자: 보여준 거 중에 제일 싼거 알림줘. 부키: (최신 대화 내역 5개에서 확인한 항공편 중 selling_price가 가장 작은 것을 고른 후)아래 항공편 가격이 [selling_price*0.9] 이하로 떨어지면 이메일로 알려드릴까요?"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
    )
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | safe_parser
)