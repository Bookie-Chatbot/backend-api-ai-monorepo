# src/app/prompts.py
# 프롬프트 템플릿 관련 코드
from langchain.prompts import PromptTemplate

DEFAULT_PROMPT = PromptTemplate(
    template="질문: {question}\n\n문서: {context}\n\n답변:",
    input_variables=["question", "context"]
)

def create_prompt(template: str = None, input_variables: list = None):
    """
    프롬프트 템플릿을 생성하는 함수
    기본 템플릿: 질문과 문서에 대한 답변을 요청하는 형식
    """
    if template is None:
        template = DEFAULT_PROMPT.template
    if input_variables is None:
        input_variables = DEFAULT_PROMPT.input_variables

    return PromptTemplate(template=template, input_variables=input_variables)