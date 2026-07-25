import json
import logging
from io import BytesIO

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from PIL import Image
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from config import settings

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=settings.GEMINI_API_KEY)


class GeminiUnavailableError(Exception):
    """Raised when Gemini is overloaded/unavailable after retries are exhausted."""
    pass


# Retry only on transient server-side errors (503 overloaded, 500s).
# Don't retry on ClientError (400s) — a bad request will fail the same way every time.
_retry_gemini = retry(
    retry=retry_if_exception_type(ServerError),
    wait=wait_exponential(multiplier=1, min=2, max=20),  # 2s, 4s, 8s...
    stop=stop_after_attempt(4),
    reraise=True,
)


@_retry_gemini
async def _generate_content(**kwargs):
    try:
        return await _client.aio.models.generate_content(**kwargs)
    except ServerError as e:
        logger.warning(f"Gemini server error, will retry: {e}")
        raise
    except ClientError as e:
        logger.error(f"Gemini client error (not retrying): {e}")
        raise


async def generate(prompt: str, system: str = "") -> str:
    """Text generation via Gemini."""
    config = types.GenerateContentConfig(
        system_instruction=system or None,
        temperature=0.3,
        top_p=0.9,
    )
    try:
        response = await _generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
    except ServerError as e:
        raise GeminiUnavailableError(
            "Gemini is currently overloaded. Please try again in a moment."
        ) from e
    return (response.text or "").strip()


async def generate_json(prompt: str, system: str = "") -> dict:
    """Generate and parse JSON from Gemini."""
    full_system = system + "\nYou MUST respond with valid JSON only. No markdown, no explanation."
    config = types.GenerateContentConfig(
        system_instruction=full_system,
        temperature=0.3,
        top_p=0.9,
        response_mime_type="application/json",
    )
    try:
        response = await _generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
    except ServerError as e:
        raise GeminiUnavailableError(
            "Gemini is currently overloaded. Please try again in a moment."
        ) from e

    text = (response.text or "").strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


async def resize_image(image_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(image_bytes))
    img.thumbnail((1024, 1024))
    buffer = BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


async def vision_analyze(image_bytes: bytes, prompt: str) -> str:
    """Analyze an image using Gemini's multimodal model."""
    image_bytes = await resize_image(image_bytes)
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    config = types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=300,
    )
    try:
        response = await _generate_content(
            model=settings.GEMINI_VISION_MODEL,
            contents=[image_part, prompt],
            config=config,
        )
    except ServerError as e:
        raise GeminiUnavailableError(
            "Gemini is currently overloaded. Please try again in a moment."
        ) from e
    return (response.text or "").strip()


@_retry_gemini
async def _embed_content(**kwargs):
    return await _client.aio.models.embed_content(**kwargs)


async def embed(text: str) -> list[float]:
    """Get embeddings from Gemini."""
    try:
        result = await _embed_content(
            model=settings.GEMINI_EMBED_MODEL,
            contents=text,
        )
    except ServerError as e:
        raise GeminiUnavailableError(
            "Gemini is currently overloaded. Please try again in a moment."
        ) from e
    return result.embeddings[0].values