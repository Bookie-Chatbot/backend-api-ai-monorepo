from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from chatbot_contents.dest_recommend import DestRecommendContent
import os
from dotenv import load_dotenv

load_dotenv()

dest_recommend_parser = PydanticOutputParser(pydantic_object=DestRecommendContent)

dest_recommend_chain = (
    PromptTemplate.from_template(
        "목적지 추천 결과를 아래 JSON 스키마에 맞춰 `contents`만 반환하세요.\n"
        "{format_instructions}\n"
        "질문: {question}"
    )
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | dest_recommend_parser
)
