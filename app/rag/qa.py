from langchain_ollama import ChatOllama
from app.rag.retriever import retrieve

llm = ChatOllama(
    model="llama3",
    temperature=0.2
)

def ask_rag(query: str):

    docs = retrieve(query)

    context = "\n\n".join(
        [d.page_content for d in docs]
    )

    prompt = f"""
You are an agriculture expert AI.

Use ONLY the context below to answer.

Context:
{context}

Question:
{query}

Answer in simple farming language:
"""

    response = llm.invoke(prompt)

    return response.content