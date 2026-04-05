"""Generate a short summary for a candidate item."""

from __future__ import annotations

from app.utils.text_utils import truncate


class Summarizer:
    """Creates a brief summary from title + content."""

    def summarize(self, title: str, content: str) -> str:
        """Return a 1-2 sentence summary combining title and content."""
        if not content:
            return title
        combined = f"{title}. {content}"
        # Take first two sentences or truncate
        sentences = combined.split(". ")
        summary = ". ".join(sentences[:2])
        return truncate(summary, max_length=500)
