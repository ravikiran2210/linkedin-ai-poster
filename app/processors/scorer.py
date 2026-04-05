"""Score candidates on recency, authority, interest, and clarity."""

from __future__ import annotations

import math
import re

from app.collectors.base import CollectedItem
from app.constants import (
    HIGH_AUTHORITY_SOURCES,
    HIGH_INTEREST_KEYWORDS,
    WEIGHT_AUTHORITY,
    WEIGHT_CLARITY,
    WEIGHT_INTEREST,
    WEIGHT_RECENCY,
)
from app.utils.time_utils import age_hours
from app.utils.url_utils import domain


class Scorer:
    """Compute sub-scores and a weighted final score for a CollectedItem."""

    # ── Recency ─────────────────────────────────────────────────────

    def recency_score(self, item: CollectedItem) -> float:
        """Newer = higher. Exponential decay: half-life ~24 h."""
        hours = age_hours(item.published_at)
        return math.exp(-0.03 * hours)  # 24 h ≈ 0.49, 48 h ≈ 0.24

    # ── Authority ───────────────────────────────────────────────────

    def authority_score(self, item: CollectedItem) -> float:
        """Score based on whether the source is a known high-authority org."""
        text = f"{item.source_name} {item.url} {item.author or ''}".lower()
        for src in HIGH_AUTHORITY_SOURCES:
            if src in text:
                return 1.0
        # Medium authority for known domains
        d = domain(item.url)
        if any(kw in d for kw in ("arxiv", "github", "huggingface")):
            return 0.8
        return 0.3

    # ── Interest ────────────────────────────────────────────────────

    def interest_score(self, item: CollectedItem) -> float:
        """Higher when the title/content contains high-interest keywords."""
        text = f"{item.title} {item.content}".lower()
        hits = sum(1 for kw in HIGH_INTEREST_KEYWORDS if kw in text)
        # Normalize: 3+ keyword hits → 1.0
        return min(hits / 3.0, 1.0)

    # ── Clarity ─────────────────────────────────────────────────────

    def clarity_score(self, item: CollectedItem) -> float:
        """Heuristic: prefer items with a clear title and enough content to explain."""
        score = 0.5

        title_words = len(item.title.split())
        if 5 <= title_words <= 20:
            score += 0.2
        elif title_words > 25:
            score -= 0.1

        content_len = len(item.content)
        if content_len > 200:
            score += 0.2
        if content_len > 50:
            score += 0.1

        # Penalize all-caps or junk titles
        if item.title.isupper():
            score -= 0.2

        return max(0.0, min(score, 1.0))

    # ── Final ───────────────────────────────────────────────────────

    def score(self, item: CollectedItem) -> dict[str, float]:
        """Return all sub-scores and the weighted final score."""
        r = self.recency_score(item)
        a = self.authority_score(item)
        i = self.interest_score(item)
        c = self.clarity_score(item)
        final = (
            WEIGHT_RECENCY * r
            + WEIGHT_INTEREST * i
            + WEIGHT_AUTHORITY * a
            + WEIGHT_CLARITY * c
        )
        return {
            "recency_score": round(r, 4),
            "authority_score": round(a, 4),
            "interest_score": round(i, 4),
            "clarity_score": round(c, 4),
            "final_score": round(final, 4),
        }
