# preprocess.py
from app import loaders, splitters, embeddings

def main():
    # 1. PDF 파일 로드 (호텔 예약 정보)
    pdf_path = "data/raw/HotelReservations.pdf"
    docs = loaders.load_pdf(pdf_path)
    print(f"Loaded {len(docs)} pages from {pdf_path}")
    
    # 2. 문서 분할: 각 PDF 페이지의 텍스트를 청크로 분할
    split_docs = []
    for doc in docs:
        chunks = splitters.split_text(doc.page_content)
        split_docs.extend(chunks)
    print(f"Split into {len(split_docs)} chunks")
    
    # 3. FAISS 벡터스토어 생성 및 저장
    vectorstore = embeddings.create_vectorstore(split_docs)
    print("Vectorstore created and persisted.")

if __name__ == "__main__":
    main()
