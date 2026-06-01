import os
from fastapi import UploadFile
from app.loaders.pdf_loader import load_pdf
from app.rag.ingest import ingest_docs

UPLOAD_DIR = "uploads"

async def save_file(file: UploadFile):

    # Create uploads folder if not exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return file_path

async def process_pdf(file_path: str):

    docs = load_pdf(file_path)

    chunk_count = ingest_docs(docs)

    return {
        "status": "indexed",
        "chunks": chunk_count
    }