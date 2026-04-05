"""Publish approved drafts to LinkedIn."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.publisher.post_creator import PostCreator
from app.storage.models import PublishedPost
from app.storage.repositories.asset_repo import AssetRepo
from app.storage.repositories.post_repo import DraftPostRepo, PublishedPostRepo
from app.utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class PublishingService:
    """Upload assets and publish an approved draft to LinkedIn."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.draft_repo = DraftPostRepo(session)
        self.pub_repo = PublishedPostRepo(session)
        self.asset_repo = AssetRepo(session)
        self.post_creator = PostCreator()

    async def publish_draft(self, draft_id: int) -> PublishedPost | None:
        """Publish a draft. Returns the PublishedPost or None if draft not found/not approved."""
        draft = await self.draft_repo.get_by_id(draft_id)
        if not draft:
            logger.error("Draft %d not found", draft_id)
            return None

        if draft.status not in ("approved", "draft"):
            logger.warning("Draft %d has status '%s', cannot publish", draft_id, draft.status)
            return None

        # Gather asset file paths
        assets = await self.asset_repo.get_by_candidate(draft.candidate_id)
        image_paths = [a.file_path for a in assets if a.asset_type in ("slide", "image")]

        # Publish
        result = await self.post_creator.publish(
            caption=draft.full_caption,
            image_paths=image_paths,
        )

        # Persist published record
        pub = PublishedPost(
            draft_post_id=draft.id,
            linkedin_post_id=result.get("id", ""),
            linkedin_post_url=result.get("url", ""),
            posted_at=utc_now(),
        )
        await self.pub_repo.insert(pub)
        await self.draft_repo.mark_published(draft.id)
        await self.session.commit()

        logger.info("Published draft %d -> %s", draft_id, pub.linkedin_post_url)
        return pub
