 # 텍스트 청크 분할 관련 함수 및 클래스
from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 50):
    """
    텍스트를 지정한 크기와 중복(오버랩)으로 청크로 분할
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)  # 문자열 리스트 반환
