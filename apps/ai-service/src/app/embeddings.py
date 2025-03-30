# src/app/embeddings.py
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from app import config

def create_vectorstore(splits):
    """
    splits: List[str] - 청크 분할된 텍스트 리스트
    이 함수를 통해 FAISS 벡터 스토어를 생성
    """

    print("Starting embedding model creation (HuggingFaceBgeEmbeddings)...")

    # 1) splits를 Document 객체 리스트로 변환
    doc_list = [Document(page_content=text) for text in splits]

   
    embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large-instruct",
    encode_kwargs={"normalize_embeddings": True},
    )
    
    print("Embedding model initialized. Creating vectorstore...")

    # 3) from_documents()를 사용해 문서(Document) 리스트를 임베딩 후 FAISS 벡터 스토어 생성
    vectorstore = FAISS.from_documents(documents=doc_list, embedding=embeddings)

    print(f"Vectorstore created with {len(doc_list)} documents")

    return vectorstore
