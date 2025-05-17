import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

from .prompts import DEFAULT_PROMPT

def create_rag_chain(retriever, prompt=DEFAULT_PROMPT):
    """
    Create a RetrievalQA chain using the provided retriever and prompt.
    Utilizes gpt-3.5-turbo as the LLM and the 'stuff' chain type.
    """
    print("[DEBUG] Entering create_rag_chain (RetrievalQA)")
    load_dotenv()
    print("[DEBUG] Loaded environment variables")
    print(f"[DEBUG] Retriever provided: {retriever!r}")
    print(f"[DEBUG] Prompt template: {prompt!r}")

    print("[DEBUG] Initializing ChatOpenAI LLM")
    try:
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        print(f"[DEBUG] ChatOpenAI LLM initialized: {llm!r}")
    except Exception as e:
        print(f"[ERROR] Failed to initialize ChatOpenAI: {e}", file=sys.stderr)
        raise

    print("[DEBUG] Creating RetrievalQA.from_chain_type")
    try:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False,
            chain_type_kwargs={"prompt": prompt},
        )
        print("[DEBUG] RetrievalQA chain created successfully")
    except Exception as e:
        print(f"[ERROR] Error creating RetrievalQA chain: {e}", file=sys.stderr)
        raise

    print("[DEBUG] Exiting create_rag_chain")
    return qa_chain
