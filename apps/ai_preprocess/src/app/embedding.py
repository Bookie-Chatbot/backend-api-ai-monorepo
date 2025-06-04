from langchain_openai import OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
# from langchain.embeddings import CacheBackedEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import os
from dotenv import load_dotenv
import config

# cacheback은 사용 안했음
'''
    embeddings = OpenAiEmbeddings(model =
    "text-embedding-3-small" or
    "text-embedding-3-large" or
    "text-embedding-ada-002" , dimensions=차원 지정 가능)

    doc_embed = embeddings.embed_documents([docs])
    document embedding하는 방법

'''
def embed_document_openai(doc):
    # List[str] input을 OpneAIEmbedding 사용해서 embed하는 메소드. doc type이어야됨
    load_dotenv()
    embedder = config.Embedding_Model

    doc_embed = embedder.embed_documents(doc)
    return doc_embed, embedder

# def similarity(a, b):
#     return cosine_similarity([a], [b])[0][0]
# cosine similarity로 embedded chunks간의 유사도 측정

'''
    store = LocalFileStore("./cache/")

    cached_embedder = CacheBackedEmbeddings.from_bytes_store(   <- from_bytes_store = cache embedder 초기화 메소드
        underlying_embeddings = embedding,
        document_embedding_cache = store,
        namespace=embedding.model,    <- 같은 텍스트를 다른 임베딩 모델로 임베딩할 때 충돌 피하기 위해 namespace 설정 필수
    )

'''

'''
    hf_embedder = HuggingFaceEndpointEmbeddings(
        model = "intfloat/multilingual-e5-large-instruct" 외에도 많음. "BAAI/bge-m3", "MTEB" 등,
        task = "feature-extraction",
        huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
        model_kwargs={"device": "cuda"} <- device 교체로 gpu, mps, cpu 사용해 성능 높일 수 있음
    )

'''

def embed_document_huggingface(doc):
    # List[str] input을 HuggingFaceEmbedding 사용해서 embed하는 메소드. List[str] type이어야됨
    load_dotenv()
    # os.environ["HF_HOME"]="./cache"
    embedder = HuggingFaceEmbeddings(
        model_name = "intfloat/multilingual-e5-large-instruct",
    )

    doc_embed=embedder.embed_documents(doc)
    return doc_embed, embedder



if __name__ == "__main__" :
    import json
    import requests
    
    kcreds = {"access_token" :"Lq4X_z2QHvANAdxulavvaBFikDOomWo9AAAAAQoNGZAAAAGXLyNIE9EMsmlHt4Ko"}
    kheaders = {"Authorization": "Bearer " + kcreds.get('access_token')} # 이건 바꾸는거 아님.

    url_mine = "https://kapi.kakao.com/v2/api/talk/memo/default/send" # 나에게 보내기
    url = "https://changsroad.tistory.com/366"

    # 메세지 템플릿(자신이 원하는 형식으로 보낼 수 있음)
    content  = f"""\
    Hello From Bookie!!
    """
    template = {"object_type": "text","text": content ,
                "link": {"web_url": url_mine,"mobile_web_url": url_mine},
                "button_title": "확인 클릭"}
                
    data = {"template_object" : json.dumps(template)}
    
    res = requests.post(url_mine, data=data, headers=kheaders)
    print(res)
    # if res.json().get('result_code') == 0: print('나에게 전송 성공.')
    # else: print('나에게 전송 실패. Error : ' + str(res.json()))