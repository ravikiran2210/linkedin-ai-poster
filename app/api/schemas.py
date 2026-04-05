"""Pydantic schemas for API responses."""

from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"


class DraftSummary(BaseModel):
    id: int
    candidate_id: int
    hook: str
    status: str
    hashtags: str
    created_at: dt.datetime


class DraftDetail(BaseModel):
    id: int
    candidate_id: int
    hook: str
    body: str
    cta: str
    full_caption: str
    hashtags: str
    image_strategy: str
    status: str
    created_at: dt.datetime
    updated_at: dt.datetime
    topic: Optional[str] = None
    title: Optional[str] = None
    score: Optional[float] = None


class ApprovalResponse(BaseModel):
    status: str
    draft_id: int
    message: str = ""
    linkedin_url: Optional[str] = None


class PipelineResponse(BaseModel):
    status: str
    new_items: int = 0
    selected: Optional[dict] = None
    draft_id: Optional[int] = None
    published: bool = False
