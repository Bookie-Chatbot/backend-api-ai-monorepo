import loader, splitter, embedding, vectorstore
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import utils
import config

def create_file_vectorstore(file_path):
    docs = loader.load_pdf_plumber(file_path)
    # docs = loader.load_pdf_unstructured(file_path)

    split_doc = splitter.splitter_recursive(docs)
    # split_doc = splitter.splitter_semantic(docs)

    # doc, _ = embedding.embed_document_huggingface(doc=split_doc[3].page_content)
    print(len(split_doc))

    # db=vectorstore.create_doc_FAISS(split_doc=split_doc)
    # db=vectorstore.create_doc_Chroma(split_doc=split_doc)
    
    return split_doc

def add_file_vectorstore(file_path, db):
    docs = loader.load_pdf_plumber(file_path)
    # docs = loader.load_pdf_unstructured(file_path)

    split_doc = splitter.splitter_recursive(docs)
    # split_doc = splitter.splitter_semantic(docs)

    if isinstance(db, FAISS):
        vectorstore.add_doc_to_FAISS(db, new_docs=split_doc)
    elif isinstance(db, Chroma):
        vectorstore.add_doc_to_Chroma(db, new_docs=split_doc)
    
    return db


if __name__ == "__main__":
    ###### load, split 확인용 코드 ######
    # doc=create_file_vectorstore("root_data/asiana_domestic.pdf")
    # print(len(doc.docstore.__dict__))
    # print(len(doc))
    # for docs in doc:
    #     if(docs.metadata['page'] == 13 or docs.metadata['page'] == 17) :
    #         print(docs.page_content)
    #         print(docs.metadata)
        #     print(docs.metadata['chapter_info'][-1])

        # elif(docs.metadata['page'] > 16) :
        #     print(docs.page_content)
        #     print(docs.metadata)


    ###### FAISS DB load start ######
    embedder = config.Embedding_Model
    db=FAISS.load_local("db_FAISS/", embeddings=embedder,
                        allow_dangerous_deserialization=True)
    print('load한 vectorspace의 총 chunk 수 : ', len(db.index_to_docstore_id))        # 총 FAISS chunk수

    ###### FAISS DB load fin ######
    '''
    현재 들어가있는 총 chunk 개수
    koreanair=69
    asiana_domestic=58
    '''

    ###### db에서 해당 source를 가진 chunk들 삭제 start ######
    # ids = []
    # for key in db.docstore.__dict__['_dict']:
    #     msource = db.docstore.__dict__['_dict'][key].metadata['source']
    #     if msource == 'asiana':                                     # 삭제할 소스 입력
    #         ids.append(key)

    # print('현재 총 chunk 수 : ', len(db.index_to_docstore_id))        # 총 FAISS chunk수
    # print('삭제 할 chunk 수 : ', len(ids))                           # 삭제할 chunk 개수

    # vectorstore.delete_ids_FAISS(db, ids=ids)

    # print('삭제 후 chunk 수 : ', len(db.index_to_docstore_id))      # 삭제 후 FAISS chunk수
    ###### db에서 해당 source를 가진 chunk들 삭제 fin ######


    ###### db에 해당 path에 있는 파일 추가 임베딩 start ######
    # add_file_vectorstore("root_data/asiana_domestic.pdf", db)
    
    # print(db.docstore.__dict__) 이건 다 출력하는 거니까 최대한 자제
    # print('추가 후 chunk 개수 : ', len(db.index_to_docstore_id))
    ###### db에 해당 path에 있는 파일 추가 임베딩 fin ######

