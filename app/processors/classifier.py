"""Rule-based topic classifier for collected items."""

from __future__ import annotations

import re
from app.collectors.base import CollectedItem
from app.constants import TOPICS

# Pattern → topic mapping (checked in order, first match wins)
_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(agent|agentic|multi.?agent|tool.?use|mcp|function.?call)", re.I), "ai_agents"),
    (re.compile(r"\b(benchmark|eval|leaderboard|mmlu|humaneval|arena)", re.I), "benchmark"),
    (re.compile(r"\b(llm|language.?model|gpt|claude|gemini|llama|mistral|phi|qwen)", re.I), "llm"),
    (re.compile(r"\b(open.?source|weights|apache|mit.?licen|release.*model)", re.I), "open_source_models"),
    (re.compile(r"\b(inference|quantiz|gguf|vllm|trt|onnx|serving|deploy)", re.I), "inference"),
    (re.compile(r"\b(launch|product|api|platform|announce|availab)", re.I), "product_launch"),
    (re.compile(r"\b(tool|framework|library|sdk|cli|plugin|extension)", re.I), "tooling"),
    (re.compile(r"\b(train|research|paper|arxiv|neural|attention|transformer|diffusion)", re.I), "ml_research"),
]


class Classifier:
    """Assigns a topic label to a CollectedItem based on keyword rules."""

    def classify(self, item: CollectedItem) -> str:
        """Return the best-matching topic string."""
        text = f"{item.title} {item.content}".lower()
        for pattern, topic in _RULES:
            if pattern.search(text):
                return topic
        return "ml_research"  # default fallback

    def classify_batch(self, items: list[CollectedItem]) -> dict[str, str]:
        """Return {external_id: topic} for a batch."""
        return {item.external_id: self.classify(item) for item in items}
