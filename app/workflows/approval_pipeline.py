"""Approval workflow: approve a draft and trigger publishing."""

from __future__ import annotations

import logging

from app.services.publishing_service import PublishingService
from app.storage.db import async_session_factory
from app.storage.repositories.post_repo import DraftPostRepo

logger = logging.getLogger(__name__)


class ApprovalPipeline:
    """Handle manual approval of drafts."""

    async def approve_and_publish(self, draft_id: int) -> dict:
        """Approve a draft, then publish it."""
        async with async_session_factory() as session:
            repo = DraftPostRepo(session)
            draft = await repo.approve(draft_id)
            if not draft:
                return {"status": "error", "message": f"Draft {draft_id} not found or not in draft status"}

            await session.commit()

            pub_svc = PublishingService(session)
            pub = await pub_svc.publish_draft(draft_id)

            if pub:
                return {
                    "status": "published",
                    "draft_id": draft_id,
                    "linkedin_url": pub.linkedin_post_url,
                }
            return {"status": "error", "message": "Publishing failed"}

    async def reject(self, draft_id: int) -> dict:
        """Reject a draft."""
        async with async_session_factory() as session:
            repo = DraftPostRepo(session)
            draft = await repo.reject(draft_id)
            if not draft:
                return {"status": "error", "message": f"Draft {draft_id} not found or not in draft status"}
            await session.commit()
            return {"status": "rejected", "draft_id": draft_id}
