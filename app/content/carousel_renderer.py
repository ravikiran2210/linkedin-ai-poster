"""Render branded carousel slides using Pillow."""

from __future__ import annotations

import logging
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.constants import CAROUSEL_SLIDE_COUNT, SLIDE_HEIGHT, SLIDE_WIDTH

logger = logging.getLogger(__name__)

# Color palette
BG_COLORS = ["#1a1a2e", "#16213e", "#0f3460", "#1a1a2e"]
ACCENT = "#00d4ff"
TEXT_WHITE = "#ffffff"
TEXT_GRAY = "#b0b0b0"


class CarouselRenderer:
    """Generates 4-slide branded carousel images with Pillow."""

    def __init__(self) -> None:
        self.output_dir = Path(settings.generated_assets_dir) / "slides"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(
        self,
        candidate_id: int,
        title: str,
        what_changed: str,
        why_it_matters: str,
        takeaway: str,
        topic: str,
    ) -> list[str]:
        """Render 4 carousel slides and return list of file paths."""
        slides_data = [
            {"type": "cover", "text": title, "subtitle": f"#{topic.replace('_', ' ').title()}"},
            {"type": "content", "heading": "What Changed", "text": what_changed},
            {"type": "content", "heading": "Why It Matters", "text": why_it_matters},
            {"type": "cta", "heading": "Key Takeaway", "text": takeaway},
        ]

        paths: list[str] = []
        for i, slide in enumerate(slides_data):
            path = self.output_dir / f"candidate_{candidate_id}_slide_{i + 1}.png"
            img = self._render_slide(slide, BG_COLORS[i % len(BG_COLORS)], i + 1)
            img.save(str(path), "PNG")
            paths.append(str(path))
            logger.info("Rendered slide %d -> %s", i + 1, path)

        return paths

    def _render_slide(self, data: dict, bg_color: str, slide_num: int) -> Image.Image:
        img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT), bg_color)
        draw = ImageDraw.Draw(img)

        # Use default font (no external font files required)
        try:
            font_large = ImageFont.truetype("arial.ttf", 48)
            font_medium = ImageFont.truetype("arial.ttf", 32)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except OSError:
            font_large = ImageFont.load_default()
            font_medium = font_large
            font_small = font_large

        # Accent bar at top
        draw.rectangle([(0, 0), (SLIDE_WIDTH, 8)], fill=ACCENT)

        slide_type = data.get("type", "content")

        if slide_type == "cover":
            # Cover slide
            wrapped = textwrap.fill(data["text"], width=28)
            draw.multiline_text(
                (80, SLIDE_HEIGHT // 3),
                wrapped,
                fill=TEXT_WHITE,
                font=font_large,
                spacing=16,
            )
            draw.text(
                (80, SLIDE_HEIGHT - 200),
                data.get("subtitle", ""),
                fill=ACCENT,
                font=font_medium,
            )

        elif slide_type == "cta":
            # Takeaway/CTA slide
            draw.text((80, 100), data.get("heading", ""), fill=ACCENT, font=font_medium)
            wrapped = textwrap.fill(data["text"], width=35)
            draw.multiline_text((80, 220), wrapped, fill=TEXT_WHITE, font=font_medium, spacing=14)
            draw.text(
                (80, SLIDE_HEIGHT - 150),
                "Follow for daily AI updates",
                fill=TEXT_GRAY,
                font=font_small,
            )

        else:
            # Content slide
            draw.text((80, 100), data.get("heading", ""), fill=ACCENT, font=font_medium)
            wrapped = textwrap.fill(data["text"], width=38)
            draw.multiline_text((80, 220), wrapped, fill=TEXT_WHITE, font=font_small, spacing=12)

        # Slide number
        draw.text(
            (SLIDE_WIDTH - 80, SLIDE_HEIGHT - 60),
            f"{slide_num}/{CAROUSEL_SLIDE_COUNT}",
            fill=TEXT_GRAY,
            font=font_small,
        )

        return img
