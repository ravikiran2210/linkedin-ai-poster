"""Generate images using Gemini's image generation capabilities or Pillow fallback."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_IMAGE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
)


class ImageGenerator:
    """Generate images via Gemini or fall back to Pillow-rendered slides."""

    def __init__(self) -> None:
        self.api_key = settings.gemini_api_key
        self.output_dir = Path(settings.generated_assets_dir) / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate(self, prompt: str, filename: str) -> str | None:
        """Generate an image and return the local file path, or None on failure.

        MVP falls back to Pillow carousel rendering if Gemini image gen is unavailable.
        """
        if self.api_key:
            try:
                return await self._generate_with_gemini(prompt, filename)
            except Exception:
                logger.warning("Gemini image generation failed for '%s', skipping", filename)

        logger.info("No image API available – carousel_renderer will handle slide generation")
        return None

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
    async def _generate_with_gemini(self, prompt: str, filename: str) -> str | None:
        """Use Gemini to generate an image.

        NOTE: Gemini 2.5 Flash primarily generates text. For image generation,
        you may need to use Imagen via the same API. This is a forward-compatible stub
        that can be swapped to the correct endpoint when image gen is GA.
        """
        # TODO: Switch to Imagen 3 endpoint when available:
        # https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict
        payload = {
            "contents": [{"parts": [{"text": f"Generate an image: {prompt}"}]}],
            "generationConfig": {"responseMimeType": "image/png"},
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{GEMINI_IMAGE_URL}?key={self.api_key}",
                json=payload,
            )
            if resp.status_code != 200:
                logger.warning("Gemini image API returned %d", resp.status_code)
                return None

            data = resp.json()
            # Extract inline image data if present
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            for part in parts:
                if "inlineData" in part:
                    import base64
                    img_bytes = base64.b64decode(part["inlineData"]["data"])
                    path = self.output_dir / filename
                    path.write_bytes(img_bytes)
                    logger.info("Generated image saved to %s", path)
                    return str(path)

        return None
