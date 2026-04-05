"""Fetch relevant images from Google via SerpAPI based on topic/title."""

from __future__ import annotations

import logging
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search.json"


class ImageFetcher:
    """Fetch topic-relevant images from Google Images via SerpAPI and download them locally."""

    def __init__(self) -> None:
        self.api_key = settings.serpapi_key
        self.image_count = settings.image_count
        self.output_dir = Path(settings.generated_assets_dir) / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_images(
        self,
        candidate_id: int,
        title: str,
        topic: str,
    ) -> list[str]:
        """Search for images and download them. Returns list of local file paths."""
        if not self.api_key:
            logger.warning("SERPAPI_KEY not set — skipping image fetch")
            return []

        # Build a search query from the title + topic
        query = self._build_query(title, topic)
        image_urls = await self._search_images(query)

        if not image_urls:
            logger.warning("No images found for query: %s", query)
            return []

        # Download images locally
        paths: list[str] = []
        for i, url in enumerate(image_urls[: self.image_count]):
            path = await self._download_image(url, candidate_id, i)
            if path:
                paths.append(path)

        logger.info("Fetched %d images for candidate %d", len(paths), candidate_id)
        return paths

    def _build_query(self, title: str, topic: str) -> str:
        """Build a Google Image search query from title and topic."""
        # Use title keywords + topic for relevant results
        topic_label = topic.replace("_", " ")
        # Keep query concise — take first 8 words of title
        title_words = title.split()[:8]
        short_title = " ".join(title_words)
        return f"{short_title} {topic_label} AI technology"

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def _search_images(self, query: str) -> list[str]:
        """Call SerpAPI Google Images search and return image URLs."""
        params = {
            "engine": "google_images",
            "q": query,
            "api_key": self.api_key,
            "num": self.image_count + 2,  # fetch a few extra in case download fails
            "safe": "active",
            "ijn": "0",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(SERPAPI_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        images = data.get("images_results", [])
        urls: list[str] = []
        for img in images:
            original = img.get("original")
            if original and self._is_valid_image_url(original):
                urls.append(original)

        logger.info("SerpAPI returned %d image URLs for: %s", len(urls), query[:60])
        return urls

    @staticmethod
    def _is_valid_image_url(url: str) -> bool:
        """Basic filter for image URLs."""
        lower = url.lower()
        return any(ext in lower for ext in (".jpg", ".jpeg", ".png", ".webp"))

    async def _download_image(self, url: str, candidate_id: int, index: int) -> str | None:
        """Download a single image and save locally. Returns file path or None."""
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()

                content_type = resp.headers.get("content-type", "")
                if "image" not in content_type:
                    return None

                # Determine extension
                if "png" in content_type:
                    ext = "png"
                elif "webp" in content_type:
                    ext = "webp"
                else:
                    ext = "jpg"

                filename = f"candidate_{candidate_id}_img_{index + 1}.{ext}"
                path = self.output_dir / filename
                path.write_bytes(resp.content)
                logger.info("Downloaded image: %s (%d KB)", filename, len(resp.content) // 1024)
                return str(path)

        except Exception:
            logger.warning("Failed to download image: %s", url[:80])
            return None
