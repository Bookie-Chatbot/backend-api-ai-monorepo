# src/app/splitters.py
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text(text: str, chunk_size: int = 250, chunk_overlap: int = 50):
    """
    텍스트를 지정한 크기와 중복(오버랩)으로 청크로 분할
    기본 값: chunk_size=250, chunk_overlap=50
    분할 순서는 단락 -> 문장 -> 단어 순으로 재귀적으로 진행
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(text)
