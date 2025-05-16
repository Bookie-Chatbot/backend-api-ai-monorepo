import loader, splitter, embedding, vectorstore
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS

def create_file_vectorstore(file_path):
    docs = loader.load_pdf_plumber(file_path)
    # docs = loader.load_pdf_unstructured(file_path)

    split_doc = splitter.splitter_recursive(docs)
    # split_doc = splitter.splitter_semantic(docs)

    # doc, _ = embedding.embed_document_huggingface(doc=split_doc[3].page_content)

    db=vectorstore.create_doc_FAISS(split_doc=split_doc)
    # db=vectorstore.create_doc_Chroma(split_doc=split_doc)
    
    return db

def add_file_vectorstore(file_path, db):
    docs = loader.load_pdf_plumber(file_path)
    # docs = loader.load_pdf_unstructured(file_path)

    split_doc = splitter.splitter_recursive(docs)
    # split_doc = splitter.splitter_semantic(docs)

    if isinstance(db, FAISS):
        vectorstore.add_doc_to_FAISS(db, split_doc=split_doc)
    elif isinstance(db, Chroma):
        vectorstore.add_doc_Chroma(db, split_doc=split_doc)
    
    return db

