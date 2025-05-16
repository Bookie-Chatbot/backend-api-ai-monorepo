from langchain_chroma import Chroma
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv
import warnings

'''
    db = Chroma.from_documents(
        documents=doc, <- type(doc)=List[Document]
        embedding=embedder,
        persist_directory="./chroma_db", <- 문서를 disk에 저장할 때. 영구 저장하려면 persist_directory에 저장 경로 지정
        collection_name="my_db", <- 생성할 collection 이름
        ids=List[str], <- id 리스트

    ) <- document로부터 vector db 생성

    persist_db = Chroma(persist_directory=, embedding_function=, collection_name=) <- 디스크에서 문서 로드
    << 이때 collection_name은 똑같이 써야돼

    db.get(where 등 조건 삽입 가능) <- 저장된 데이터 확인

    db.similarity_search(
        "query",
        filter={"source": "찾기 원하는 해당 space"},
        k=4, <- default가 4

    ) <- query와 유사도 계산. k-nearest

    db.add_documents([docs]) <- 생성된 db에 document 추가
    db.delete(ids=["삭제할id들 str list"])

'''
load_dotenv()

def create_doc_Chroma(split_doc, persist_directory="db_Chroma"):
    # split doc들로 Chroma DB를 생성하는 메소드. 해당 데이터는 persist_directory 폴더에 저장
    
    DB_PATH = "./chroma_db"
    # embedder = OpenAIEmbeddings(model = "text-embedding-3-small", )
    embedder = HuggingFaceEmbeddings(
        model_name = "intfloat/multilingual-e5-large-instruct",
        # task= "feature-extraction",
        # huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
        # model_kwargs={"device": "cpu"},
    )
    db = Chroma.from_documents(
        split_doc, embedder,
        persist_directory=persist_directory,
        # collection_name="my_db"
    )

    return db
    
def add_doc_to_Chroma(db: Chroma, new_docs):
    # 만들어져 있는 db에 새 docmunet 추가할 때 사용
    db.add_documents(new_docs)

'''
    warnings.filterwarnings("ignore")

    db = FAISS(
        embedding_function=embedder,
        index=faiss.IndexFlatL2(dim_size), <- embedding의 차원 크기를 미리 계산해 dim_size로 넘겨주기
        docstore=InMemoryDocstore(), <- 사용할 문서 저장소
        index_to_docstore_id={Dict[int, str]}, <- 인덱스에서 문서 저장소 ID로의 매핑

    )

    db = FAISS.from_documents(
        documents=doc,
        embedding=embedder,

    ) <- FAISS 벡터 저장소 생성

    db.add_documents([Document], ids=["new_id"])
    db.delete(ids)

    db.save_local(
        folder_path="저장할 폴더 경로",
        index_name="저장할 인덱스 파일 이름"
    ) <- FAISS 인덱스, store, id mapping을 로컬 disk에 저장
    원래 FAISS가 메모리에만 저장되기 때문에 로켈 disk에 저장하려면 save_local 필수

    loaded_db = FAISS.load_local(
        folder_path="폴더 경로",
        index_name="인덱스 파일 이름",
        embeddings=embedder,
        allow_dangerous_deserialization=False(default)

    ) <- 해당 폴더에 있는 저장된 데이터 로드 가능

    db.merge_from(db2) <- 원래 db 뒤에 db2를 병합. db2에 정보 손실은 없음

'''

warnings.filterwarnings("ignore")
os.environ["HF_HOME"] = "./cache/"
# filterwarnings("module") 실제 운영 환경에서 이게 더 안전

def create_doc_FAISS(split_doc, persist_directory="db_FAISS"):
    # split doc들로 FAISS DB를 생성하는 메소드. persist_directory 폴더에 저장

    # embedder = OpenAIEmbeddings(model = "text-embedding-3-small", )
    embedder = HuggingFaceEmbeddings(
        model_name= "intfloat/multilingual-e5-large-instruct",
    )
    db = FAISS.from_documents(
        split_doc, embedder,
    )
    db.save_local(persist_directory)

    return db
    
def add_doc_to_FAISS(db: FAISS, new_docs, persist_directory="db_FAISS"):
    # 만들어져 있는 db에 새 docmunet 추가할 때 사용
    db.add_documents(new_docs)
    db.save_local(persist_directory)
