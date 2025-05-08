#!/usr/bin/env python
# apps/ai-service/src/main_service.py

import os
from dotenv import load_dotenv
from app import config
from app.service.prompts import create_prompt, create_sql_summary_prompt
from app.virtual_db import load_virtual_db
from app.sql_queries import sql_query_map
from app.sql_executor import pseudo_execute_sql

def main():
    # 1) 환경변수 로드
    load_dotenv()  
    print("⚙️  환경변수 로드 완료")

    # 2) 분류 체인과 SQL 요약 체인 준비
    classification_chain = create_prompt()
    sql_summary_chain   = create_sql_summary_prompt()
    print("🔗 체인 초기화 완료 (분류 + SQL 요약)")

    # 3) 가상 DB 로드
    db_data = load_virtual_db()
    print("📂 가상 DB 로드 완료")

    # 4) 사용자 입력 루프
    print("\n💬 질문을 입력하세요. (종료하려면 빈 줄 Enter)\n")
    while True:
        question = input("▶ ")
        if not question.strip():
            print("👋 종료합니다.")
            break

        # 5) 분류(chain.invoke) → SQL 키 결정
        classification = classification_chain.invoke({"question": question}).strip()
        print(f"[분류 결과] {classification}")

        # 6) SQL 조회 & 요약
        if classification in sql_query_map:
            query_key = sql_query_map[classification]
            raw_rows  = pseudo_execute_sql(query_key, db_data)
            print(f"[SQL 조회] {query_key} → {raw_rows}")

            summary = sql_summary_chain.invoke({
                "sql_result":    str(raw_rows),
                "user_question": question
            })
            print(f"\n📝 최종 답변:\n{summary}\n")
        else:
            print("⚠️ 해당 분류는 SQL 처리 대상이 아닙니다. 다른 로직을 구현하세요.\n")

if __name__ == "__main__":
    main()
