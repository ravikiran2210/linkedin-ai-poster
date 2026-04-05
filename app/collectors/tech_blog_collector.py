"""Collector for tech blogs that don't have clean RSS – scrapes known pages."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.collectors.base import BaseCollector, CollectedItem
from app.utils.text_utils import strip_html

logger = logging.getLogger(__name__)

# Blog pages to check (title regex to filter AI content)
BLOG_SOURCES: list[dict] = [
    {
        "name": "Meta AI Blog",
        "url": "https://ai.meta.com/blog/",
        "title_pattern": r"<h[23][^>]*>.*?<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
    },
    {
        "name": "NVIDIA AI Blog",
        "url": "https://blogs.nvidia.com/blog/category/deep-learning/",
        "title_pattern": r"<h[23][^>]*>.*?<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
    },
]

AI_KEYWORDS = re.compile(
    r"(llm|gpt|transformer|diffusion|agent|rag|fine.?tun|benchmark|"
    r"inference|multimodal|neural|deep.?learn|machine.?learn|"
    r"language.?model|reasoning|open.?source)",
    re.IGNORECASE,
)


class TechBlogCollector(BaseCollector):
    """Scrapes known AI/ML blog index pages for new post links."""

    name = "tech_blog"
    source_type = "blog"

    def __init__(self, sources: list[dict] | None = None) -> None:
        self.sources = sources or BLOG_SOURCES

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
    async def _fetch_page(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    async def collect(self) -> list[CollectedItem]:
        items: list[CollectedItem] = []

        for src in self.sources:
            try:
                html = await self._fetch_page(src["url"])
                matches = re.findall(src["title_pattern"], html, re.DOTALL)

                for href, raw_title in matches[:15]:
                    title = strip_html(raw_title).strip()
                    if not title or not AI_KEYWORDS.search(title):
                        continue

                    # Resolve relative URLs
                    if href.startswith("/"):
                        from urllib.parse import urlparse
                        parsed = urlparse(src["url"])
                        href = f"{parsed.scheme}://{parsed.netloc}{href}"

                    items.append(
                        CollectedItem(
                            source_name=src["name"],
                            source_type="blog",
                            external_id=href,
                            title=title,
                            url=href,
                            published_at=datetime.now(timezone.utc),
                            content="",
                            metadata={"blog": src["name"]},
                        )
                    )
            except Exception:
                logger.exception("Blog collector failed for %s", src["name"])

        logger.info("Blog collector gathered %d items", len(items))
        return items
