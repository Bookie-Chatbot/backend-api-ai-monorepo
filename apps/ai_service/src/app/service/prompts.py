# app/prompts.py

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from app.sql_queries import sql_query_map

# 1) SQL vs. PDF 분류 프롬프트 체인 (RunnableSequence 사용, 구체적 지시문 추가)

def create_prompt():
    """
    DB 구조/필드 정보를 프롬프트에 포함, 사용자 질문이 DB로 해결 가능한지 좀 더 세밀하게 판단하도록 유도.
    """
    classification_prompt = PromptTemplate(
        input_variables=["question"],
        template="""
다음은 호텔·항공 예약 시스템의 DB 스키마 개요입니다:

[User] 테이블
- id, name, email, password, created_at
- 특정 사용자의 ID(예: user_id=1)가 여기서 할당됩니다.

[Flight] 테이블
- id, airline, departure, arrival, departure_time, arrival_time, price, available_seats, last_updated
- 항공편 정보(출발지/도착지, 출발/도착 시간 등)가 저장됩니다.

[Reservation] 테이블
- id, airline, departure, arrival, departure_time, arrival_time, price, available_seats, last_updated
- 사용자 예약 내역을 이 테이블에 저장합니다 (실제론 user_id 등이 필요하지만, 가상 예시임).

[Hotel] 테이블
- id, name, location, price, available_rooms, last_updated
- 호텔 관련 정보(가격, 가용 객실 수 등).

기타 테이블(Hotel, QueryLog, AdminSettings 등)은 생략.

[사용 가능한 SQL 옵션]
1) available_rooms
   - 예: "예약 가능한 방이 몇 개인가요?", "가장 저렴한 방이 있나요?"
   - Hotel의 price, available_rooms를 조회
2) upcoming_reservations
   - 예: "다가오는 예약 일정이 어떻게 되나요?"
   - Reservation, Flight의 departure_time/arrival_time 등
3) customer_reservation
   - 예: "특정 고객(홍길동)이 예약한 항공편, 도착 시간을 알고 싶어요."
   - Reservation or Flight에서 user_id 혹은 customer_name을 기준 조회
4) revenue_summary
   - 예: "이번 달 예약 총 매출은 얼마인가요?"
   - price 필드 합산
5) reservation_details
   - 예: "예약 번호 1234의 상세 정보를 알려주세요."
   - Reservation 테이블에서 특정 id 조회

6) pdf_only
   - 위 SQL 옵션으로 해결이 안 되거나, DB 테이블에 없는 정보(예: 취소 정책, 호텔 규정)는 PDF 문서를 참고.

사용자 질문이 DB로 해결 가능하면 적절한 SQL 옵션을 고르세요.
- 단, 규정·약관·정책 등 DB에 없는 정보면 pdf_only.

규칙:
- 오직 아래 6가지 중 하나를 답으로 내놓으세요 (기타 설명 없이).
- user1 같은 특정 사용자가 예약한 항공편 정보를 묻는 경우라면 "customer_reservation" 선택이 유력.
- "가장 저렴한 방"이면 "available_rooms".
- "호텔 취소 정책"이면 "pdf_only".

User Question:
{question}
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
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_openai import ChatOpenAI

def create_sql_summary_prompt():
    """
    SQL 실행 결과와 사용자 원본 질문(user_question)을 입력받아,
    자연어로 요약한 답변을 생성하는 RunnableSequence 체인을 생성.
    """
    summary_prompt = PromptTemplate(
        # user_question도 input_variables에 추가
        input_variables=["sql_result", "user_question"],
        template="""
사용자가 다음과 같은 질문을 했습니다:
"{user_question}"

그리고 아래는 가상 DB에서 조회된 결과입니다:
{sql_result}

위 정보를 종합하여, 사용자의 질문 의도를 놓치지 말고 친절하고 정확한 답변을 작성하세요.

만약 가격(price) 관련 정보가 있으면, 구체적인 금액을 명확히 안내하세요.
또한 사용자가 묻고자 하는 최종 목적(예: 가장 저렴한 방, 특정 예약 정보 등)을
간과하지 말고, 그 목적에 맞게 답변을 보완하세요.
"""
    )
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    output_parser = StrOutputParser()
    
    chain = RunnableSequence(
        {
            "sql_result": RunnablePassthrough(),
            "user_question": RunnablePassthrough()
        }
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
