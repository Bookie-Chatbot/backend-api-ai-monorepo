# search.py

import os
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app import retrievers, chains, utils, embeddings, config
from app.virtual_db import load_virtual_db
from app.prompts import (
    create_prompt, 
    create_sql_summary_prompt,
)
from app.sql_queries import sql_query_map
from app.sql_executor import pseudo_execute_sql
from app.question_handler import handle_question

def main():
    # 1. PDF 벡터스토어 로드 (PDF RAG용)
    vectorstore = embeddings.load_vectorstore()
    print("Loaded persisted vectorstore.")
    
    # 2. Retriever 생성 (PDF 검색용)
    retriever = retrievers.create_retriever(vectorstore, k=3)
    print("Retriever created")

    # 3. PDF 기반 RAG 체인 생성
    rag_chain = chains.create_rag_chain(retriever)
    print("RAG chain created")

    # 4. 분류 체인과 SQL 결과 요약 체인 생성
    classification_chain = create_prompt()
    sql_summary_chain = create_sql_summary_prompt()

    # 5. 가상 DB 로드
    db_data = load_virtual_db()
    print("Virtual DB loaded.")
    
    ############################################################################
    # [질문 1] 예시
    ############################################################################
    question1 = "가장 저렴한 방이 있는지 확인하고 싶어요."
    print(f"\n[User Question 1] {question1}")

    result = classification_chain.invoke({"question": question1})
    classification_key_1 = result.strip()
    print(f"[Classification Key 1] {classification_key_1}")

    final_answer_1 = handle_question(question1, classification_key_1, rag_chain, db_data, sql_summary_chain, retriever)
    print("\n=== Final Answer 1 ===")
    print(final_answer_1)

    ############################################################################
    # [질문 2] 예시
    ############################################################################
    question2 = "호텔 예약 취소 정책은 어떻게 되나요?"
    print(f"\n[User Question 2] {question2}")

    result = classification_chain.invoke({"question": question2})
    classification_key_2 = result.strip()
    print(f"[Classification Key 2] {classification_key_2}")

    final_answer_2 = handle_question(question2, classification_key_2, rag_chain, db_data, sql_summary_chain, retriever)
    print("\n=== Final Answer 2 ===")
    print(final_answer_2)

if __name__ == "__main__":
    main()
