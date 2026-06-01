from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3",
    temperature=0.3
)

def ask_ai(question):

    response = llm.invoke(question)

    return response.content