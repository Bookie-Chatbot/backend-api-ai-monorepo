# app/question_handler.py

from app.service.prompts import sql_query_map
from app.sql_executor import pseudo_execute_sql
from app.service.utils import utils
from langchain_openai import ChatOpenAI
from app.service.prompts import PromptTemplate

def handle_question(question, classification_key, rag_chain, db_data, sql_summary_chain, retriever):
    """
    분류 결과에 따라 SQL 조회 후 LLM 후처리를 하되,
    항상 PDF RAG도 병행하여 참고하는 로직
    """
    # 1. PDF RAG 먼저 수행
    context_docs = retriever.invoke(question)
    pdf_answer = rag_chain.invoke(question)  # PDF 기반 응답
    pdf_context = utils.format_docs(context_docs)

    # 2. SQL 조회 여부 결정
    if classification_key in sql_query_map:
        query_key = sql_query_map[classification_key]
        # 가상 DB에서 SQL 쿼리 
        sql_raw_result = pseudo_execute_sql(query_key, db_data)
        # SQL 결과를 자연어 요약
        sql_answer = sql_summary_chain.invoke({"sql_result": str(sql_raw_result)})

        # 3. PDF + SQL 결과를 통합하여 최종 답변 생성
        final_answer = merge_pdf_and_sql2(question, pdf_context, pdf_answer, sql_answer)
    else:
        # SQL로 분류되지 않았다면, PDF만 사용
        final_answer = pdf_answer

    return final_answer


def merge_pdf_and_sql1(question, pdf_context, pdf_answer, sql_answer):
    """
    간단히 두 결과를 합친 뒤, 최종 모델에 다시 한번 '병합' 요청할 수도 있고,
    아니면 문자열로 단순 합쳐서 반환할 수도 있음.
    일단은 

    '문자열 단순 병합 + 안내 문구' 예시.
    추후 필요하면 이때 별도의 LLM 체인을 또 만들 수도
    """
    merged_text = f"""
[문서 기반 응답]
{pdf_answer}

[SQL 기반 응답]
{sql_answer}

사용자가 원하는 내용을 종합적으로 안내해 주세요.
"""
    return merged_text


def merge_pdf_and_sql2(question, pdf_context, pdf_answer, sql_answer):
    """
    PDF 응답(pdf_answer) + SQL 응답(sql_answer)을 통합하는 LLM 프롬프트.
    사용자 질문(question)의 본래 의도(목적)을 절대 잊지 말도록 강조.
    """
    merge_prompt = PromptTemplate(
        input_variables=["pdf_answer", "sql_answer", "question"],
        template="""
사용자의 질문:
{question}

[PDF 기반 응답]
{pdf_answer}

[SQL 기반 응답]
{sql_answer}

위 두 정보를 종합하여, 질문자가 궁극적으로 알고자 하는 목표를 절대 놓치지 마세요.

- 사용자 질문에 '가장 저렴한 방'과 같이 가격 관련 요구가 있다면, 반드시 가격정보를 포함하세요.
- '호텔 정책'처럼 DB 범위를 넘어서는 정보는 PDF 응답을 참고하여 보강하세요.
- 중복되거나 모호한 표현은 피하고, 사용자 의도에 꼭 맞춘 구체적 답변을 작성하세요.
"""
    )
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    
    final_merged = llm.invoke(
        merge_prompt.format(
            pdf_answer=pdf_answer,
            sql_answer=sql_answer,
            question=question
        )
    )
    return final_merged
