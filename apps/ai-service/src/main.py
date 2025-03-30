# 애플리케이션 실행 진입점 (챗봇 실행)
from app import config, loaders, splitters, embeddings, retrievers, chains, utils, virtual_db
from langchain.prompts import PromptTemplate
#from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

def main():
    # 1. PDF 파일 로드 (호텔 예약 정보)
    pdf_path = "data/raw/HotelReservations.pdf"
    docs = loaders.load_pdf(pdf_path)
    print(f"Loaded {len(docs)} pages from {pdf_path}")
    # 2. 문서 분할: 각 PDF 문서의 텍스트를 청크로 나눔 
    split_docs = []
    for doc in docs:
        chunks = splitters.split_text(doc.page_content)
        split_docs.extend(chunks)
    print(f"Split into {len(split_docs)} chunks")
    # 3. 벡터 스토어 생성: 텍스트 청크를 임베딩하여 벡터화
    vectorstore = embeddings.create_vectorstore(split_docs)
    print("Vectorstore created")
    
    # 4. Retriever 생성: 상위 k개의 문서를 검색할 수 있도록 retriever 생성
    retriever = retrievers.create_retriever(vectorstore, k=3)
    print("Retriever created")
    
    # 5. RAG 체인 생성: 질문-답변 체인을 구성
    rag_chain = chains.create_rag_chain(retriever)
    print("RAG chain created")
    # 6. 예시 질문 실행 (RAG 기반)
    question = "호텔 예약 가능한 객실은 어떤 것들이 있나요?"
    #context_docs = retriever.get_relevant_documents(question)
    context_docs = retriever.invoke(question)
    context = utils.format_docs(context_docs)
    answer = rag_chain.invoke(question)
    
    print("=== PDF 기반 RAG 체인 ===")
    print("Question:", question)
    print("Context:", context)
    print("Answer:", answer)
    
    # 7. 가상 DB 로드: 여러 JSON 파일을 병합하여 가상 DB 데이터 획득
    db_data = virtual_db.load_virtual_db()
    
    # 예시: 가상 DB에서 호텔 정보 가져오기
    hotels = db_data.get("Hotel", [])
    hotel_context = "\n".join(
        [
            f"호텔명: {hotel['name']}, 위치: {hotel['location']}, 기본가격: {hotel['price']}, 사용가능 객실: {hotel['available_rooms']}"
            for hotel in hotels
        ]
    )
    
    # 간단한 프롬프트를 통해 가상 DB의 호텔 정보를 활용해 답변 생성
    question2 = "현재 예약 가능한 호텔은 어디인가요?"
    prompt_template = PromptTemplate(
        template="호텔 정보:\n{context}\n\n질문: {question}\n\n답변:",
        input_variables=["context", "question"]
    )
   # llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    llm = ChatOllama(model="ollama3")

    prompt_text = prompt_template.format(context=hotel_context, question=question2)
    answer2 = llm.invoke(prompt_text)
    
    print("\n=== 가상 DB (JSON) 활용 예시 ===")
    print("Question:", question2)
    print("Context:", hotel_context)
    print("Answer:", answer2)

if __name__ == "__main__":
    main()
