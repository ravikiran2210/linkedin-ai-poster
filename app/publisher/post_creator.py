"""Orchestrate media upload + post creation on LinkedIn."""

from __future__ import annotations

import logging
from typing import Any

from app.publisher.linkedin_client import LinkedInClient
from app.publisher.media_uploader import MediaUploader

logger = logging.getLogger(__name__)


class PostCreator:
    """High-level: upload assets, then create a LinkedIn post."""

    def __init__(self) -> None:
        self.client = LinkedInClient()
        self.uploader = MediaUploader(self.client)

    async def publish(
        self,
        caption: str,
        image_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        """Upload images (if any) and create the post. Returns post metadata."""
        image_urns: list[str] = []

        if image_paths:
            image_urns = await self.uploader.upload_images(image_paths)
            logger.info("Prepared %d image URNs for post", len(image_urns))

        result = await self.client.create_post(
            text=caption,
            image_urns=image_urns or None,
        )
        logger.info("Post published: %s", result.get("url", ""))
        return result
