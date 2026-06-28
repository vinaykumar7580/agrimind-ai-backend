import chromadb
from chromadb.config import Settings as ChromaSettings
from config import settings
from rag.knowledge_base import ALL_DOCS

_client = None
_collection = None

def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _client

def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name="agrimind_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
    return _collection

def init_vector_store():
    """Load knowledge base into ChromaDB if empty."""
    collection = get_collection()
    if collection.count() > 0:
        print(f"✅ ChromaDB already has {collection.count()} documents")
        return

    print("📚 Loading knowledge base into ChromaDB...")
    ids = [doc["id"] for doc in ALL_DOCS]
    texts = [doc["text"] for doc in ALL_DOCS]
    metadatas = [doc["metadata"] for doc in ALL_DOCS]

    collection.add(documents=texts, ids=ids, metadatas=metadatas)
    print(f"✅ Loaded {len(ALL_DOCS)} documents into ChromaDB")

def similarity_search(query: str, n_results: int = 4, where: dict = None) -> list[dict]:
    """Search for relevant documents."""
    collection = get_collection()
    kwargs = {"query_texts": [query], "n_results": min(n_results, collection.count())}
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)
    docs = []
    for i, doc in enumerate(results["documents"][0]):
        docs.append({
            "text": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })
    return docs