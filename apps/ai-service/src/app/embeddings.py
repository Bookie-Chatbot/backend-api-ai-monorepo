# src/app/embeddings.py
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from app import config

PERSIST_DIRECTORY = "data/db/faiss_index"

def create_vectorstore(splits):
    """
    splits: List[str] - 분할된 텍스트 청크 리스트
    문서 리스트를 임베딩하고, FAISS 벡터스토어를 생성 후 디스크에 저장
    """
    print("Starting embedding model creation (HuggingFaceEmbeddings)...")
    
    # splits를 Document 객체 리스트로 변환
    doc_list = [Document(page_content=text) for text in splits]

    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-large-instruct",
        encode_kwargs={"normalize_embeddings": True},
    )
    
    print("Embedding model initialized. Creating vectorstore...")
    
    # FAISS 벡터스토어 생성 
    vectorstore = FAISS.from_documents(
        documents=doc_list,
        embedding=embeddings
    )
    
    # FAISS 인덱스 저장
    vectorstore.save_local(PERSIST_DIRECTORY)
    print(f"Vectorstore created with {len(doc_list)} documents and saved to '{PERSIST_DIRECTORY}'")
    return vectorstore

def load_vectorstore():
    """
    저장된 벡터스토어를 디스크에서 로드
    """
    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-large-instruct",
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = FAISS.load_local(PERSIST_DIRECTORY, embeddings, allow_dangerous_deserialization=True)
    return vectorstore
