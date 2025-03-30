 # src/app/chains.py
# RAG 체인 등 LangChain 체인 구성 코드
from langchain.chains import RetrievalQA
#from langchain_community.llms import Ollama
#from langchain_ollama import OllamaLLM
from app import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from app .prompts import DEFAULT_PROMPT

def create_rag_chain(retriever,prompt=DEFAULT_PROMPT):
 llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)


# 체인을 생성
 chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
    )
 return chain
