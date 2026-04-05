"""Score and rank raw items into candidates."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import CollectedItem
from app.config import settings
from app.processors.classifier import Classifier
from app.processors.deduplicator import Deduplicator
from app.processors.scorer import Scorer
from app.processors.selector import Selector
from app.processors.summarizer import Summarizer
from app.storage.models import Candidate, RawItem
from app.storage.repositories.candidate_repo import CandidateRepo
from app.storage.repositories.raw_item_repo import RawItemRepo
from app.utils.text_utils import normalize_title
from app.utils.time_utils import hours_ago

logger = logging.getLogger(__name__)


class RankingService:
    """Process raw items → scored candidates → select the best one."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.raw_repo = RawItemRepo(session)
        self.cand_repo = CandidateRepo(session)
        self.classifier = Classifier()
        self.scorer = Scorer()
        self.dedup = Deduplicator()
        self.summarizer = Summarizer()
        self.selector = Selector()

    async def process_and_rank(self) -> Candidate | None:
        """Score unprocessed raw items, create candidates, and select the best."""
        since = hours_ago(settings.fetch_window_hours)
        raw_items = await self.raw_repo.get_without_candidate(since)

        if raw_items:
            # Convert to CollectedItem for processing
            collected = [self._raw_to_collected(ri) for ri in raw_items]

            # Create candidates
            for raw_item, ci in zip(raw_items, collected):
                topic = self.classifier.classify(ci)
                scores = self.scorer.score(ci)
                summary = self.summarizer.summarize(ci.title, ci.content)
                dup_key = self.dedup.duplicate_group_key(ci)

                # Skip if duplicate group already has a candidate
                if await self.cand_repo.exists_by_duplicate_key(dup_key):
                    continue

                cand = Candidate(
                    raw_item_id=raw_item.id,
                    topic=topic,
                    short_summary=summary,
                    normalized_title=normalize_title(ci.title),
                    normalized_content=ci.content[:2000] if ci.content else None,
                    duplicate_group_key=dup_key,
                    authority_score=scores["authority_score"],
                    recency_score=scores["recency_score"],
                    interest_score=scores["interest_score"],
                    clarity_score=scores["clarity_score"],
                    final_score=scores["final_score"],
                )
                await self.cand_repo.insert(cand)

            await self.session.commit()
            logger.info("Created candidates from %d new raw items", len(raw_items))
        else:
            logger.info("No new raw items — selecting from existing pending candidates")

        # Always try to select the best pending candidate
        top = await self.cand_repo.get_top_candidates(limit=20)
        if not top:
            logger.warning("No pending candidates available")
            return None

        recent = await self.cand_repo.get_recent_selected(days=7)

        recent_topics = [c.topic for c in recent]
        recent_sources = [
            c.raw_item.source.name if c.raw_item and c.raw_item.source else ""
            for c in recent
        ]

        selected = self.selector.select(
            list(top),
            recent_topics,
            recent_sources,
            min_score=settings.min_score_to_post,
        )

        if selected:
            await self.cand_repo.mark_selected(selected.id)
            await self.session.commit()

        return selected

    def _raw_to_collected(self, raw: RawItem) -> CollectedItem:
        return CollectedItem(
            source_name=raw.source.name if raw.source else "unknown",
            source_type=raw.source.type if raw.source else "unknown",
            external_id=raw.external_id,
            title=raw.title,
            url=raw.url,
            author=raw.author,
            published_at=raw.published_at,
            content=raw.raw_content or "",
            metadata=raw.raw_metadata_json or {},
        )
