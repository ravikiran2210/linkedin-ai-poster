"""SQLAlchemy ORM models for every table in the pipeline."""

from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── Sources ─────────────────────────────────────────────────────────


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # rss | arxiv | github | blog
    base_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    fetch_config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    raw_items: Mapped[list["RawItem"]] = relationship(back_populates="source")


# ── Raw Items ───────────────────────────────────────────────────────


class RawItem(Base):
    __tablename__ = "raw_items"
    __table_args__ = (
        Index("ix_raw_items_content_hash", "content_hash"),
        Index("ix_raw_items_external_id", "external_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    published_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped["Source"] = relationship(back_populates="raw_items")
    candidate: Mapped[Optional["Candidate"]] = relationship(back_populates="raw_item", uselist=False)


# ── Candidates ──────────────────────────────────────────────────────


class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (Index("ix_candidates_final_score", "final_score"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_item_id: Mapped[int] = mapped_column(ForeignKey("raw_items.id"), unique=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(64), nullable=False)
    short_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    normalized_title: Mapped[str] = mapped_column(String(1024), nullable=False)
    normalized_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duplicate_group_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    authority_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)
    interest_score: Mapped[float] = mapped_column(Float, default=0.0)
    clarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending | selected | rejected
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    raw_item: Mapped["RawItem"] = relationship(back_populates="candidate")
    assets: Mapped[list["Asset"]] = relationship(back_populates="candidate")
    draft_post: Mapped[Optional["DraftPost"]] = relationship(back_populates="candidate", uselist=False)


# ── Assets ──────────────────────────────────────────────────────────


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)  # slide | thumbnail | image
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(64), default="image/png")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate: Mapped["Candidate"] = relationship(back_populates="assets")


# ── Draft Posts ─────────────────────────────────────────────────────


class DraftPost(Base):
    __tablename__ = "draft_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), unique=True, nullable=False)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    cta: Mapped[str] = mapped_column(Text, nullable=False)
    full_caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[str] = mapped_column(Text, default="")
    image_strategy: Mapped[str] = mapped_column(String(32), default="carousel")
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft | approved | rejected | published
    llm_metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    candidate: Mapped["Candidate"] = relationship(back_populates="draft_post")
    published_post: Mapped[Optional["PublishedPost"]] = relationship(back_populates="draft_post", uselist=False)


# ── Published Posts ─────────────────────────────────────────────────


class PublishedPost(Base):
    __tablename__ = "published_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_post_id: Mapped[int] = mapped_column(ForeignKey("draft_posts.id"), unique=True, nullable=False)
    linkedin_post_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    linkedin_post_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    posted_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    reactions: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    analytics_last_synced_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    draft_post: Mapped["DraftPost"] = relationship(back_populates="published_post")
