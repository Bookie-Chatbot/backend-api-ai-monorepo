import os
import sys
import argparse
from app_preprocess import loader, splitter, embedding, vectorstore
# from langchain_chroma import Chroma  # Chroma support commented out
from langchain_community.vectorstores import FAISS


def create_file_vectorstore(file_path):
    print("[INFO] Loading PDF from:", file_path)
    docs = loader.load_pdf_plumber(file_path)
    print(f"[INFO] Loaded {len(docs)} pages from PDF.")

    print("[INFO] Splitting documents into chunks...")
    split_docs = splitter.splitter_recursive(docs)
    print(f"[INFO] Created {len(split_docs)} text chunks.")

    print("[INFO] Embedding and indexing chunks into FAISS vector store...")
    db = vectorstore.create_doc_FAISS(split_doc=split_docs)
    print("[INFO] FAISS vector store created with index size:", getattr(db, 'ntotal', 'Unknown'))
    return db


def add_file_vectorstore(file_path, db):
    print("[INFO] Loading PDF from:", file_path)
    docs = loader.load_pdf_plumber(file_path)
    print(f"[INFO] Loaded {len(docs)} pages from PDF.")

    print("[INFO] Splitting documents into chunks...")
    split_docs = splitter.splitter_recursive(docs)
    print(f"[INFO] Created {len(split_docs)} text chunks.")

    if isinstance(db, FAISS):
        print("[INFO] Adding chunks to existing FAISS index...")
        vectorstore.add_doc_to_FAISS(db, split_doc=split_docs)
        print("[INFO] FAISS index now contains total:", getattr(db, 'ntotal', 'Unknown'))
    # Chroma support is disabled
    # elif isinstance(db, Chroma):
    #     print("[INFO] Adding chunks to existing Chroma collection...")
    #     vectorstore.add_doc_to_Chroma(db, split_doc=split_docs)
    #     print("[INFO] Chroma collection now has count:", db._collection.count())
    else:
        print("[ERROR] Unsupported DB type, only FAISS is supported:", type(db))
        sys.exit(1)
    return db


def main():
    print("[INFO] ==== Vector Store Preprocess Test (FAISS Only) ====")
    parser = argparse.ArgumentParser(
        description='PDF 파일을 FAISS 벡터 스토어에 저장하거나 추가 테스트 (Chroma 지원 제거)')
    parser.add_argument(
        'pdf',
        help='처리할 PDF 파일명 (data/ 폴더 기준 또는 절대경로)'
    )
    parser.add_argument(
        '--mode',
        choices=['create', 'add'],
        default='create',
        help='create: 새 벡터 스토어 생성 (기본), add: 기존 FAISS DB에 추가'
    )
    args = parser.parse_args()

    #project_root = os.path.dirname(os.path.abspath(__file__))
    data_dir = 'root_data'
    runs_dir = os.path.join('runs', 'test')
    os.makedirs(runs_dir, exist_ok=True)
    print(f"[INFO] Data directory: {data_dir}")
    print(f"[INFO] Runs/test directory: {runs_dir}")


    # Resolve PDF path
    if os.path.isabs(args.pdf):
        pdf_path = args.pdf
    else:
        pdf_path = os.path.join(data_dir, args.pdf)

    print(f"[INFO] Resolved PDF path: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF 파일을 찾을 수 없습니다: {pdf_path}")
        sys.exit(1)

    # Execute create or add
    if args.mode == 'create':
        print(f"[ACTION] Mode=create: Generating new FAISS vector store from PDF...")
        db = create_file_vectorstore(pdf_path)
        print(f"[SUCCESS] FAISS vector store creation complete: {type(db)}")
    else:
        print(f"[ACTION] Mode=add: Adding PDF content to existing FAISS vector store...")
        try:
            db
        except NameError:
            print('[ERROR] 기존 FAISS DB 객체가 없습니다. 먼저 create 모드로 실행해주세요.')
            sys.exit(1)
        db = add_file_vectorstore(pdf_path, db)
        print(f"[SUCCESS] Document added to FAISS vector store: {type(db)}")


if __name__ == '__main__':
    # 예시 사용법:
    # python -m runs.test.preprocess.pdf --mode create
    # python -m runs.test.preprocess sample.pdf --mode add
    main()
