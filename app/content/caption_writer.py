"""Generate LinkedIn captions using Google Gemini or a template fallback."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.content.prompt_templates import LINKEDIN_CAPTION_SYSTEM, LINKEDIN_CAPTION_USER

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


class CaptionResult:
    """Structured caption output."""

    def __init__(
        self,
        hook: str,
        explanation: str,
        why_it_matters: str,
        takeaway: str,
        cta: str,
        hashtags: str,
        full_caption: str,
    ) -> None:
        self.hook = hook
        self.explanation = explanation
        self.why_it_matters = why_it_matters
        self.takeaway = takeaway
        self.cta = cta
        self.hashtags = hashtags
        self.full_caption = full_caption

    def to_dict(self) -> dict[str, str]:
        return {
            "hook": self.hook,
            "explanation": self.explanation,
            "why_it_matters": self.why_it_matters,
            "takeaway": self.takeaway,
            "cta": self.cta,
            "hashtags": self.hashtags,
            "full_caption": self.full_caption,
        }


class CaptionWriter:
    """Generates LinkedIn captions via Gemini 2.5 Flash with template fallback."""

    def __init__(self) -> None:
        self.api_key = settings.gemini_api_key

    async def generate(
        self,
        title: str,
        summary: str,
        source: str,
        topic: str,
        url: str,
    ) -> CaptionResult:
        """Generate a caption. Falls back to template if Gemini is unavailable."""
        if self.api_key:
            try:
                return await self._generate_with_gemini(title, summary, source, topic, url)
            except Exception:
                logger.exception("Gemini caption generation failed, using template fallback")

        return self._template_fallback(title, summary, source, topic, url)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
    async def _generate_with_gemini(
        self, title: str, summary: str, source: str, topic: str, url: str
    ) -> CaptionResult:
        user_prompt = LINKEDIN_CAPTION_USER.format(
            title=title, summary=summary, source=source, topic=topic, url=url
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{LINKEDIN_CAPTION_SYSTEM}\n\n{user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{GEMINI_API_URL}?key={self.api_key}",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # Extract text from Gemini response
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        # Strip markdown code fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        parsed = json.loads(text)

        return CaptionResult(
            hook=parsed.get("hook", ""),
            explanation=parsed.get("explanation", ""),
            why_it_matters=parsed.get("why_it_matters", ""),
            takeaway=parsed.get("takeaway", ""),
            cta=parsed.get("cta", ""),
            hashtags=parsed.get("hashtags", ""),
            full_caption=parsed.get("full_caption", ""),
        )

    def _template_fallback(
        self, title: str, summary: str, source: str, topic: str, url: str
    ) -> CaptionResult:
        """Structured template fallback when no LLM key is available."""
        topic_label = topic.replace("_", " ").title()

        # Topic-specific hooks with emojis and high energy
        hooks = {
            "llm": f"🚨 New LLM drop just landed — and this one is genuinely worth paying attention to.",
            "ai_agents": f"🤖 AI agents just got significantly more capable. Here is what you need to know.",
            "ml_research": f"🔬 Fresh from the research lab — a paper that could fundamentally shift how we build.",
            "inference": f"⚡ Faster inference isn't just nice-to-have anymore. It is absolute table stakes.",
            "open_source_models": f"🌍 Open source AI continues to relentlessly close the gap with closed models.",
            "tooling": f"🛠️ New developer tooling alert — this could easily save you hours per week.",
            "benchmark": f"📊 New benchmark results are in, and the leaderboard just changed.",
            "product_launch": f"🚀 Major product launch in the AI space! Here is the real story beneath the hype.",
        }
        hook = hooks.get(topic, f"🔥 Something massive just dropped in {topic_label}.")

        explanation = (
            f"📌 {title.upper()}\n\n"
            f"Here is the core breakdown from {source}:\n"
            f"🔹 {summary}"
        )

        why_templates = {
            "llm": "💡 Why it matters:\nIf you are building on top of language models, this directly affects your stack. Better models mean better products — but also new architectural trade-offs to evaluate.",
            "ai_agents": "💡 Why it matters:\nFor teams building agentic workflows, this transforms what is possible out of the box. Less glue code, more reliable and scalable execution.",
            "ml_research": "💡 Why it matters:\nThis is not just academic — the techniques here could show up in production models within months. It is highly worth understanding right now.",
            "inference": "💡 Why it matters:\nFor anyone serving models in production, this translates directly to significantly lower costs and snap-fast responses for your end-users.",
            "open_source_models": "💡 Why it matters:\nMore open weights means more options for fine-tuning, self-hosting, and building custom solutions completely free from vendor lock-in.",
            "tooling": "💡 Why it matters:\nDeveloper experience is paramount. Better tools mean dramatically faster iteration cycles and far fewer hours debugging infrastructure.",
            "benchmark": "💡 Why it matters:\nBenchmarks aren't everything, but they provide a highly useful signal for where the entire field is heading and which models you must evaluate next.",
            "product_launch": "💡 Why it matters:\nNew products reshape the competitive landscape. This one is incredibly worth evaluating if you are making strict build-vs-buy decisions.",
        }
        why = why_templates.get(topic, "💡 Why it matters:\nThis matters for anyone building with AI. The ecosystem is moving at breakneck speed, and staying current is your absolute best competitive advantage.")

        takeaway = f"🎯 The Takeaway:\nI'd keep a very close eye on this. The teams that move fast on updates like this are the ones shipping industry-leading products."

        cta_templates = {
            "llm": "👇 Have you tried it yet? What is your go-to model for production right now?",
            "ai_agents": "👇 Are you building with AI agents yet, or still waiting for the tooling to fully mature?",
            "ml_research": "👇 Which recent research paper has had the biggest impact on your actual day-to-day work?",
            "inference": "👇 What is your current inference setup? Still using the identical stack from 6 months ago?",
            "open_source_models": "👇 Open source or closed API — which paradigm are you strongly betting on for your next major project?",
            "tooling": "👇 What is the one single AI dev tool you couldn't possibly work without right now?",
            "benchmark": "👇 Do you actually use public benchmark scores to pick models, or do you run entirely custom internal evals?",
            "product_launch": "👇 First impressions — does this solve a very real problem you have, or is it merely a solution looking for one?",
        }
        cta = cta_templates.get(topic, "👇 What is your take on this? Would love to hear from other builders in the comments below.")

        hashtags = f"#AI #{topic_label.replace(' ', '')} #MachineLearning #Tech #BuildWithAI"

        full_caption = f"{hook}\n\n{explanation}\n\n{why}\n\n{takeaway}\n\n{cta}\n\n🔗 Read more: {url}\n\n{hashtags}"

        return CaptionResult(
            hook=hook,
            explanation=explanation,
            why_it_matters=why,
            takeaway=takeaway,
            cta=cta,
            hashtags=hashtags,
            full_caption=full_caption,
        )
