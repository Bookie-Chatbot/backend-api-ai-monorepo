# intent_router.py

from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from chatbot_contents.chat_message import ChatbotMessage  # Discriminated Union 모델

# 1) PydanticOutputParser 초기화
output_parser = PydanticOutputParser(pydantic_object=ChatbotMessage)

# 2) PromptTemplate 정의
prompt = PromptTemplate(
    template=(
        "아래 JSON 스키마에 맞춰 한 줄로만 응답하세요. 주석·개행 금지.\n"
        "{format_instructions}\n"
        "질문: {user_input}"
    ),
    input_variables=["format_instructions", "user_input"]
)

# 3) LLM 설정
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0,
    model_kwargs={"response_format": {"type": "json_object"}}
)

def classify_and_parse(question: str) -> ChatbotMessage:
    # 프롬프트 완성
    formatted = prompt.format(
        format_instructions=output_parser.get_format_instructions(),
        user_input=question
    )
    # LLM 호출
    response = llm([("user", formatted)])
    raw = response.content

    # 4) PydanticOutputParser로 JSON → ChatbotMessage 객체 파싱
    try:
        chat_msg: ChatbotMessage = output_parser.parse(raw)
    except Exception as e:
        # 파싱 실패 시 예외 처리 로직
        raise ValueError(f"Structured output parsing failed: {e}")

    return chat_msg

# 사용 예시
if __name__ == "__main__":
    q = "인천에서 뉴욕 가는 항공권 7월 중 200만원 이하로 찾아줘"
    msg = classify_and_parse(q)
    print("Intent:", msg.intent)
    print("Contents:", msg.contents)
