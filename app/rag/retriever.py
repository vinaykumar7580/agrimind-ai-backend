from app.rag.vector_db import vector_store


def retrieve(query: str, k: int = 3):

    docs = vector_store.similarity_search(
        query,
        k=k
    )

    return docs