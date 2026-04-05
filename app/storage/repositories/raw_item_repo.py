"""Repository for raw_items table."""

from __future__ import annotations

import datetime as dt
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.storage.models import RawItem


class RawItemRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def exists_by_content_hash(self, content_hash: str) -> bool:
        stmt = select(RawItem.id).where(RawItem.content_hash == content_hash).limit(1)
        result = await self._s.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_external_id(self, source_id: int, external_id: str) -> bool:
        stmt = (
            select(RawItem.id)
            .where(RawItem.source_id == source_id, RawItem.external_id == external_id)
            .limit(1)
        )
        result = await self._s.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def insert(self, item: RawItem) -> RawItem:
        self._s.add(item)
        await self._s.flush()
        return item

    async def get_recent(self, since: dt.datetime) -> Sequence[RawItem]:
        stmt = (
            select(RawItem)
            .where(RawItem.fetched_at >= since)
            .order_by(RawItem.fetched_at.desc())
        )
        result = await self._s.execute(stmt)
        return result.scalars().all()

    async def get_without_candidate(self, since: dt.datetime) -> Sequence[RawItem]:
        """Return raw items that haven't been processed into candidates yet."""
        stmt = (
            select(RawItem)
            .options(joinedload(RawItem.source))
            .outerjoin(RawItem.candidate)
            .where(RawItem.fetched_at >= since)
            .filter(RawItem.candidate == None)  # noqa: E711
            .order_by(RawItem.fetched_at.desc())
        )
        result = await self._s.execute(stmt)
        return result.scalars().unique().all()
