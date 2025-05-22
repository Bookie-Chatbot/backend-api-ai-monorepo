import os
import sys
import argparse
from datetime import date
from dotenv import load_dotenv

from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS

# from app_service.service.retrievers import create_retriever
# from app_service.service.chains import create_rag_chain
# from app_preprocess.embedding import embed_document_openai
# for window
from apps.ai_service.src.app.service.retrievers import create_retriever
from apps.ai_service.src.app.service.chains import create_rag_chain
from apps.ai_preprocess.src.app.embedding import embed_document_openai


import faiss, os
from langchain_openai import OpenAIEmbeddings

# 환경 변수 로드 (OpenAI API 키 등)
load_dotenv()

# =====================================================
# Test Policy RAG Script (Interactive Questions)
# 귀여운 부엉이 정책 도우미 역할 프롬프트 적용
# =====================================================
TODAY = date.today().isoformat()
ROLE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     f"🦉 안녕! 나는 지혜로운 부엉이 정책 도우미야! 오늘 날짜는 {TODAY}이고, 언제나 친절하고 귀여운 말투로 정책 관련 질문에 답할게."
     "\n정확한 정보만 알려주고, 만약 확실치 않거나 문서에 없으면 '죄송하지만 제 지식 범위 내에는 해당 정보가 없어요'라고 솔직하게 말할 거야.")
])

DEFAULT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "🦉 나는 지혜로운 부엉이 정책 도우미야! 언제나 친절하고 귀여운 말투로 정책 관련 질문에 답할게."
     "\n정확한 정보만 제공하고, 모르는 내용은 '죄송하지만 제 지식 범위 내에는 해당 정보가 없어요'라고 알려줘."),
    ("user", "질문: {question}\n\n문서에서 찾은 정보: ```{context}```\n\n답변:")
])


def load_faiss_store(path: str) -> FAISS:
    """
    Load a persisted FAISS vectorstore from disk,
    wiring in the embedder defined in embedding.py.
    """
    # embedder만 필요하므로 빈 리스트로 호출
    _, embedder = embed_document_openai([])
    abs_path = os.path.abspath(path)
    store_dir = abs_path if os.path.isdir(abs_path) else os.path.dirname(abs_path)

    print(f"[INFO] Loading FAISS vectorstore from: {store_dir}")
    vectorstore = FAISS.load_local(
        store_dir,
        embedder,
        allow_dangerous_deserialization=True
    )
    print(f"[INFO] Vectorstore loaded: {type(vectorstore)}")
    return vectorstore


def main():
    parser = argparse.ArgumentParser(
        description='Policy-related 질문에 대해 PDF RAG를 테스트합니다. (귀여운 부엉이 모드)'
    )
    parser.add_argument(
        '--db-path', default='db_FAISS',
        help='FAISS DB 경로 (디렉터리 또는 index 파일의 경로)'
    )
    args = parser.parse_args()

    # 1. 벡터 스토어 로드
    vectorstore = load_faiss_store(args.db_path)

    # 2. Retriever 생성
    retriever = create_retriever(vectorstore, k=3)
    print("[INFO] Retriever created.")

    # 2.1. FAISS 인덱스와 임베더 차원 확인
    print("[INFO] FAISS 인덱스와 임베더 차원 확인")
    idx = faiss.read_index(os.path.join("db_FAISS", "index.faiss"))
    print("Index dim →", idx.d)   # 예: 3072
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")
    print("Embedder dim →", len(embedder.embed_query("ping")))  # 예: 1536

    # 3. RAG 체인 생성
    rag_chain = create_rag_chain(retriever, prompt=DEFAULT_PROMPT)
    print("[INFO] RAG chain initialized with owl prompt.")
    print("[INFO] 질문을 입력하세요. 종료하려면 'exit' 또는 'quit'를 입력하세요.")



    # 4. 인터랙티브 루프
    while True:
        try:
            question = input("\n[INPUT] 질문: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] 입력 종료. 프로그램을 종료합니다.")
            break

        if not question:
            print("[WARN] 질문이 입력되지 않았어요.")
            continue
        if question.lower() in ('exit', 'quit'):
            print("[INFO] 'exit' 명령어 감지. 프로그램을 종료합니다.")
            break

        print(f"\n=== 질문 ===\n{question}")
        print("[ACTION] 귀여운 부엉이가 답변 준비 중...")
        try:
            # LCEL 체인에 dict 형태로 질문 전달
            result = rag_chain.invoke({"query": question})

            # 반환 dict에서 'answer' 또는 'output' 키를 사용
            if isinstance(result, dict):
                answer = result.get("answer") or result.get("output") or str(result)
            else:
                answer = str(result)
            print("\n--- 답변 ---")
            print(answer)
        except Exception as e:
            print(f"[ERROR] 질문 처리 중 오류 발생: {e!r}")

    print("[INFO] 프로그램 종료.")


if __name__ == '__main__':
    main()
