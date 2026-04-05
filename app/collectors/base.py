"""Base collector interface and shared CollectedItem schema."""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class CollectedItem(BaseModel):
    """Common schema every collector normalizes into."""

    source_name: str
    source_type: str  # rss | arxiv | github | blog
    external_id: str
    title: str
    url: str
    author: Optional[str] = None
    published_at: Optional[dt.datetime] = None
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseCollector(ABC):
    """Abstract base for all collectors."""

    name: str = "base"
    source_type: str = "unknown"

    @abstractmethod
    async def collect(self) -> list[CollectedItem]:
        """Fetch items from the source and return normalized CollectedItems."""
        ...
