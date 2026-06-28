import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rag.knowledge_base import ALL_DOCS

STORE_PATH = Path("./faiss_store")
_model: SentenceTransformer = None
_index: faiss.Index = None
_docs: list = []

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("📦 Loading embedding model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Embedding model loaded")
    return _model

def init_vector_store():
    global _index, _docs

    STORE_PATH.mkdir(exist_ok=True)
    index_file = STORE_PATH / "index.faiss"
    docs_file  = STORE_PATH / "docs.json"

    # Load existing index if available
    if index_file.exists() and docs_file.exists():
        _index = faiss.read_index(str(index_file))
        _docs  = json.loads(docs_file.read_text(encoding="utf-8"))
        print(f"✅ FAISS index loaded — {len(_docs)} documents")
        return

    # Build index from scratch
    print("📚 Building FAISS index from knowledge base...")
    model  = get_model()
    texts  = [d["text"] for d in ALL_DOCS]

    # Generate embeddings
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        batch_size=16
    ).astype("float32")

    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)

    # Build flat inner product index (= cosine after normalization)
    dim   = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # Persist to disk
    faiss.write_index(index, str(index_file))
    docs_file.write_text(
        json.dumps(ALL_DOCS, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    _index = index
    _docs  = list(ALL_DOCS)
    print(f"✅ FAISS index built — {len(_docs)} documents indexed")


def similarity_search(
    query: str,
    n_results: int = 4,
    where: dict = None
) -> list[dict]:
    """Search knowledge base and return top matching documents."""
    global _index, _docs

    if _index is None:
        init_vector_store()

    model = get_model()

    # Encode and normalize query
    q_vec = model.encode([query]).astype("float32")
    faiss.normalize_L2(q_vec)

    # Search — get more results if we need to filter
    k = min(n_results * 3 if where else n_results, len(_docs))
    distances, indices = _index.search(q_vec, k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < 0 or idx >= len(_docs):
            continue

        doc = _docs[idx]

        # Apply metadata filter if provided
        if where:
            meta = doc.get("metadata", {})
            if not all(meta.get(key) == val for key, val in where.items()):
                continue

        results.append({
            "text":     doc["text"],
            "metadata": doc.get("metadata", {}),
            "score":    float(distances[0][i])
        })

        if len(results) >= n_results:
            break

    return results