"""Project-wide constants."""

from __future__ import annotations

# ── Topic taxonomy ──────────────────────────────────────────────────
TOPICS: list[str] = [
    "llm",
    "ai_agents",
    "ml_research",
    "inference",
    "open_source_models",
    "tooling",
    "benchmark",
    "product_launch",
]

# ── Scoring weights ─────────────────────────────────────────────────
WEIGHT_RECENCY: float = 0.40
WEIGHT_INTEREST: float = 0.25
WEIGHT_AUTHORITY: float = 0.20
WEIGHT_CLARITY: float = 0.15

# ── Authority sources (canonical domains / org names) ───────────────
HIGH_AUTHORITY_SOURCES: set[str] = {
    "openai",
    "anthropic",
    "google",
    "deepmind",
    "meta",
    "huggingface",
    "hugging face",
    "arxiv",
    "github",
    "microsoft",
    "nvidia",
    "mistral",
    "cohere",
    "stability",
    "together",
}

# ── Interest keywords ──────────────────────────────────────────────
HIGH_INTEREST_KEYWORDS: set[str] = {
    "launch",
    "release",
    "benchmark",
    "open-source",
    "open source",
    "state-of-the-art",
    "sota",
    "breakthrough",
    "gpt",
    "claude",
    "gemini",
    "llama",
    "mistral",
    "agent",
    "agentic",
    "rag",
    "fine-tune",
    "fine-tuning",
    "multimodal",
    "reasoning",
    "inference",
    "context window",
    "mcp",
    "tool use",
}

# ── Guard-rails ─────────────────────────────────────────────────────
MAX_CONSECUTIVE_SAME_TOPIC: int = 2
MAX_CONSECUTIVE_SAME_SOURCE: int = 2

# ── Caption constraints ────────────────────────────────────────────
CAPTION_MIN_WORDS: int = 120
CAPTION_MAX_WORDS: int = 220

# ── Carousel slides ────────────────────────────────────────────────
CAROUSEL_SLIDE_COUNT: int = 4
SLIDE_WIDTH: int = 1080
SLIDE_HEIGHT: int = 1080
