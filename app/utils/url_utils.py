"""URL normalisation helpers."""

from __future__ import annotations

from urllib.parse import urlparse


def canonical_url(url: str) -> str:
    """Strip fragments, trailing slashes, and common tracking params."""
    parsed = urlparse(url)
    clean = parsed._replace(fragment="", query="")
    path = clean.path.rstrip("/")
    return f"{clean.scheme}://{clean.netloc}{path}"


def domain(url: str) -> str:
    """Extract the bare domain from a URL."""
    return urlparse(url).netloc.lower().replace("www.", "")
