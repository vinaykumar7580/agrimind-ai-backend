from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.rag.vector_db import vector_store

def ingest_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    vector_store.add_documents(chunks)

    return len(chunks)