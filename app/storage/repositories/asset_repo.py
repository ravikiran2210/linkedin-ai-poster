"""Repository for assets table."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models import Asset


class AssetRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def insert(self, asset: Asset) -> Asset:
        self._s.add(asset)
        await self._s.flush()
        return asset

    async def insert_many(self, assets: list[Asset]) -> list[Asset]:
        self._s.add_all(assets)
        await self._s.flush()
        return assets

    async def get_by_candidate(self, candidate_id: int) -> Sequence[Asset]:
        stmt = (
            select(Asset)
            .where(Asset.candidate_id == candidate_id)
            .order_by(Asset.sort_order)
        )
        result = await self._s.execute(stmt)
        return result.scalars().all()
