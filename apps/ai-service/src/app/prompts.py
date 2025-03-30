# app/prompts.py

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from app.sql_queries import sql_query_map

# 1. SQL vs. PDF 분류 프롬프트 체인 (RunnableSequence 사용)

def create_prompt():
    """
    분류용 RunnableSequence 체인을 생성해 반환
    사용자 질문을 입력받아, 아래 옵션 중 하나(예: available_rooms, pdf_only 등)를 출력
    """
    classification_prompt = PromptTemplate(
        input_variables=["question"],
        template="""
사용자의 질문이 주어집니다.

아래 옵션 중에서 가장 적절한 SQL 쿼리 유형의 키를 하나 선택하세요. 
만약 해당하는 SQL 쿼리가 없고 PDF 문서를 이용해야 한다면 'pdf_only'라고만 출력하세요.

옵션:
- available_rooms: 현재 이용 가능한 객실 목록
- upcoming_reservations: 다가오는 예약 목록
- customer_reservation: 특정 고객의 예약 내역
- revenue_summary: 특정 기간의 총 예약 수익
- reservation_details: 특정 예약 ID에 대한 상세 정보
- pdf_only: SQL로 조회할 내용이 아닐 때

출력은 반드시 위 옵션 중 하나로만 작성하세요 (다른 문구 없이).
Question: {question}
"""
    )
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    output_parser = StrOutputParser()
    
    chain = RunnableSequence(
        {"question": RunnablePassthrough()}
        | classification_prompt
        | llm
        | output_parser
    )
    return chain

# 2. SQL 결과 요약 프롬프트 체인 (RunnableSequence 사용)

def create_sql_summary_prompt():
    """
    SQL 실행 결과(예: dict 또는 list 형태)를 입력받아, 
    자연어로 요약한 답변을 생성하는 RunnableSequence 체인을 생성
    """
    summary_prompt = PromptTemplate(
        input_variables=["sql_result"],
        template="""
다음은 가상 DB에서 조회된 결과입니다:

{sql_result}

이 정보를 바탕으로, 사용자의 질문에 대한 친절하고 정확한 답변을 작성하세요.
"""
    )
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    output_parser = StrOutputParser()
    
    chain = RunnableSequence(
        {"sql_result": RunnablePassthrough()}
        | summary_prompt
        | llm
        | output_parser
    )
    return chain

# 3. PDF RAG용 기본 프롬프트 

DEFAULT_PROMPT = PromptTemplate(
    template="질문: {question}\n\n문서: {context}\n\n답변:",
    input_variables=["question", "context"]
)
