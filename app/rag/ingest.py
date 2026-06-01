from app.rag.vector_db import vector_store
from langchain.text_splitter import RecursiveCharacterTextSplitter

def ingest_docs(docs):

    # STEP 1: Chunking
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(docs)

    # STEP 2: Store in vector DB
    vector_store.add_documents(chunks)

    return len(chunks)