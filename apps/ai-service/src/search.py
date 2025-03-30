# search.py
from app import config, retrievers, prompts, chains, utils, virtual_db, embeddings
from langchain_openai import ChatOpenAI
import os
#from langchain_community.chat_models import ChatOllama

def main():
    # 1. 저장된 FAISS 벡터스토어 로드
    vectorstore = embeddings.load_vectorstore()
    print("Loaded persisted vectorstore.")
    
    # 2. Retriever 생성: 상위 k개의 문서를 검색
    retriever = retrievers.create_retriever(vectorstore, k=3)
    print("Retriever created")

    prompt = prompts.create_prompt()
    # 3. RAG 체인 생성: 질문-답변 체인 구성
    rag_chain = chains.create_rag_chain(retriever, prompt)
    print("RAG chain created")
    
    # 4. 예시 질문 실행 (PDF 기반)
    question = "호텔 예약 취소 정책은 어떻게 되나요?"
    # LangChain 1.0 이후 권장: invoke() 사용
    context_docs = retriever.invoke(question)
    context = utils.format_docs(context_docs)
    answer = rag_chain.invoke(question)
    
    print("=== PDF 기반 RAG 체인 ===")
    print("Question:", question)
    print("Context:", context)
    print("Answer:", answer)
    
    # 5. 가상 DB 활용 예시
    db_data = virtual_db.load_virtual_db()
    hotels = db_data.get("Hotel", [])
    hotel_context = "\n".join(
        [
            f"호텔명: {hotel['name']}, 위치: {hotel['location']}, 기본가격: {hotel['price']}, 사용가능 객실: {hotel['available_rooms']}"
            for hotel in hotels
        ]
    )
    question2 = "현재 예약 가능한 호텔은 어디인가요?"
    prompt_template = prompts.create_prompt(
        template="호텔 정보:\n{context}\n\n질문: {question}\n\n답변:",
        input_variables=["context", "question"]
    )
    # llm = ChatOllama(model="ollama3")
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    print(f"[API KEY]\n{os.environ['OPENAI_API_KEY']}")

    prompt_text = prompt_template.format(context=hotel_context, question=question2)
    answer2 = llm.invoke(prompt_text)
    
    print("\n=== 가상 DB (JSON) 활용 예시 ===")
    print("Question:", question2)
    print("Context:", hotel_context)
    print("Answer:", answer2)

if __name__ == "__main__":
    main()
