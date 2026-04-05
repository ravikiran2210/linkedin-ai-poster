"""Retry pipeline for failed operations."""

from __future__ import annotations

import logging

from app.services.publishing_service import PublishingService
from app.storage.db import async_session_factory
from app.storage.repositories.post_repo import DraftPostRepo

logger = logging.getLogger(__name__)


class RetryPipeline:
    """Retry publishing for approved but unpublished drafts."""

    async def retry_pending_publishes(self) -> list[dict]:
        """Find approved drafts that haven't been published and try again."""
        results: list[dict] = []

        async with async_session_factory() as session:
            repo = DraftPostRepo(session)
            # Get approved but not published drafts
            from sqlalchemy import select
            from app.storage.models import DraftPost

            stmt = select(DraftPost).where(DraftPost.status == "approved")
            result = await session.execute(stmt)
            drafts = result.scalars().all()

            pub_svc = PublishingService(session)
            for draft in drafts:
                try:
                    pub = await pub_svc.publish_draft(draft.id)
                    results.append({
                        "draft_id": draft.id,
                        "status": "published" if pub else "failed",
                    })
                except Exception:
                    logger.exception("Retry failed for draft %d", draft.id)
                    results.append({"draft_id": draft.id, "status": "error"})

        return results
