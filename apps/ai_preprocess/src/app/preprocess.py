import loader, splitter, embedding, vectorstore
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import utils

def create_file_vectorstore(file_path):
    docs = loader.load_pdf_plumber(file_path)
    # docs = loader.load_pdf_unstructured(file_path)

    split_doc = splitter.splitter_recursive(docs)
    # split_doc = splitter.splitter_semantic(docs)

    # doc, _ = embedding.embed_document_huggingface(doc=split_doc[3].page_content)

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
    doc=create_file_vectorstore("root_data/koreanair.pdf")
    # print(doc.docstore.__dict__)
    for docs in doc:
        if(docs.metadata['page'] > 16) :
            print(docs.page_content)
            print(docs.metadata)
    
        

    # _, embedder = embedding.embed_document_openai([])
    # db=FAISS.load_local("db_FAISS/", embeddings=embedder,
    #                     allow_dangerous_deserialization=True)
    # print(len(db.index_to_docstore_id))
    
    # add_file_vectorstore("root_data/asiana_air_domestic.pdf", db)

    # print(db.docstore.__dict__)
