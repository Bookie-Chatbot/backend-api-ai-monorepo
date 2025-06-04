from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
# from chatbot_contents.policy_qa import PolicyQAContent
# for window
from packages.chatbot_contents.policy_qa import PolicyQAContent
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableMap

from langchain_community.vectorstores import FAISS
from apps.ai_preprocess.src.app import config
import os
import argparse
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import FlashrankRerank

load_dotenv()

policy_qa_parser = PydanticOutputParser(pydantic_object=PolicyQAContent)

def parse_or_passthrough(text: str):
    try:
        return policy_qa_parser.parse(text)
    except Exception:
        return text

safe_parser = RunnableLambda(parse_or_passthrough)

policy_qa_chain = (
    PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에 설명을 작성해주고, ‘부엉이 부키’라는 귀여운 부엉이처럼 대답하면서, 모든 답변 끝에 ‘부키!’를 붙여줘."
        "특정 항공사나 호텔에 관한 정책은 source가 해당 회사 이름인 저장소에서 찾아줘."
        "회사를 특정하지 않으면 항공 관련 정책 질의는 flight_policy.pdf에서, 호텔 관련 정책 질의는 hotel_policy.pdf에서 찾아줘."
        "질문에 대해 아래 JSON Schema에 맞춰서 결과 반환해줘.\n"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
        "Context: {context}\n"
    )
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | safe_parser
)

def load_vecDB(path: str) -> FAISS:
    embedder = config.Embedding_Model

    # 상대경로로 vectorDB load. 
    # 절대경로로 바꾸는 코드
    # abs_path = os.path.abspath(path)
    # store_dir = abs_path if os.path.isdir(abs_path) else os.path.dirname(abs_path)
    # store_dir를 path대신 사용
    print(f"[INFO] Loading FAISS vectorstore from: {path}")
    db = FAISS.load_local(path, embeddings=embedder,
                          allow_dangerous_deserialization=True)
    print(f"[INFO] Vectorstore loaded: {type(db)}")
    
    return db

def create_policy_chain():
    parser = argparse.ArgumentParser(
        description='Policy-related 질문에 대해 PDF RAG를 테스트합니다. (귀여운 부엉이 모드)'
    )
    parser.add_argument(
        '--db-path', default='db_FAISS',
        help='FAISS DB 경로 (디렉터리 또는 index 파일의 경로)'
    )
    args = parser.parse_args()

    # 1. vectorstore load
    vectorstore = load_vecDB(args.db_path)

    # 2. Retriever 및 Reranker 생성
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    print("[INFO] Retriever created.")
    
    # 2.1. 문서 압축기 초기화
    compressor = FlashrankRerank(model="ms-marco-MultiBERT-L-12")
    print("[INFO] Comperssor Created")

    # 2.2. 문맥 압축 검색기 초기화
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=retriever
    )
    print("[INFO] Compression Retriever Initialize")

    input_mapper = RunnableMap({
        "context": lambda x: compression_retriever.invoke(x["question"]),
        "question": lambda x: x["question"],
        "format_instructions": lambda x: x["format_instructions"],
        "chat_history": lambda x: x.get("chat_history", None),
    })

    new_chain = input_mapper | policy_qa_chain
    print("[INFO] New Chain Production")

    return new_chain


if __name__ == "__main__" :
<<<<<<< Updated upstream
=======
<<<<<<< HEAD

=======
>>>>>>> shin_
>>>>>>> Stashed changes
    # vecstore = load_vecDB("db_FAISS/")
    chain = create_policy_chain()
    print(chain.invoke({
        "question": "화물 수행인에 대해 설명해줘",
        "format_instructions": policy_qa_parser.get_format_instructions(),
        "chat_history": None
    }))
    
<<<<<<< Updated upstream
=======
<<<<<<< HEAD


    



=======
>>>>>>> shin_
>>>>>>> Stashed changes
