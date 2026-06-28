import base64
import httpx
import json
from config import settings

OLLAMA_URL = settings.OLLAMA_BASE_URL

async def generate(prompt: str, system: str = "") -> str:
    """Text generation via Ollama."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.3, "top_p": 0.9}
    }
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        r.raise_for_status()
        return r.json()["response"].strip()


async def generate_json(prompt: str, system: str = "") -> dict:
    """Generate and parse JSON from Ollama."""
    full_system = system + "\nYou MUST respond with valid JSON only. No markdown, no explanation."
    text = await generate(prompt, full_system)
    # strip markdown fences if present
    text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(text)


async def vision_analyze(image_bytes: bytes, prompt: str) -> str:
    """Analyze an image using Ollama vision model (llava)."""
    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "model": settings.OLLAMA_VISION_MODEL,
        "prompt": prompt,
        "images": [b64],
        "stream": False,
        "options": {"temperature": 0.2}
    }
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        r.raise_for_status()
        return r.json()["response"].strip()


async def embed(text: str) -> list[float]:
    """Get embeddings from Ollama."""
    payload = {"model": "nomic-embed-text", "prompt": text}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{OLLAMA_URL}/api/embeddings", json=payload)
        r.raise_for_status()
        return r.json()["embedding"]