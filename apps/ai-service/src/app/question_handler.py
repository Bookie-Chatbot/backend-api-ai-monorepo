from app.sql_executor import pseudo_execute_sql
from app import utils

def handle_question(question, classification_key, rag_chain, db_data, sql_summary_chain, retriever):
    """
    분류 결과에 따라 SQL 조회 후 LLM 후처리하거나, PDF RAG를 사용하여 최종 답변을 생성
    """
    from app.prompts import sql_query_map
    if classification_key in sql_query_map:
        query_key = sql_query_map[classification_key]
        sql_raw_result = pseudo_execute_sql(query_key, db_data)
        final_answer = sql_summary_chain.invoke({"sql_result": str(sql_raw_result)})
        return final_answer
    else:
        context_docs = retriever.invoke(question)
        context = utils.format_docs(context_docs)
        final_answer = rag_chain.invoke(question)
        return final_answer