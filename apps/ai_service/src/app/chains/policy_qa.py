"""Policy QA chain module

This module builds a LangChain pipeline that answers airline/hotel policy questions
using PDF RAG + reranking. It fixes the classic `INVALID_PROMPT_INPUT` error by
supplying a default empty value for the ``context`` variable via
``PromptTemplate.partial``.
"""

from __future__ import annotations

import argparse
import os
from dotenv import load_dotenv

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableLambda, RunnableMap

from langchain_community.vectorstores import FAISS
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import FlashrankRerank

# project-local imports ---------------------------------------------------------
from apps.ai_preprocess.src.app import config
from packages.chatbot_contents.policy_qa import PolicyQAContent

load_dotenv()

# -----------------------------------------------------------------------------
# 0.  Pydantic parser & safe-guard
# -----------------------------------------------------------------------------

policy_qa_parser = PydanticOutputParser(pydantic_object=PolicyQAContent)


def _parse_or_passthrough(text: str):
    """Try pydantic-parse; on failure return raw string so chain doesn’t crash."""
    try:
        return policy_qa_parser.parse(text)
    except Exception:
        return text

safe_parser = RunnableLambda(_parse_or_passthrough)

# -----------------------------------------------------------------------------
# 1.  PromptTemplate with *partial(context="")*  ⇢  ★ 핵심 FIX ★
# -----------------------------------------------------------------------------

_PROMPT = (
    PromptTemplate.from_template(
        "당신은 ‘부엉이 부키’라는 귀여운 부엉이야. "
        "json의 contents.message 안에 설명을 작성해주고, ‘부엉이 부키’처럼 대답하면서, 모든 답변 끝에 ‘부키!’를 붙여줘."
        "특정 항공사나 호텔 정책은 source가 해당 회사인 저장소에서 찾아줘. "
        "회사를 특정하지 않으면 항공 정책은 flight_policy.pdf, 호텔 정책은 hotel_policy.pdf에서 찾아줘.\n"
        "질문에 대해 아래 JSON Schema에 맞춰서 결과를 반환해줘.\n"
        "{format_instructions}\n"
        "질문: {question}\n"
        "이전 대화 내역:\n{chat_history}\n"
        "Context: {context}\n"
    ).partial(context="")  # <= default ensures context is never missing
)

policy_qa_chain = _PROMPT | ChatOpenAI(model_name="gpt-4o-mini", temperature=0) | safe_parser

# -----------------------------------------------------------------------------
# 2.  Helper to load FAISS vector DB
# -----------------------------------------------------------------------------

def load_vecdb(path: str) -> FAISS:
    """Load a FAISS index from *path* using the project’s embedding model."""
    embedder = config.Embedding_Model
    print(f"[INFO] Loading FAISS vectorstore from: {path}")
    db = FAISS.load_local(path, embeddings=embedder, allow_dangerous_deserialization=True)
    print(f"[INFO] Vectorstore loaded: {type(db)}")
    return db

# -----------------------------------------------------------------------------
# 3.  Public factory: create_policy_chain()
# -----------------------------------------------------------------------------

def create_policy_chain() -> RunnableMap:
    """Return a fully-wired QA chain with retriever + reranker."""

    parser = argparse.ArgumentParser(
        description="Policy QA RAG 테스트 (부엉이 부키 모드)"
    )
    parser.add_argument("--db-path", default="db_FAISS", help="FAISS DB 경로")
    args, _ = parser.parse_known_args()

    # 3-1. Vectorstore & retriever
    vectorstore = load_vecdb(args.db_path)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    print("[INFO] Retriever created.")

    # 3-2. FlashRank reranker / compressor
    compressor = FlashrankRerank(model="ms-marco-MultiBERT-L-12")
    print("[INFO] Compressor created.")

    comp_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=retriever,
    )
    print("[INFO] Compression Retriever initialised.")

    # 3-3. Map inputs → LLM
    mapper = RunnableMap({
        "context": lambda d: comp_retriever.invoke(d["question"]),
        "question": lambda d: d["question"],
        "format_instructions": lambda d: d["format_instructions"],
        "chat_history": lambda d: d.get("chat_history", ""),
    })

    chain = mapper | policy_qa_chain | safe_parser

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
    print(demo_result)
