from fastapi import FastAPI
from fastapi import UploadFile, File, HTTPException
from pydantic import BaseModel

from app.graph.workflow import workflow
from app.chatbot import ask_ai
from app.upload import save_file, process_pdf
from app.loaders.pdf_loader import load_pdf
from app.rag.ingest import ingest_documents
from app.rag.qa import ask_rag
from app.upload import (
    save_image,
    validate_image
)



app = FastAPI(
    title="AgriMind AI",
    version="1.0.0"
)

class PDFRequest(BaseModel):
    file_path: str

class IndexPDFRequest(BaseModel):
    file_path: str

class Query(BaseModel):
    question: str

class QuestionRequest(BaseModel):
    question: str

class AgentChatRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {
        "message": "AgriMind AI Backend Running"
    }


@app.post("/ask")
def chat(data: ChatRequest):

    answer = ask_ai(data.question)

    return {
        "answer": answer
    }


@app.post("/chat")
def chat(data: Query):

    result = workflow.invoke({
        "query": data.question,
        "context": "",
        "answer": ""
    })

    return {
        "answer": result["answer"]
    }

@app.post("/upload")
async def upload(
    file: UploadFile = File(...)
):
    try:

        path = await save_file(file)

        return {
            "status": "success",
            "path": path,
            "filename": file.filename
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.post("/read-pdf")
def read_pdf(data: PDFRequest):

    docs = load_pdf(data.file_path)

    return {
        "total_pages": len(docs),
        "preview": docs[0].page_content[:1000]
    }


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    file_path = await save_file(file)

    result = await process_pdf(file_path)

    return result

@app.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...)
):
    try:

        await validate_image(file)

        file_path = await save_image(file)

        return {
            "status": "success",
            "image_path": file_path
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.post("/index-pdf")
def index_pdf(data: IndexPDFRequest):

    docs = load_pdf(data.file_path)

    chunks = ingest_documents(docs)

    return {
        "status": "indexed",
        "chunks": chunks
    }

@app.post("/rag-chat")
def rag_chat(data: QuestionRequest):

    answer = ask_rag(data.question)

    return {
        "answer": answer
    }

@app.post("/agent-chat")
def agent_chat(
    data: AgentChatRequest
):

    result = workflow.invoke(
        {
            "query": data.question,
            "context": "",
            "answer": ""
        }
    )

    return {
        "answer": result["answer"]
    }