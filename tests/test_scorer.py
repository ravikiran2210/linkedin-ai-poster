"""Tests for the scoring engine."""

from __future__ import annotations

import datetime as dt

import pytest

from app.collectors.base import CollectedItem
from app.processors.scorer import Scorer


@pytest.fixture
def scorer():
    return Scorer()


class TestRecencyScore:
    def test_recent_item_scores_high(self, scorer, sample_item):
        score = scorer.recency_score(sample_item)
        assert score > 0.7  # 6 hours old

    def test_old_item_scores_low(self, scorer):
        item = CollectedItem(
            source_name="Test",
            source_type="rss",
            external_id="old-1",
            title="Old News",
            url="https://example.com",
            published_at=dt.datetime.now(dt.UTC) - dt.timedelta(hours=72),
        )
        score = scorer.recency_score(item)
        assert score < 0.2

    def test_none_published_at_defaults(self, scorer):
        item = CollectedItem(
            source_name="Test",
            source_type="rss",
            external_id="no-date",
            title="No Date",
            url="https://example.com",
        )
        score = scorer.recency_score(item)
        assert score < 0.2  # treated as 72h old


class TestAuthorityScore:
    def test_openai_is_high_authority(self, scorer, sample_item):
        assert scorer.authority_score(sample_item) == 1.0

    def test_unknown_source_is_low(self, scorer):
        item = CollectedItem(
            source_name="Random Blog",
            source_type="blog",
            external_id="x",
            title="Something",
            url="https://randomsite.xyz/post",
        )
        assert scorer.authority_score(item) == 0.3


class TestInterestScore:
    def test_keyword_rich_item(self, scorer, sample_item):
        score = scorer.interest_score(sample_item)
        assert score > 0.5

    def test_no_keywords(self, scorer):
        item = CollectedItem(
            source_name="Test",
            source_type="rss",
            external_id="boring",
            title="Meeting Notes from Tuesday",
            url="https://example.com",
            content="We discussed various topics.",
        )
        assert scorer.interest_score(item) == 0.0


class TestFinalScore:
    def test_score_returns_all_fields(self, scorer, sample_item):
        result = scorer.score(sample_item)
        assert "recency_score" in result
        assert "authority_score" in result
        assert "interest_score" in result
        assert "clarity_score" in result
        assert "final_score" in result

    def test_final_score_is_weighted_sum(self, scorer, sample_item):
        result = scorer.score(sample_item)
        expected = (
            0.40 * result["recency_score"]
            + 0.25 * result["interest_score"]
            + 0.20 * result["authority_score"]
            + 0.15 * result["clarity_score"]
        )
        assert abs(result["final_score"] - expected) < 0.01

    def test_scores_bounded(self, scorer, sample_items):
        for item in sample_items:
            result = scorer.score(item)
            for key, val in result.items():
                assert 0.0 <= val <= 1.0, f"{key}={val} out of bounds for {item.title}"
