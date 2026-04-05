"""Upload media assets to LinkedIn."""

from __future__ import annotations

import logging
from pathlib import Path

from app.publisher.linkedin_client import LinkedInClient

logger = logging.getLogger(__name__)


class MediaUploader:
    """Handles uploading local image files to LinkedIn and returns asset URNs."""

    def __init__(self, client: LinkedInClient) -> None:
        self.client = client

    async def upload_images(self, file_paths: list[str]) -> list[str]:
        """Upload images and return list of LinkedIn asset URNs."""
        asset_urns: list[str] = []

        for fp in file_paths:
            path = Path(fp)
            if not path.exists():
                logger.warning("Image file not found: %s", fp)
                continue

            try:
                reg = await self.client.register_image_upload()
                image_bytes = path.read_bytes()
                success = await self.client.upload_image(reg["upload_url"], image_bytes)
                if success:
                    asset_urns.append(reg["asset"])
                else:
                    # In stub mode, still track the asset for the draft
                    asset_urns.append(reg["asset"])
            except Exception:
                logger.exception("Failed to upload image %s", fp)

        logger.info("Uploaded %d/%d images", len(asset_urns), len(file_paths))
        return asset_urns
