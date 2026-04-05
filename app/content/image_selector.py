"""Select relevant images for a post."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ImageSelector:
    """Select images from item metadata or external sources."""

    def select_images(self, title: str, topic: str, metadata: dict) -> list[str]:
        """Return a list of image URLs relevant to the topic.

        For MVP, returns empty list — carousel_renderer generates branded slides instead.
        Future: integrate with Unsplash API or item-embedded images.
        """
        urls: list[str] = []

        # Check if the item metadata has images
        if "image_url" in metadata:
            urls.append(metadata["image_url"])
        if "thumbnail" in metadata:
            urls.append(metadata["thumbnail"])

        logger.info("ImageSelector found %d pre-existing images for '%s'", len(urls), title[:50])
        return urls[:4]
