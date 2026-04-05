"""LinkedIn API client using the Community Management / Posts API."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

LINKEDIN_API_BASE = "https://api.linkedin.com"
LINKEDIN_VERSION = os.getenv("LINKEDIN_VERSION", "202601")


class LinkedInClient:
    """Abstraction over the LinkedIn REST API for image uploads and post creation.

    Uses:
    - POST /rest/images?action=initializeUpload  (upload images)
    - POST /rest/posts  (create posts with images)
    """

    def __init__(self) -> None:
        self.access_token = settings.linkedin_access_token
        self.person_urn = settings.linkedin_person_urn

    def _rest_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Linkedin-Version": LINKEDIN_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
        }

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.person_urn)

    # ── Image Upload ────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def initialize_image_upload(self) -> dict[str, str]:
        """Initialize an image upload. Returns upload_url and image URN.

        LinkedIn API: POST /rest/images?action=initializeUpload
        """
        if not self.is_configured:
            logger.warning("LinkedIn not configured – returning stub")
            return {"upload_url": "", "image_urn": "urn:li:image:STUB"}

        payload = {
            "initializeUploadRequest": {
                "owner": self.person_urn,
            }
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{LINKEDIN_API_BASE}/rest/images?action=initializeUpload",
                headers=self._rest_headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        value = data["value"]
        upload_url = value["uploadUrl"]
        image_urn = value["image"]

        logger.info("Initialized image upload: %s", image_urn)
        return {"upload_url": upload_url, "image_urn": image_urn}

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def upload_image_binary(self, upload_url: str, image_bytes: bytes) -> bool:
        """Upload binary image data to LinkedIn's upload URL."""
        if not upload_url:
            logger.warning("No upload URL – skipping (stub mode)")
            return False

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.put(upload_url, headers=headers, content=image_bytes)
            resp.raise_for_status()

        logger.info("Image binary uploaded successfully")
        return True

    # ── Post Creation ───────────────────────────────────────────────

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def create_post(
        self,
        text: str,
        image_urns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a LinkedIn post with optional images.

        LinkedIn API: POST /rest/posts
        """
        if not self.is_configured:
            logger.warning("LinkedIn not configured – returning stub post")
            return {
                "id": "urn:li:share:STUB_POST_ID",
                "url": "https://www.linkedin.com/feed/update/urn:li:share:STUB_POST_ID",
            }

        payload: dict[str, Any] = {
            "author": self.person_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
        }

        # Attach images if provided
        if image_urns and len(image_urns) == 1:
            payload["content"] = {
                "media": {
                    "id": image_urns[0],
                }
            }
        elif image_urns and len(image_urns) > 1:
            # Multi-image post
            payload["content"] = {
                "multiImage": {
                    "images": [{"id": urn} for urn in image_urns],
                }
            }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{LINKEDIN_API_BASE}/rest/posts",
                headers=self._rest_headers(),
                json=payload,
            )
            resp.raise_for_status()

        # The Posts API returns the post ID in the x-restli-id header
        post_id = resp.headers.get("x-restli-id", "")
        post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else ""

        logger.info("LinkedIn post created: %s", post_url)
        return {"id": post_id, "url": post_url}
