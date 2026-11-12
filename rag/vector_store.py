import json
import numpy as np
import faiss
from pathlib import Path
from fastembed import TextEmbedding
from rag.knowledge_base import ALL_DOCS

STORE_PATH = Path("./faiss_store")
# all-MiniLM-L6-v2 run with ONNX instead of PyTorch: identical vectors to the
# sentence-transformers version (so the saved index still matches) at about a
# quarter of the memory. The model is cached in the project folder so a deploy
# can download it once at build time.
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_CACHE = Path("./.fastembed_cache")
_model: TextEmbedding = None
_index: faiss.Index = None
_docs: list = []

def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        print("📦 Loading embedding model...")
        _model = TextEmbedding(EMBED_MODEL, cache_dir=str(MODEL_CACHE))
        print("✅ Embedding model loaded")
    return _model

def _encode(texts: list[str]) -> np.ndarray:
    return np.array(list(get_model().embed(texts, batch_size=16)), dtype="float32")

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
        get_model()   # load now so the first chat or scan isn't slow
        return

    # Build index from scratch
    print("📚 Building FAISS index from knowledge base...")
    texts  = [d["text"] for d in ALL_DOCS]

    # Generate embeddings
    embeddings = _encode(texts)

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

    # Encode and normalize query
    q_vec = _encode([query])
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