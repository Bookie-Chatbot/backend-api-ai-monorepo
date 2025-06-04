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
    
    start_page = 4
    end_page = len(doc)

    split_docs = splitter.split_documents(doc[start_page:end_page])

    # split_docs[0].metadata["chapter_info"] = None
    for i, d in enumerate(split_docs):
        # match = re.findall(r"(제\s*\d+\s*조\s+[^\n\d항]+?)\n", d.page_content)
        pattern = r"제\s*\d+\s*조\s*\([^()\n]+\)\n"
        match = re.findall(pattern, d.page_content)
        if match:
            # full_t = match.group()
            title = []
            lines = d.page_content.strip().split('\n')

            # 첫 번째 줄과 두 번째 줄
            line1 = lines[0]+'\n'
            line2 = lines[1]+'\n'

            # 첫 번째 줄과 두 번째 줄에 패턴이 없으면 -> 1, 2번 줄에 '제 %d 조 ( ~~ )' 가 안나오면 이전 chunk의 정책 내용 포함
            # 이전 chunk의 chapter_info의 맨 마지막 원소 추가
            if not(re.search(pattern, line1) or re.search(pattern, line2)) and (split_docs[i-1].metadata["chapter_info"] != None):
                mdata = split_docs[i-1].metadata["chapter_info"]
                title.append(mdata[-1])

            for full_t in match:
                title.append(re.sub(r"^제\s*\d+\s*조\s*\((.*?)\)", r"\1", full_t).strip())
            d.metadata["chapter_info"] = title

        else:
            if i==0:
                d.metadata["chapter_info"] = None
                continue
            title=[]
            title.append(split_docs[i-1].metadata["chapter_info"][-1])
            d.metadata["chapter_info"] = title
        

    return split_docs

def splitter_semantic(doc):
    splitter = SemanticChunker(OpenAIEmbeddings())
    # embedding을 huggingface로 바꿔서도

    return splitter.split_documents(doc)

# parameter는 document type으로 그대로.
# return 값이 쪼개진 doc.
# chunks = splitter_(doc) 로
# chunks 에 doc를 분할한 상태로 저장.
