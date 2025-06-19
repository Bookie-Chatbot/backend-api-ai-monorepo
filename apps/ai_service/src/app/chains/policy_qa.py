from __future__ import annotations
import argparse, os, re
from dotenv import load_dotenv
from typing import Any
from pprint import pprint         # ← 추가

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableLambda, RunnableMap

from langchain_community.vectorstores import FAISS
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import FlashrankRerank

# project-local imports ---------------------------------------------------------
from apps.ai_preprocess.src.app import config
from packages.chatbot_contents.policy_qa import PolicyQAContent, ContentsList

load_dotenv()

# -----------------------------------------------------------------------------
# 0.  Pydantic parser & safe-guard
# -----------------------------------------------------------------------------
policy_qa_parser = PydanticOutputParser(pydantic_object=PolicyQAContent)

# -------------------------------------
# utils/parsing.py  ―  개선 버전
# -------------------------------------
import re
from langchain_core.messages import AIMessage
from packages.chatbot_contents.policy_qa import PolicyQAContent, ContentsList
from langchain.output_parsers.pydantic import PydanticOutputParser

_FENCE_RE = re.compile(r"```(?:json)?\\s*(.*?)\\s*```", re.S | re.I)
parser = PydanticOutputParser(pydantic_object=PolicyQAContent)

def _parse_or_passthrough(output) -> PolicyQAContent:
    # 1) AIMessage → text
    if isinstance(output, AIMessage):
        text = output.content
    elif isinstance(output, dict):
        return PolicyQAContent(**output)
    else:
        text = str(output)

    # 2) 코드펜스 제거
    m = _FENCE_RE.search(text)
    json_str = m.group(1) if m else text

    # 3) 파싱 시도
    try:
        return parser.parse(json_str)
    except Exception as e:
        # 4) 실패하면 원본 포장
        return PolicyQAContent(
            contents=ContentsList(message=text, references=[])
        )


safe_parser = RunnableLambda(_parse_or_passthrough)

# -----------------------------------------------------------------------------
# 1.  PromptTemplate with context default
# -----------------------------------------------------------------------------
_PROMPT = PromptTemplate.from_template(
     "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에 설명을 작성해주고, ‘부엉이 부키’라는 귀여운 부엉이처럼 대답하면서, 모든 답변 끝에 ‘부키!’를 붙여줘."
        "질문은 db_FAISS에 저장된 문서들만을 사용해서 찾아줘."
        "특정 항공사 관한 정책 물어보면 metadata의 source 키값이 해당 회사 이름인 저장소에서 찾아줘."
        "특정 항공사를 사용자가 언급하지 않으면, 가장 평균적인 정책에 대해서 응답해줘."
        "질문에 대해 아래 JSON Schema에 맞춰서 결과 반환해줘.\n"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
        "Context: {context}\n"
).partial(context="")

policy_qa_chain = (
    _PROMPT
    | ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    | safe_parser
)

# -----------------------------------------------------------------------------
# 2.  Helper to load FAISS vector DB
# -----------------------------------------------------------------------------
def load_vecdb(path: str) -> FAISS:
    embedder = config.Embedding_Model
    print(f"[INFO] Loading FAISS vectorstore from: {path}")
    db = FAISS.load_local(path, embeddings=embedder, allow_dangerous_deserialization=True)
    print(f"[INFO] Vectorstore loaded: {type(db)}")
    return db

# -----------------------------------------------------------------------------
# 3.  Public factory: create_policy_chain()
# -----------------------------------------------------------------------------
def create_policy_chain() -> RunnableMap:
    parser = argparse.ArgumentParser(description="Policy QA RAG 테스트 (부엉이 부키 모드)")
    parser.add_argument("--db-path", default="db_FAISS", help="FAISS DB 경로")
    args, _ = parser.parse_known_args()

    vectorstore = load_vecdb(args.db_path)
    retriever = vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 5, "score_threshold": 0.8},
        )
    print("[INFO] Retriever created.")

    compressor = FlashrankRerank(model="ms-marco-MultiBERT-L-12")
    print("[INFO] Compressor created.")

    comp_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=retriever,
    )
    print("[INFO] Compression Retriever initialised.")

    mapper = RunnableMap({
        "context": lambda d: comp_retriever.invoke(d["question"]),
        "question": lambda d: d["question"],
        "format_instructions": lambda d: d["format_instructions"],
        "chat_history": lambda d: d.get("chat_history", ""),
    })

    chain = mapper | policy_qa_chain  # Note: no second safe_parser here
    print("[INFO] Policy QA chain ready.")
    return chain

# -----------------------------------------------------------------------------
# 4.  CLI demo
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    qa_chain = create_policy_chain()
    demo_result = qa_chain.invoke({
        "question": "화물 수행인에 대해 설명해줘",
        "format_instructions": policy_qa_parser.get_format_instructions(),
        "chat_history": None,
    })
    print("\n=== DEMO OUTPUT ===")
    # ← 결과도 pprint!
    pprint(demo_result)