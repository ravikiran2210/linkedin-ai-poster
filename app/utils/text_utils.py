"""Text normalisation helpers."""

from __future__ import annotations

import re
import unicodedata


def normalize_title(title: str) -> str:
    """Lowercase, strip whitespace, collapse spaces, remove non-alphanumeric."""
    title = unicodedata.normalize("NFKD", title)
    title = title.lower().strip()
    title = re.sub(r"\s+", " ", title)
    return title


def truncate(text: str, max_length: int = 300) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def word_count(text: str) -> int:
    return len(text.split())


def strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text)
