"""arXiv paper collector via the Atom API."""

from __future__ import annotations

import logging
from datetime import timezone
from urllib.parse import quote

import httpx
import feedparser
from dateutil.parser import parse as parse_date
from tenacity import retry, stop_after_attempt, wait_exponential

from app.collectors.base import BaseCollector, CollectedItem

logger = logging.getLogger(__name__)

ARXIV_QUERIES: list[str] = [
    "cat:cs.CL",   # Computation & Language (LLMs, NLP)
    "cat:cs.AI",   # Artificial Intelligence
    "cat:cs.LG",   # Machine Learning
    "cat:cs.MA",   # Multi-agent Systems
]

ARXIV_API = "http://export.arxiv.org/api/query"


class ArxivCollector(BaseCollector):
    """Fetches recent arXiv papers in AI/ML categories."""

    name = "arxiv"
    source_type = "arxiv"

    def __init__(self, queries: list[str] | None = None, max_results: int = 15) -> None:
        self.queries = queries or ARXIV_QUERIES
        self.max_results = max_results

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def _fetch(self, query: str) -> str:
        params = {
            "search_query": query,
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(ARXIV_API, params=params)
            resp.raise_for_status()
            return resp.text

    async def collect(self) -> list[CollectedItem]:
        items: list[CollectedItem] = []
        seen_ids: set[str] = set()

        for query in self.queries:
            try:
                raw = await self._fetch(query)
                feed = feedparser.parse(raw)
                for entry in feed.entries:
                    arxiv_id = entry.get("id", "")
                    if arxiv_id in seen_ids:
                        continue
                    seen_ids.add(arxiv_id)

                    published = None
                    if entry.get("published"):
                        try:
                            published = parse_date(entry["published"])
                            if published.tzinfo is None:
                                published = published.replace(tzinfo=timezone.utc)
                        except (ValueError, TypeError):
                            pass

                    authors = ", ".join(a.get("name", "") for a in entry.get("authors", []))
                    summary = entry.get("summary", "").replace("\n", " ").strip()

                    items.append(
                        CollectedItem(
                            source_name="arXiv",
                            source_type="arxiv",
                            external_id=arxiv_id,
                            title=entry.get("title", "").replace("\n", " ").strip(),
                            url=entry.get("link", arxiv_id),
                            author=authors or None,
                            published_at=published,
                            content=summary[:2000],
                            metadata={
                                "categories": [t["term"] for t in entry.get("tags", [])],
                            },
                        )
                    )
            except Exception:
                logger.exception("arXiv query failed: %s", query)

        logger.info("arXiv collector gathered %d items", len(items))
        return items
