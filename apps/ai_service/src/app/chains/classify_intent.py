from langchain.prompts import PromptTemplate
from langchain.output_parsers.pydantic import PydanticOutputParser
from chatbot_contents.intents import IntentOnly
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


# 1) 의도 분류용 PydanticOutputParser
intent_parser = PydanticOutputParser(pydantic_object=IntentOnly)

# 2) 분류 프롬프트
classify_prompt = PromptTemplate.from_template(
   "아래 JSON 스키마에 맞춰, intent만 한 줄 JSON으로 응답하세요.\n"
   "cheapest date는, 가장 저렴한 날짜를 찾는 질문에 대한 응답입니다.\n"
   "weather summary는, 날씨 요약을 요청하는 질문에 대한 응답입니다.\n"
    "price search는, 항공권 종류들의 검색 조회하는 질문에 대한 응답입니다.\n"
    "dest recommend는, 여행지 추천을 요청하는 질문에 대한 응답입니다.\n"
    "alert dispatch는, 가격 알림 설정을 요청하는 질문에 대한 응답입니다.\n"
    "price analysis는, 가격 분석을 요청하는 질문에 대한 응답입니다.\n"
    "예시 [cheapest date]: 파리행 항공권 제일 싼날/싼거 알려줘\n"
   "{format_instructions}\n"
   "# 이전 대화 내역 (role:content 리스트):\n"
   "{chat_history}\n"
   "질문: {question}"
)

# 3) 분류 체인
classification_chain = (
    classify_prompt
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | intent_parser
)
