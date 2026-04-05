"""Repository for draft_posts and published_posts tables."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.storage.models import DraftPost, PublishedPost


class DraftPostRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def insert(self, draft: DraftPost) -> DraftPost:
        self._s.add(draft)
        await self._s.flush()
        return draft

    async def get_by_id(self, draft_id: int) -> Optional[DraftPost]:
        stmt = (
            select(DraftPost)
            .options(joinedload(DraftPost.candidate))
            .where(DraftPost.id == draft_id)
        )
        result = await self._s.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pending(self) -> Sequence[DraftPost]:
        stmt = (
            select(DraftPost)
            .options(joinedload(DraftPost.candidate))
            .where(DraftPost.status == "draft")
            .order_by(DraftPost.created_at.desc())
        )
        result = await self._s.execute(stmt)
        return result.scalars().unique().all()

    async def approve(self, draft_id: int) -> Optional[DraftPost]:
        draft = await self._s.get(DraftPost, draft_id)
        if draft and draft.status == "draft":
            draft.status = "approved"
            await self._s.flush()
        return draft

    async def reject(self, draft_id: int) -> Optional[DraftPost]:
        draft = await self._s.get(DraftPost, draft_id)
        if draft and draft.status == "draft":
            draft.status = "rejected"
            await self._s.flush()
        return draft

    async def mark_published(self, draft_id: int) -> None:
        draft = await self._s.get(DraftPost, draft_id)
        if draft:
            draft.status = "published"
            await self._s.flush()


class PublishedPostRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def insert(self, post: PublishedPost) -> PublishedPost:
        self._s.add(post)
        await self._s.flush()
        return post

    async def get_by_draft_id(self, draft_id: int) -> Optional[PublishedPost]:
        stmt = select(PublishedPost).where(PublishedPost.draft_post_id == draft_id)
        result = await self._s.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 30) -> Sequence[PublishedPost]:
        stmt = (
            select(PublishedPost)
            .options(joinedload(PublishedPost.draft_post))
            .order_by(PublishedPost.posted_at.desc())
            .limit(limit)
        )
        result = await self._s.execute(stmt)
        return result.scalars().unique().all()
