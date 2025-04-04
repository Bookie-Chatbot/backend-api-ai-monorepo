 # PDF 등 문서를 로드하는 함수들
from langchain_community.document_loaders import PyPDFLoader

def load_pdf(file_path: str):
    """
    주어진 파일 경로의 PDF 문서를 로드
    """
    loader = PyPDFLoader(file_path=file_path)
    return loader.load()  # Document 객체 리스트 반환
