from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from chatbot_contents.price_search import PriceSearchContent
from langchain_core.runnables import RunnableLambda
import os
from dotenv import load_dotenv

load_dotenv()

price_search_parser = PydanticOutputParser(pydantic_object=PriceSearchContent)

# 2) 파싱 함수 + RunnableLambda 래퍼
def parse_or_passthrough(text: str):
    try:
        # 파싱에 성공하면 Pydantic 모델 반환
        return price_search_parser.parse(text)
    except Exception:
        # 실패하면 원본 문자열 그대로 반환
        return text

safe_parser = RunnableLambda(parse_or_passthrough)


# 3) 체인 정의
price_search_chain = (
    PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에, 2줄짜리 설명을 작성해주고, ‘부엉이 부키’라는 귀여운 부엉이처럼 대답하면서, 모든 답변 끝에 ‘부키!’를 붙여줘."
        "가격 조회 결과를 아래 JSON 스키마에 맞춰 반환해줘.\n"
        "{format_instructions}\n"
        "질문: {question}"
    )
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | safe_parser
)

{
  "intent": "PRICE_SEARCH",
  "contents": {
    "message": "가격을 검색해보니, 2025년 6월 15일 출발, 2025년 6월 22일 귀국 항공편이 있습니다. 부키!",
    "flights": [
      {
        "origin": "ICN",
        "destination": "LAX",
        "departureDate": "2025-06-15",
        "returnDate": "2025-06-22",
        "price": 1250000.0,
        "currency": "KRW",
        "bookingUrl": "https://booking.example.com/ICN-LAX"
      },
      {
        "origin": "ICN",
        "destination": "LAX",
        "departureDate": "2025-06-15",
        "returnDate": "",
        "price": 1100000.0,
        "currency": "KRW",
        "bookingUrl": ""
      }
    ]
  }
}
