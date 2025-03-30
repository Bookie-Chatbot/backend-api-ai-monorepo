# app/prompts.py

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from app.sql_queries import sql_query_map

# 1) SQL vs. PDF 분류 프롬프트 체인 (RunnableSequence 사용, 구체적 지시문 추가)

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
