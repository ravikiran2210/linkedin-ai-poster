"""GitHub trending/release collector for AI/ML repos."""

from __future__ import annotations

import logging
from datetime import timezone

import httpx
from dateutil.parser import parse as parse_date
from tenacity import retry, stop_after_attempt, wait_exponential

from app.collectors.base import BaseCollector, CollectedItem

logger = logging.getLogger(__name__)

# High-signal repos to watch for releases
WATCHED_REPOS: list[str] = [
    "openai/openai-python",
    "langchain-ai/langchain",
    "huggingface/transformers",
    "vllm-project/vllm",
    "ggerganov/llama.cpp",
    "microsoft/autogen",
    "anthropics/anthropic-sdk-python",
    "meta-llama/llama",
    "mistralai/mistral-inference",
    "run-llama/llama_index",
    "modelcontextprotocol/servers",
]

GITHUB_API = "https://api.github.com"


class GitHubReleaseCollector(BaseCollector):
    """Fetches latest releases from watched AI/ML GitHub repos."""

    name = "github"
    source_type = "github"

    def __init__(self, repos: list[str] | None = None, token: str | None = None) -> None:
        self.repos = repos or WATCHED_REPOS
        self.token = token
        self._headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _fetch_releases(self, repo: str) -> list[dict]:
        url = f"{GITHUB_API}/repos/{repo}/releases"
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers=self._headers, params={"per_page": 5})
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            return resp.json()

    async def collect(self) -> list[CollectedItem]:
        items: list[CollectedItem] = []

        for repo in self.repos:
            try:
                releases = await self._fetch_releases(repo)
                for rel in releases[:3]:
                    if rel.get("draft"):
                        continue
                    published = None
                    if rel.get("published_at"):
                        try:
                            published = parse_date(rel["published_at"])
                            if published.tzinfo is None:
                                published = published.replace(tzinfo=timezone.utc)
                        except (ValueError, TypeError):
                            pass

                    body = (rel.get("body") or "")[:2000]
                    tag = rel.get("tag_name", "")

                    items.append(
                        CollectedItem(
                            source_name=f"GitHub:{repo}",
                            source_type="github",
                            external_id=f"{repo}:{tag}",
                            title=f"{repo} {tag} – {rel.get('name', tag)}",
                            url=rel.get("html_url", f"https://github.com/{repo}"),
                            author=rel.get("author", {}).get("login"),
                            published_at=published,
                            content=body,
                            metadata={"repo": repo, "tag": tag, "prerelease": rel.get("prerelease", False)},
                        )
                    )
            except Exception:
                logger.exception("GitHub collector failed for %s", repo)

        logger.info("GitHub collector gathered %d items", len(items))
        return items
