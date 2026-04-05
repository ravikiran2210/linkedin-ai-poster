"""Tests for the LinkedIn publisher (stub mode)."""

from __future__ import annotations

import pytest

from app.publisher.linkedin_client import LinkedInClient
from app.publisher.post_creator import PostCreator


class TestLinkedInClient:
    @pytest.fixture
    def client(self):
        c = LinkedInClient()
        c.access_token = ""
        c.person_urn = ""
        return c

    def test_not_configured(self, client):
        assert not client.is_configured

    @pytest.mark.asyncio
    async def test_stub_register_upload(self, client):
        result = await client.register_image_upload()
        assert "asset" in result
        assert "STUB" in result["asset"]

    @pytest.mark.asyncio
    async def test_stub_upload_image(self, client):
        result = await client.upload_image("", b"fake")
        assert result is False

    @pytest.mark.asyncio
    async def test_stub_create_post(self, client):
        result = await client.create_post("Hello LinkedIn!")
        assert "id" in result
        assert "url" in result
        assert "STUB" in result["id"]


class TestPostCreator:
    @pytest.mark.asyncio
    async def test_publish_without_images(self):
        creator = PostCreator()
        creator.client.access_token = ""
        creator.client.person_urn = ""
        result = await creator.publish("Test post content")
        assert "id" in result
