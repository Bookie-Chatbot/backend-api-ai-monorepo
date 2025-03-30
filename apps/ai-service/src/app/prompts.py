 # 프롬프트 템플릿 관련 코드
from langchain.prompts import PromptTemplate

DEFAULT_PROMPT = PromptTemplate(
    template="질문: {question}\n\n문서: {context}\n\n답변:",
    input_variables=["question", "context"]
)
