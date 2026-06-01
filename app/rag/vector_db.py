from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Embedding model (FREE + fast)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Vector DB
vector_store = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings
)