"""Runs all collectors and returns a unified list of CollectedItems."""

from __future__ import annotations

import asyncio
import logging

from app.collectors.arxiv_collector import ArxivCollector
from app.collectors.base import BaseCollector, CollectedItem
from app.collectors.github_collector import GitHubReleaseCollector
from app.collectors.rss_collector import RSSCollector
from app.collectors.tech_blog_collector import TechBlogCollector

logger = logging.getLogger(__name__)


class CollectorAggregator:
    """Orchestrates all collectors and merges results."""

    def __init__(self, collectors: list[BaseCollector] | None = None) -> None:
        self.collectors = collectors or [
            RSSCollector(),
            ArxivCollector(),
            GitHubReleaseCollector(),
            TechBlogCollector(),
        ]

    async def collect_all(self) -> list[CollectedItem]:
        """Run every collector concurrently and merge results."""
        tasks = [c.collect() for c in self.collectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        items: list[CollectedItem] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Collector %s failed: %s",
                    self.collectors[i].name,
                    result,
                )
                continue
            items.extend(result)

        logger.info("Aggregator collected %d total items from %d collectors", len(items), len(self.collectors))
        return items
