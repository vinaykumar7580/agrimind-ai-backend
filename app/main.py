from fastapi import FastAPI
from fastapi import UploadFile, File
from pydantic import BaseModel

from app.chatbot import ask_ai
from app.upload import save_file, process_pdf
from app.loaders.pdf_loader import load_pdf
from app.rag.qa import ask_rag



app = FastAPI()

class Query(BaseModel):
    question: str


@app.post("/chat")
def chat(data: Query):

    answer = ask_rag(data.question)

    return {
        "answer": answer
    }

@app.post("/upload")
async def upload(
    file: UploadFile = File(...)
):
    path = await save_file(file)

    return {
        "status": "success",
        "file": path
    }

@app.post("/read-pdf")
async def read_pdf(file_path: str):
    docs = load_pdf(file_path)

    return {
        "pages": len(docs),
        "content_preview": docs[0].page_content[:500]
    }

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    file_path = await save_file(file)

    result = await process_pdf(file_path)

    return result