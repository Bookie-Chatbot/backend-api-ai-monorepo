from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document
import re

def splitter_recursive(doc):
    # recursive. hyperparam은 여기서 조정 구분자도 조정 가능
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        separators=[r"(?:제\s*\d+\s*조\s+[^\n\d항]+?)\n", "\n\n", "\n", ".", " ", ""],        
        is_separator_regex=True
        )
    
    start_page = 1
    end_page = len(doc)

    split_docs = splitter.split_documents(doc[start_page:end_page])

    # split_docs[0].metadata["chapter_info"] = None
    for i, d in enumerate(split_docs):
        if i==0:
            d.metadata["chapter_info"] = None
            continue
        match = re.search(r"(제\s*\d+\s*조\s+[^\n\d항]+?)\n", d.page_content)
        if match:
            full_t = match.group()
            title = re.sub(r"^제\s*\d+\s*조", "", full_t).strip()
            d.metadata["chapter_info"] = title
        else:
            d.metadata["chapter_info"] = split_docs[i-1].metadata["chapter_info"]
        

    return split_docs

def splitter_semantic(doc):
    splitter = SemanticChunker(OpenAIEmbeddings())
    # embedding을 huggingface로 바꿔서도

    return splitter.split_documents(doc)

# parameter는 document type으로 그대로.
# return 값이 쪼개진 doc.
# chunks = splitter_(doc) 로
# chunks 에 doc를 분할한 상태로 저장.
