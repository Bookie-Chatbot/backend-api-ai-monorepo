# chains/slot_clarification.py
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from chatbot_contents.slot_clarification import SlotClarificationContent

# SlotClarificationContent 전용 파서
slot_clarification_parser = PydanticOutputParser(pydantic_object=SlotClarificationContent)

# 슬롯 보강을 위한 질문 프롬프트
slot_clarification_prompt = PromptTemplate.from_template(
    '''
필수 정보가 부족합니다. 아래 스키마({format_instructions})에 맞춰
누락된 항목을 알려주세요.
'''
)

slot_clarification_chain = (
    slot_clarification_prompt
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | slot_clarification_parser
)


# chains/fallback.py
from langchain_core.runnables import RunnableLambda

# 단순 fallback 응답 생성
def _fallback_run(inputs: dict) -> dict:
    return {
        "intent": "FALLBACK",
        "contents": {"message": "죄송해요, 해당 기능은 아직 지원하지 않습니다."}
    }

fallback_chain = RunnableLambda(_fallback_run)
