from langchain_ollama import ChatOllama

from app.rag.retriever import retrieve_context

llm = ChatOllama(
    model="llama3",
    temperature=0.2
)

def ask_rag(question: str):

    docs = retrieve_context(question)

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    prompt = f"""
You are an agriculture expert.

Answer ONLY from the context below.

Context:
{context}

Question:
{question}

Answer:
"""

    response = llm.invoke(prompt)

    return response.content