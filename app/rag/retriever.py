from app.rag.vector_db import vector_store

def retrieve_context(query: str, k: int = 4):

    docs = vector_store.similarity_search(
        query,
        k=k
    )

    return docs