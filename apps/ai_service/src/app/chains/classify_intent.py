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
