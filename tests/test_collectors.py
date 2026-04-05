"""Tests for collectors."""

from __future__ import annotations

import pytest

from app.collectors.base import CollectedItem
from app.collectors.rss_collector import RSSCollector


class TestCollectedItem:
    def test_schema_creation(self):
        item = CollectedItem(
            source_name="Test",
            source_type="rss",
            external_id="test-1",
            title="Test Title",
            url="https://example.com",
        )
        assert item.source_name == "Test"
        assert item.metadata == {}
        assert item.author is None

    def test_schema_with_all_fields(self, sample_item):
        assert sample_item.source_name == "OpenAI Blog"
        assert "GPT-5" in sample_item.title
        assert sample_item.published_at is not None


class TestRSSCollector:
    def test_default_feeds_loaded(self):
        collector = RSSCollector()
        assert len(collector.feeds) > 0
        assert collector.name == "rss"
        assert collector.source_type == "rss"

    def test_custom_feeds(self):
        feeds = [{"name": "Custom", "url": "https://example.com/rss"}]
        collector = RSSCollector(feeds=feeds)
        assert len(collector.feeds) == 1
        assert collector.feeds[0]["name"] == "Custom"
