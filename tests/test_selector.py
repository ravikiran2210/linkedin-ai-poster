"""Tests for the candidate selector."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.processors.selector import Selector


def _make_candidate(id: int, topic: str, score: float, source_name: str = "TestSource"):
    """Create a mock Candidate."""
    cand = MagicMock()
    cand.id = id
    cand.topic = topic
    cand.final_score = score
    cand.raw_item = MagicMock()
    cand.raw_item.source = MagicMock()
    cand.raw_item.source.name = source_name
    return cand


class TestSelector:
    @pytest.fixture
    def selector(self):
        return Selector()

    def test_selects_highest_score(self, selector):
        candidates = [
            _make_candidate(1, "llm", 0.9),
            _make_candidate(2, "tooling", 0.7),
            _make_candidate(3, "ai_agents", 0.5),
        ]
        result = selector.select(candidates, [], [])
        assert result.id == 1

    def test_respects_min_score(self, selector):
        candidates = [_make_candidate(1, "llm", 0.2)]
        result = selector.select(candidates, [], [], min_score=0.5)
        assert result is None

    def test_skips_repeated_topic(self, selector):
        candidates = [
            _make_candidate(1, "llm", 0.9),
            _make_candidate(2, "tooling", 0.7),
        ]
        # Topic "llm" was selected 2 days in a row already
        recent_topics = ["llm", "llm"]
        result = selector.select(candidates, recent_topics, [])
        assert result.id == 2  # falls through to tooling

    def test_skips_repeated_source(self, selector):
        candidates = [
            _make_candidate(1, "llm", 0.9, source_name="OpenAI Blog"),
            _make_candidate(2, "ai_agents", 0.7, source_name="arXiv"),
        ]
        recent_sources = ["OpenAI Blog", "OpenAI Blog"]
        result = selector.select(candidates, [], recent_sources)
        assert result.id == 2

    def test_returns_none_when_all_filtered(self, selector):
        candidates = [_make_candidate(1, "llm", 0.9)]
        recent_topics = ["llm", "llm"]
        result = selector.select(candidates, recent_topics, [])
        assert result is None

    def test_empty_candidates(self, selector):
        result = selector.select([], [], [])
        assert result is None
