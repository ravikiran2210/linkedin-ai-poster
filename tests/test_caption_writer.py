"""Tests for the caption writer."""

from __future__ import annotations

import pytest

from app.content.caption_writer import CaptionWriter


class TestCaptionWriterFallback:
    """Test the template fallback (no LLM key needed)."""

    @pytest.fixture
    def writer(self):
        w = CaptionWriter()
        w.api_key = ""  # force fallback
        return w

    @pytest.mark.asyncio
    async def test_fallback_returns_all_fields(self, writer):
        result = await writer.generate(
            title="GPT-5 Released",
            summary="OpenAI released GPT-5 with major reasoning improvements.",
            source="OpenAI Blog",
            topic="llm",
            url="https://openai.com/blog/gpt5",
        )
        assert result.hook
        assert result.explanation
        assert result.why_it_matters
        assert result.takeaway
        assert result.cta
        assert result.hashtags
        assert result.full_caption

    @pytest.mark.asyncio
    async def test_fallback_contains_title(self, writer):
        result = await writer.generate(
            title="Llama 4 Open Source Release",
            summary="Meta released Llama 4 as open source.",
            source="Meta AI",
            topic="open_source_models",
            url="https://ai.meta.com/blog/llama4",
        )
        assert "Llama 4" in result.full_caption

    @pytest.mark.asyncio
    async def test_to_dict(self, writer):
        result = await writer.generate(
            title="Test", summary="Test summary", source="Test", topic="llm", url="https://example.com"
        )
        d = result.to_dict()
        assert set(d.keys()) == {"hook", "explanation", "why_it_matters", "takeaway", "cta", "hashtags", "full_caption"}
