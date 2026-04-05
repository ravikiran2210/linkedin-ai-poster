"""Shared test fixtures."""

from __future__ import annotations

import datetime as dt

import pytest

from app.collectors.base import CollectedItem


@pytest.fixture
def sample_item() -> CollectedItem:
    return CollectedItem(
        source_name="OpenAI Blog",
        source_type="rss",
        external_id="https://openai.com/blog/gpt5-release",
        title="GPT-5 Released: A New Frontier in Reasoning",
        url="https://openai.com/blog/gpt5-release",
        author="OpenAI",
        published_at=dt.datetime.now(dt.UTC) - dt.timedelta(hours=6),
        content=(
            "OpenAI has released GPT-5, their most capable model yet. "
            "The model shows significant improvements in reasoning, "
            "code generation, and multimodal understanding. "
            "GPT-5 scores 92% on MMLU and achieves new state-of-the-art results."
        ),
        metadata={"tags": ["llm", "gpt", "release"]},
    )


@pytest.fixture
def sample_items() -> list[CollectedItem]:
    now = dt.datetime.now(dt.UTC)
    return [
        CollectedItem(
            source_name="OpenAI Blog",
            source_type="rss",
            external_id="openai-1",
            title="GPT-5 Released: A New Frontier in Reasoning",
            url="https://openai.com/blog/gpt5-release",
            author="OpenAI",
            published_at=now - dt.timedelta(hours=2),
            content="OpenAI released GPT-5 with major reasoning improvements and benchmark results.",
        ),
        CollectedItem(
            source_name="arXiv",
            source_type="arxiv",
            external_id="arxiv-2",
            title="Attention Is Still All You Need: Revisiting Transformers",
            url="https://arxiv.org/abs/2401.99999",
            author="Researcher et al.",
            published_at=now - dt.timedelta(hours=12),
            content="We revisit the transformer architecture and propose improvements.",
        ),
        CollectedItem(
            source_name="GitHub:vllm-project/vllm",
            source_type="github",
            external_id="vllm-v0.5",
            title="vllm v0.5.0 – 2x Faster Inference",
            url="https://github.com/vllm-project/vllm/releases/tag/v0.5.0",
            author="vllm-team",
            published_at=now - dt.timedelta(hours=24),
            content="Major release with 2x inference speedup, new quantization support.",
        ),
        CollectedItem(
            source_name="Hugging Face Blog",
            source_type="rss",
            external_id="hf-1",
            title="Open-Source Llama 4 Now Available on the Hub",
            url="https://huggingface.co/blog/llama4-release",
            author="HF Team",
            published_at=now - dt.timedelta(hours=48),
            content="Meta's Llama 4 is now available as open-source weights on Hugging Face.",
        ),
    ]
