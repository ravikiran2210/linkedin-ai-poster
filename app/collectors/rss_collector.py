"""RSS/Atom feed collector."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx
from dateutil.parser import parse as parse_date
from tenacity import retry, stop_after_attempt, wait_exponential

from app.collectors.base import BaseCollector, CollectedItem
from app.utils.text_utils import strip_html

logger = logging.getLogger(__name__)

# Default AI/ML RSS feeds
DEFAULT_FEEDS: list[dict[str, str]] = [
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Anthropic Research", "url": "https://www.anthropic.com/rss.xml"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
]


class RSSCollector(BaseCollector):
    """Collects items from one or more RSS/Atom feeds."""

    name = "rss"
    source_type = "rss"

    def __init__(self, feeds: list[dict[str, str]] | None = None) -> None:
        self.feeds = feeds or DEFAULT_FEEDS

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _fetch_feed(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            return resp.text

    async def collect(self) -> list[CollectedItem]:
        items: list[CollectedItem] = []
        for feed_cfg in self.feeds:
            try:
                raw_xml = await self._fetch_feed(feed_cfg["url"])
                parsed = feedparser.parse(raw_xml)
                for entry in parsed.entries[:20]:
                    item = self._parse_entry(entry, feed_cfg["name"])
                    if item:
                        items.append(item)
            except Exception:
                logger.exception("Failed to fetch RSS feed %s", feed_cfg["name"])
        logger.info("RSS collector gathered %d items", len(items))
        return items

    def _parse_entry(self, entry: Any, source_name: str) -> CollectedItem | None:
        title = getattr(entry, "title", None)
        link = getattr(entry, "link", None)
        if not title or not link:
            return None

        published = None
        for date_field in ("published", "updated", "created"):
            raw = getattr(entry, date_field, None)
            if raw:
                try:
                    published = parse_date(raw)
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass
                break

        summary = strip_html(getattr(entry, "summary", "") or "")

        return CollectedItem(
            source_name=source_name,
            source_type="rss",
            external_id=link,
            title=title.strip(),
            url=link,
            author=getattr(entry, "author", None),
            published_at=published,
            content=summary[:2000],
            metadata={"tags": [t.get("term", "") for t in getattr(entry, "tags", [])]},
        )
