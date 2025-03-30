# 문서 검색(Retriever) 생성 함수
def create_retriever(vectorstore, k: int = 3):
    """
    주어진 벡터 스토어에서 상위 k개의 문서를 검색하는 retriever를 생성
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    return retriever
