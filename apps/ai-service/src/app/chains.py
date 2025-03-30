 # RAG 체인 등 LangChain 체인 구성 코드
from langchain.chains import RetrievalQA
from langchain_community.llms import HuggingFaceHub
from app import config

def create_rag_chain(retriever):
    """
    HuggingFaceHub LLM과 retriever를 이용해 RetrievalQA 체인을 생성
    """
    llm = HuggingFaceHub(
        repo_id=config.HUGGINGFACE_REPO_ID,
        model_kwargs={"temperature": 0.2, "max_length": 256},
        huggingfacehub_api_token=config.HUGGINGFACEHUB_API_TOKEN
    )
    chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
    return chain
