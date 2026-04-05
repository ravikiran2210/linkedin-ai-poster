"""Repository for candidates table."""

from __future__ import annotations

import datetime as dt
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.storage.models import Candidate, RawItem, Source


class CandidateRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def insert(self, candidate: Candidate) -> Candidate:
        self._s.add(candidate)
        await self._s.flush()
        return candidate

    async def get_by_id(self, candidate_id: int) -> Optional[Candidate]:
        stmt = (
            select(Candidate)
            .options(joinedload(Candidate.raw_item).joinedload(RawItem.source))
            .where(Candidate.id == candidate_id)
        )
        result = await self._s.execute(stmt)
        return result.scalar_one_or_none()

    async def get_top_candidates(self, limit: int = 10) -> Sequence[Candidate]:
        stmt = (
            select(Candidate)
            .options(joinedload(Candidate.raw_item).joinedload(RawItem.source))
            .where(Candidate.status == "pending")
            .order_by(Candidate.final_score.desc())
            .limit(limit)
        )
        result = await self._s.execute(stmt)
        return result.scalars().unique().all()

    async def get_recent_selected(self, days: int = 7) -> Sequence[Candidate]:
        since = dt.datetime.now(dt.UTC) - dt.timedelta(days=days)
        stmt = (
            select(Candidate)
            .options(joinedload(Candidate.raw_item).joinedload(RawItem.source))
            .where(Candidate.status == "selected", Candidate.created_at >= since)
            .order_by(Candidate.created_at.desc())
        )
        result = await self._s.execute(stmt)
        return result.scalars().unique().all()

    async def mark_selected(self, candidate_id: int) -> None:
        cand = await self._s.get(Candidate, candidate_id)
        if cand:
            cand.status = "selected"
            await self._s.flush()

    async def mark_rejected(self, candidate_id: int, reason: str) -> None:
        cand = await self._s.get(Candidate, candidate_id)
        if cand:
            cand.status = "rejected"
            cand.rejection_reason = reason
            await self._s.flush()

    async def exists_by_duplicate_key(self, key: str) -> bool:
        stmt = select(Candidate.id).where(Candidate.duplicate_group_key == key).limit(1)
        result = await self._s.execute(stmt)
        return result.scalar_one_or_none() is not None
