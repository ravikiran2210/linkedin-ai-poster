"""Sync post analytics from LinkedIn for ranking improvements."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.publisher.linkedin_client import LinkedInClient
from app.storage.repositories.post_repo import PublishedPostRepo
from app.utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Fetch engagement data from LinkedIn to improve future scoring."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.pub_repo = PublishedPostRepo(session)
        self.client = LinkedInClient()

    async def sync_analytics(self) -> int:
        """Update analytics for recent published posts. Returns count updated.

        TODO: Implement actual LinkedIn Analytics API calls when credentials are available.
        LinkedIn API: GET /organizationalEntityShareStatistics or /shares/{id}/statistics
        """
        if not self.client.is_configured:
            logger.info("LinkedIn not configured – skipping analytics sync")
            return 0

        posts = await self.pub_repo.list_recent(limit=30)
        updated = 0

        for post in posts:
            try:
                # TODO: Replace with actual API call:
                # GET /socialActions/{post.linkedin_post_id}
                # This would return likes, comments, shares, etc.
                logger.debug("Would sync analytics for post %s", post.linkedin_post_id)

                post.analytics_last_synced_at = utc_now()
                updated += 1
            except Exception:
                logger.exception("Failed to sync analytics for post %d", post.id)

        if updated:
            await self.session.commit()

        logger.info("Analytics sync complete: %d posts updated", updated)
        return updated
