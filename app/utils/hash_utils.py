"""Hashing utilities for deduplication."""

from __future__ import annotations

import xxhash


def content_hash(text: str) -> str:
    """Fast 64-bit hash of content, returned as hex string."""
    return xxhash.xxh64(text.encode("utf-8")).hexdigest()


def normalize_and_hash(title: str, url: str) -> str:
    """Hash a normalized (lowered, stripped) title + url combo."""
    normalized = f"{title.lower().strip()}|{url.lower().strip()}"
    return content_hash(normalized)
