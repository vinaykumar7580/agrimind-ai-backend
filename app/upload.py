import os
from fastapi import UploadFile

from app.rag.ingest import ingest_documents
from app.loaders.pdf_loader import load_pdf

BASE_UPLOAD_DIR = "uploads"

PDF_DIR = os.path.join(BASE_UPLOAD_DIR, "pdfs")
IMAGE_DIR = os.path.join(BASE_UPLOAD_DIR, "images")
EXCEL_DIR = os.path.join(BASE_UPLOAD_DIR, "excels")
DOC_DIR = os.path.join(BASE_UPLOAD_DIR, "docs")

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(EXCEL_DIR, exist_ok=True)
os.makedirs(DOC_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]


# -------------------------
# SAVE FILE
# -------------------------
async def save_file(file: UploadFile):

    extension = file.filename.split(".")[-1].lower()

    if extension == "pdf":
        folder = PDF_DIR

    elif extension in ["png", "jpg", "jpeg", "webp"]:
        folder = IMAGE_DIR

    elif extension in ["xlsx", "xls", "csv"]:
        folder = EXCEL_DIR

    elif extension in ["doc", "docx"]:
        folder = DOC_DIR

    else:
        raise Exception("Unsupported file type")

    file_path = os.path.join(folder, file.filename)

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    # 🔥 IMPORTANT: process AFTER saving
    if file_path.endswith(".pdf"):
        await process_pdf(file_path)

    return file_path


# -------------------------
# PROCESS PDF (RAG INDEXING)
# -------------------------
async def process_pdf(file_path: str):

    docs = load_pdf(file_path)

    chunk_count = ingest_documents(docs)

    return {
        "status": "indexed",
        "chunks": chunk_count
    }


# -------------------------
# IMAGE SAVE
# -------------------------
async def save_image(file: UploadFile):

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise Exception("Only jpg, jpeg, png, webp allowed")

    file_path = os.path.join(IMAGE_DIR, file.filename)

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path