from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings

def splitter_recursive(doc):
    # recursive. hyperparam은 여기서 조정 구분자도 조정 가능
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False
        )
    
    return splitter.split_documents(doc)

def splitter_semantic(doc):
    splitter = SemanticChunker(OpenAIEmbeddings())
    # embedding을 huggingface로 바꿔서도

    return splitter.split_documents(doc)

# parameter는 document type으로 그대로.
# return 값이 쪼개진 doc.
# chunks = splitter_(doc) 로
# chunks 에 doc를 분할한 상태로 저장.
