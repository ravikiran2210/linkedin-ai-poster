"""Select exactly one best candidate per day with guard-rails."""

from __future__ import annotations

import logging

from app.constants import MAX_CONSECUTIVE_SAME_SOURCE, MAX_CONSECUTIVE_SAME_TOPIC
from app.storage.models import Candidate

logger = logging.getLogger(__name__)


class Selector:
    """Picks the single best candidate from a scored list, applying diversity guard-rails."""

    def select(
        self,
        candidates: list[Candidate],
        recent_topics: list[str],
        recent_sources: list[str],
        min_score: float = 0.35,
    ) -> Candidate | None:
        """Return the highest-scoring candidate that passes guard-rails, or None."""
        # Sort by final_score descending
        ranked = sorted(candidates, key=lambda c: c.final_score, reverse=True)

        for cand in ranked:
            if cand.final_score < min_score:
                logger.info("All remaining candidates below min_score %.2f", min_score)
                return None

            # Guard-rail: same topic too many days in a row
            if self._too_many_consecutive(cand.topic, recent_topics, MAX_CONSECUTIVE_SAME_TOPIC):
                logger.debug("Skipping candidate %d – topic %s repeated too often", cand.id, cand.topic)
                continue

            # Guard-rail: same source too many days in a row
            source_name = cand.raw_item.source.name if cand.raw_item and cand.raw_item.source else ""
            if self._too_many_consecutive(source_name, recent_sources, MAX_CONSECUTIVE_SAME_SOURCE):
                logger.debug("Skipping candidate %d – source %s repeated too often", cand.id, source_name)
                continue

            logger.info("Selected candidate %d (score=%.3f, topic=%s)", cand.id, cand.final_score, cand.topic)
            return cand

        logger.warning("No candidate passed all guard-rails")
        return None

    @staticmethod
    def _too_many_consecutive(value: str, recent: list[str], max_count: int) -> bool:
        """Check if the last `max_count` entries in `recent` are all the same `value`."""
        if not value or len(recent) < max_count:
            return False
        tail = recent[:max_count]
        return all(v == value for v in tail)
