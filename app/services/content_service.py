"""Generate caption and fetch images for a selected candidate."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.content.caption_writer import CaptionWriter
from app.content.carousel_renderer import CarouselRenderer
from app.content.image_fetcher import ImageFetcher
from app.storage.models import Asset, Candidate, DraftPost
from app.storage.repositories.asset_repo import AssetRepo
from app.storage.repositories.post_repo import DraftPostRepo

logger = logging.getLogger(__name__)


class ContentService:
    """Orchestrate caption writing and image fetching for a candidate."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.caption_writer = CaptionWriter()
        self.image_fetcher = ImageFetcher()
        self.carousel_fallback = CarouselRenderer()
        self.draft_repo = DraftPostRepo(session)
        self.asset_repo = AssetRepo(session)

    async def build_draft(self, candidate: Candidate) -> DraftPost:
        """Generate caption + fetch images, persist draft and assets."""
        raw = candidate.raw_item

        # Generate caption
        caption = await self.caption_writer.generate(
            title=raw.title,
            summary=candidate.short_summary or raw.title,
            source=raw.source.name if raw.source else "Unknown",
            topic=candidate.topic,
            url=raw.url,
        )

        # Fetch images from SerpAPI
        image_paths = await self.image_fetcher.fetch_images(
            candidate_id=candidate.id,
            title=raw.title,
            topic=candidate.topic,
        )

        # Fall back to Pillow carousel if no images fetched (no SERPAPI_KEY)
        image_strategy = "serp_images"
        if not image_paths:
            logger.info("No SERP images — falling back to Pillow carousel slides")
            image_paths = self.carousel_fallback.render(
                candidate_id=candidate.id,
                title=raw.title,
                what_changed=caption.explanation,
                why_it_matters=caption.why_it_matters,
                takeaway=caption.takeaway,
                topic=candidate.topic,
            )
            image_strategy = "carousel"

        # Persist draft
        draft = DraftPost(
            candidate_id=candidate.id,
            hook=caption.hook,
            body=caption.explanation,
            cta=caption.cta,
            full_caption=caption.full_caption,
            hashtags=caption.hashtags,
            image_strategy=image_strategy,
            status="draft",
            llm_metadata_json=caption.to_dict(),
        )
        await self.draft_repo.insert(draft)

        # Persist asset records
        for i, path in enumerate(image_paths):
            # Detect type based on strategy
            asset_type = "image" if image_strategy == "serp_images" else "slide"
            mime = "image/png"
            if path.endswith(".jpg") or path.endswith(".jpeg"):
                mime = "image/jpeg"
            elif path.endswith(".webp"):
                mime = "image/webp"

            asset = Asset(
                candidate_id=candidate.id,
                asset_type=asset_type,
                file_path=path,
                mime_type=mime,
                sort_order=i,
            )
            await self.asset_repo.insert(asset)

        await self.session.commit()
        logger.info(
            "Draft %d created for candidate %d with %d %s",
            draft.id, candidate.id, len(image_paths), image_strategy,
        )
        return draft
