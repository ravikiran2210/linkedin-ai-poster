"""Remove duplicate items using title normalization, URL canonicalization, and content hashing."""

from __future__ import annotations

import logging

from app.collectors.base import CollectedItem
from app.utils.hash_utils import content_hash, normalize_and_hash
from app.utils.text_utils import normalize_title
from app.utils.url_utils import canonical_url

logger = logging.getLogger(__name__)


class Deduplicator:
    """Deduplicates a list of CollectedItems in memory."""

    def deduplicate(self, items: list[CollectedItem]) -> list[CollectedItem]:
        """Return items with duplicates removed. First occurrence wins."""
        seen_title_url: set[str] = set()
        seen_content: set[str] = set()
        unique: list[CollectedItem] = []

        for item in items:
            # Key 1: normalized title + canonical URL
            tu_key = normalize_and_hash(normalize_title(item.title), canonical_url(item.url))
            if tu_key in seen_title_url:
                continue
            seen_title_url.add(tu_key)

            # Key 2: content hash (if content is non-trivial)
            if item.content and len(item.content) > 50:
                c_hash = content_hash(item.content)
                if c_hash in seen_content:
                    continue
                seen_content.add(c_hash)

            unique.append(item)

        removed = len(items) - len(unique)
        if removed:
            logger.info("Deduplicator removed %d duplicates, %d remaining", removed, len(unique))
        return unique

    def duplicate_group_key(self, item: CollectedItem) -> str:
        """Return a grouping key for an item – items with the same key are about the same story."""
        return normalize_and_hash(normalize_title(item.title), canonical_url(item.url))
