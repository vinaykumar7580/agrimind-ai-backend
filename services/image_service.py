import os
import uuid
from pathlib import Path
from PIL import Image
import io

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def save_image(image_bytes: bytes, prefix: str = "img") -> str:
    """Save image to disk, return relative path."""
    img = Image.open(io.BytesIO(image_bytes))
    # Convert to RGB if needed
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    # Resize if too large
    if max(img.size) > 1920:
        img.thumbnail((1920, 1920), Image.LANCZOS)

    filename = f"{prefix}_{uuid.uuid4().hex[:12]}.jpg"
    path = UPLOAD_DIR / filename
    img.save(path, "JPEG", quality=85)
    return str(path)

def load_image_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def get_image_url(path: str) -> str:
    return f"/uploads/{Path(path).name}"