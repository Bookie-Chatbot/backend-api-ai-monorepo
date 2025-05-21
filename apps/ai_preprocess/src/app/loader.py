from langchain_community.document_loaders import UnstructuredPDFLoader, PDFPlumberLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document
import warnings
import os

def load_pdf_unstructured(file_path: str):
    # 비정형 데이터를 다루기 위한 공동 인터페이스 지원. metadata 많음
    loader = UnstructuredPDFLoader(file_path=file_path, 
                                   mode="elements"
    )
    
    return loader.load()

def load_pdf_plumber(file_path: str):
    # 한글 인코딩 처리 좋음. metadata 많음
    loader = PDFPlumberLoader(file_path=file_path)

    doc = loader.load()

    base_name = os.path.splitext(os.path.basename(file_path))[0]

    for d in doc:
        d.metadata["source"] = base_name
        # d.metadata["test"] = "test_metadata"

    return doc

warnings.filterwarnings("ignore", message=".*Advanced encoding*")

def load_pdf_from_dir(dir_path: str):
    # directory에서 한 번에 load 해오기
    # 폰트 인코딩을 완전 해석하지 못할 수도 있음.
    # 사용하는데 위험. pdf 제대로 해석 못할 수 있음
    loader = PyPDFDirectoryLoader(path=dir_path)

    return loader.load()

# return 값이 전부 document type.
# docs = load_pdf_(file_path) 로
# docs 에 document type으로 pdf 내용 load 가능.


if __name__ == "__main__" :
    plumber_doc = load_pdf_plumber("./root_data/koreanair.pdf")
    print(len(plumber_doc))
    # unst_doc = load_pdf_unstructured("../data/un_db/dom_trans_kr.pdf")
    # print(len(unst_doc))

    # docs=load_pdf_from_dir("../data/un_db/")

    print(plumber_doc[0].metadata)
    print(plumber_doc[0].page_content)