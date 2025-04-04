  # 기타 유틸리티 함수들 (예: 문서 포매팅)
def format_docs(documents):
    """
    Document 객체 리스트의 page_content를 하나의 문자열로 결합
    """
    return "\n\n".join([doc.page_content for doc in documents])
