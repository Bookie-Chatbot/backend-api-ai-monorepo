# app/prompts.py

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from app.sql_queries import sql_query_map

###############################################################################
# 1) SQL vs. PDF 분류 프롬프트 체인 (RunnableSequence 사용, 구체적 지시문 추가)
###############################################################################

def create_prompt():
    """
    분류용 RunnableSequence 체인을 생성해 반환.
    사용자 질문을 입력받아, 아래 옵션 중 하나(예: available_rooms, pdf_only 등)를 정확히 판단.
    """
    classification_prompt = PromptTemplate(
        input_variables=["question"],
        template="""
다음은 사용자 질문입니다:

"{question}"

사용자의 질문을 토대로, 아래 주어진 SQL 쿼리 유형 옵션 중 하나를 고르거나,
만약 SQL로 처리할 수 없는(문서 내 정보가 필요하거나, SQL 범위를 벗어나는) 경우에는 "pdf_only"라고만 출력하세요.

아래는 선택 가능한 SQL 옵션과 구체적인 사용 예시입니다:

1) available_rooms
   - 예: "예약 가능한 방이 몇 개인가요?", "가장 저렴한 방이 있나요?", "현재 어떤 객실이 비어있나요?"
   - 가격(Price) 필드가 DB에 존재. 방의 개수나 가격을 확인할 때 유용.
2) upcoming_reservations
   - 예: "다가오는 예약 일정이 어떻게 되나요?", "조만간 진행될 예약 목록을 보고 싶어요."
   - 주로 예약 날짜, 예약 상태 등 DB에서 확인할 때 유용.
3) customer_reservation
   - 예: "특정 고객(홍길동)의 예약 내역을 알려주세요."
   - 고객별 예약 조회가 필요할 때 사용.
4) revenue_summary
   - 예: "이번 달(또는 올해)의 예약 총 매출은 얼마인가요?", "수익 요약을 알고 싶어요."
   - 수익(가격 합산)을 계산할 때.
5) reservation_details
   - 예: "예약 번호 1234에 대한 상세 정보를 알려주세요."
   - 특정 예약 번호에 대한 자세한 내용(체크인, 체크아웃 등)이 필요할 때.

6) pdf_only
   - 위 SQL 옵션으로 해결이 안 되거나, PDF 문서(이용약관, 예약 취소 정책 등)를 참고해야 하는 경우.
   - 예: "취소 정책이 어떻게 되나요?", "호텔 이용 규정 알려주세요."

주의사항:
- 사용자가 "가장 저렴한 방" 등 가격 정보를 묻는 경우, DB의 price 필드를 
- 사용자가 "취소 정책", "규정" 등 DB에 없는 정보를 요청하면 "pdf_only".
- 반환은 오직 위 6가지 중 하나로만 작성하십시오 (다른 문구나 설명 없이).

User Question: {question}
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

# 2) SQL 결과 요약 프롬프트 체인 (RunnableSequence 사용)

def create_sql_summary_prompt():
    """
    SQL 실행 결과를 입력받아,
    자연어로 요약한 답변을 생성하는 RunnableSequence 체인을 생성
    """
    summary_prompt = PromptTemplate(
        input_variables=["sql_result"],
        template="""
다음은 가상 DB에서 조회된 결과입니다:

{sql_result}

이 정보를 바탕으로, 사용자의 질문에 대한 친절하고 정확한 답변을 작성하세요.
가격 관련 정보가 포함되어 있다면 가격도 함께 명확히 안내하세요.
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

# 3) PDF RAG용 기본 프롬프트 

DEFAULT_PROMPT = PromptTemplate(
    template="질문: {question}\n\n문서: {context}\n\n답변:",
    input_variables=["question", "context"]
)
