"""LinkedIn API client abstraction using official REST API patterns."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"


class LinkedInClient:
    """Abstraction over the LinkedIn Marketing/Community Management API.

    Uses the official REST API for:
    - Uploading images (registerUpload + binary upload)
    - Creating posts (ugcPosts or posts API)

    All methods are clean stubs when credentials are missing.
    """

    def __init__(self) -> None:
        self.access_token = settings.linkedin_access_token
        self.person_urn = settings.linkedin_person_urn
        self._headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202401",
        }

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.person_urn)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def register_image_upload(self) -> dict[str, Any]:
        """Register an image upload and get the upload URL + asset URN.

        LinkedIn API: POST /assets?action=registerUpload
        """
        if not self.is_configured:
            logger.warning("LinkedIn not configured – returning stub upload registration")
            return {"upload_url": "", "asset": "urn:li:digitalmediaAsset:STUB"}

        payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": self.person_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{LINKEDIN_API_BASE}/assets?action=registerUpload",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        value = data["value"]
        upload_url = value["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset = value["asset"]

        logger.info("Registered image upload: asset=%s", asset)
        return {"upload_url": upload_url, "asset": asset}

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def upload_image(self, upload_url: str, image_bytes: bytes) -> bool:
        """Upload binary image data to LinkedIn's upload URL."""
        if not upload_url:
            logger.warning("No upload URL – skipping image upload (stub mode)")
            return False

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.put(upload_url, headers=headers, content=image_bytes)
            resp.raise_for_status()

        logger.info("Image uploaded successfully")
        return True

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def create_post(
        self,
        text: str,
        media_assets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a LinkedIn post with optional image attachments.

        LinkedIn API: POST /ugcPosts
        """
        if not self.is_configured:
            logger.warning("LinkedIn not configured – returning stub post response")
            return {
                "id": "urn:li:share:STUB_POST_ID",
                "url": "https://www.linkedin.com/feed/update/urn:li:share:STUB_POST_ID",
            }

        media = []
        for asset_urn in (media_assets or []):
            media.append(
                {
                    "status": "READY",
                    "description": {"text": "AI/ML Update"},
                    "media": asset_urn,
                    "title": {"text": "Carousel Slide"},
                }
            )

        share_content: dict[str, Any] = {"shareCommentary": {"text": text}}
        if media:
            share_content["shareMediaCategory"] = "IMAGE"
            share_content["media"] = media
        else:
            share_content["shareMediaCategory"] = "NONE"

        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{LINKEDIN_API_BASE}/ugcPosts",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        post_id = data.get("id", "")
        post_url = f"https://www.linkedin.com/feed/update/{post_id}"
        logger.info("LinkedIn post created: %s", post_url)
        return {"id": post_id, "url": post_url}
