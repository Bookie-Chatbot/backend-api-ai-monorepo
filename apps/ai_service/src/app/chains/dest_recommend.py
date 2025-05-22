from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from chatbot_contents.dest_recommend import DestRecommendContent
# for window
# from packages.chatbot_contents.dest_recommend import DestRecommendContent
import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda


load_dotenv()

dest_recommend_parser = PydanticOutputParser(pydantic_object=DestRecommendContent)


# 2) 파싱 함수 + RunnableLambda 래퍼
def parse_or_passthrough(text: str):
    try:
        # 파싱에 성공하면 Pydantic 모델 반환
        return dest_recommend_parser.parse(text)
    except Exception:
        # 실패하면 원본 문자열 그대로 반환
        return text

safe_parser = RunnableLambda(parse_or_passthrough)

dest_recommend_chain = (
    PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에, 2줄짜리 설명을 작성해주고, ‘부엉이 부키’라는 귀여운 부엉이처럼 대답하면서, 모든 답변 끝에 ‘부키!’를 붙여줘."
        "추천 도시 아래 JSON 스키마에 맞춰 반환해줘.\n"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
    )
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | safe_parser
)
