"""Fetch items from all sources and persist as raw_items."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.aggregator import CollectorAggregator
from app.collectors.base import CollectedItem
from app.processors.deduplicator import Deduplicator
from app.storage.models import RawItem, Source
from app.storage.repositories.raw_item_repo import RawItemRepo
from app.utils.hash_utils import content_hash
from app.utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class FetchService:
    """Collect items from all sources, deduplicate, and store as raw_items."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.aggregator = CollectorAggregator()
        self.dedup = Deduplicator()
        self.repo = RawItemRepo(session)

    async def fetch_and_store(self) -> int:
        """Run all collectors, deduplicate, persist new items. Returns count of new items."""
        items = await self.aggregator.collect_all()
        items = self.dedup.deduplicate(items)

        new_count = 0
        for item in items:
            c_hash = content_hash(f"{item.title}|{item.url}|{item.content}")

            # Skip if already stored
            if await self.repo.exists_by_content_hash(c_hash):
                continue

            # Resolve or create source
            source_id = await self._resolve_source(item)

            raw = RawItem(
                source_id=source_id,
                external_id=item.external_id,
                title=item.title,
                url=item.url,
                author=item.author,
                published_at=item.published_at,
                raw_content=item.content,
                raw_metadata_json=item.metadata,
                content_hash=c_hash,
                fetched_at=utc_now(),
            )
            await self.repo.insert(raw)
            new_count += 1

        await self.session.commit()
        logger.info("FetchService stored %d new items", new_count)
        return new_count

    async def _resolve_source(self, item: CollectedItem) -> int:
        """Find or create a Source row. Returns source ID."""
        from sqlalchemy import select

        stmt = select(Source).where(Source.name == item.source_name).limit(1)
        result = await self.session.execute(stmt)
        source = result.scalar_one_or_none()

        if source:
            return source.id

        source = Source(
            name=item.source_name,
            type=item.source_type,
            base_url=item.url,
            is_active=True,
        )
        self.session.add(source)
        await self.session.flush()
        return source.id
