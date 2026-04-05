"""Main pipeline: fetch → rank → content → draft → approve/publish."""

from __future__ import annotations

import logging

from app.config import settings
from app.publisher.approval_router import ApprovalRouter
from app.services.content_service import ContentService
from app.services.fetch_service import FetchService
from app.services.publishing_service import PublishingService
from app.services.ranking_service import RankingService
from app.storage.db import async_session_factory

logger = logging.getLogger(__name__)


class DailyPipeline:
    """Orchestrates the full pipeline end-to-end."""

    async def run(self) -> dict:
        """Execute the pipeline. Returns a status summary dict."""
        logger.info("=== Pipeline Starting ===")
        result = {"status": "ok", "new_items": 0, "selected": None, "draft_id": None, "published": False}

        async with async_session_factory() as session:
            # Step 1: Fetch fresh items from all sources
            fetch_svc = FetchService(session)
            new_count = await fetch_svc.fetch_and_store()
            result["new_items"] = new_count
            logger.info("Step 1 complete: fetched %d new items", new_count)

            # Step 2: Rank and select the best candidate
            ranking_svc = RankingService(session)
            selected = await ranking_svc.process_and_rank()
            if not selected:
                logger.warning("No candidate selected — pipeline stopping")
                result["status"] = "no_candidate"
                return result

            result["selected"] = {
                "id": selected.id,
                "topic": selected.topic,
                "score": selected.final_score,
                "title": selected.normalized_title,
            }
            logger.info("Step 2 complete: selected candidate %d (score=%.3f)", selected.id, selected.final_score)

            # Step 3: Build content (caption + images)
            content_svc = ContentService(session)
            draft = await content_svc.build_draft(selected)
            result["draft_id"] = draft.id
            logger.info("Step 3 complete: draft %d created", draft.id)

            # Step 4: Publish or send for approval
            if settings.auto_approve:
                pub_svc = PublishingService(session)
                pub = await pub_svc.publish_draft(draft.id)
                result["published"] = pub is not None
                logger.info("Step 4 complete: auto-published=%s", result["published"])
            else:
                router = ApprovalRouter()
                await router.notify_draft_ready(
                    draft_id=draft.id,
                    title=selected.normalized_title,
                    preview_url=f"http://localhost:8000/drafts/{draft.id}",
                )
                logger.info("Step 4 complete: draft sent for manual approval")

        logger.info("=== Pipeline Complete === %s", result)
        return result
