"""Upload media assets to LinkedIn."""

from __future__ import annotations

import logging
from pathlib import Path

from app.publisher.linkedin_client import LinkedInClient

logger = logging.getLogger(__name__)


class MediaUploader:
    """Handles uploading local image files to LinkedIn and returns image URNs."""

    def __init__(self, client: LinkedInClient) -> None:
        self.client = client

    async def upload_images(self, file_paths: list[str]) -> list[str]:
        """Upload images and return list of LinkedIn image URNs."""
        image_urns: list[str] = []

        for fp in file_paths:
            path = Path(fp)
            if not path.exists():
                logger.warning("Image file not found: %s", fp)
                continue

            try:
                # Step 1: Initialize upload and get upload URL + image URN
                reg = await self.client.initialize_image_upload()
                upload_url = reg["upload_url"]
                image_urn = reg["image_urn"]

                # Step 2: Upload the binary image data
                image_bytes = path.read_bytes()
                success = await self.client.upload_image_binary(upload_url, image_bytes)

                if success:
                    image_urns.append(image_urn)
                    logger.info("Uploaded %s -> %s", path.name, image_urn)
            except Exception:
                logger.exception("Failed to upload image %s", fp)

        logger.info("Uploaded %d/%d images to LinkedIn", len(image_urns), len(file_paths))
        return image_urns
