"""Seed the sources table with default RSS feeds, arXiv queries, and GitHub repos."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.logging_config import setup_logging
from app.storage.db import async_session_factory, close_db, init_db
from app.storage.models import Source

SEED_SOURCES = [
    {"name": "OpenAI Blog", "type": "rss", "base_url": "https://openai.com/blog/rss.xml"},
    {"name": "Anthropic Research", "type": "rss", "base_url": "https://www.anthropic.com/research/rss.xml"},
    {"name": "Google AI Blog", "type": "rss", "base_url": "https://blog.google/technology/ai/rss/"},
    {"name": "Hugging Face Blog", "type": "rss", "base_url": "https://huggingface.co/blog/feed.xml"},
    {"name": "MIT Tech Review AI", "type": "rss", "base_url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "arXiv CS.CL", "type": "arxiv", "base_url": "http://export.arxiv.org/api/query?search_query=cat:cs.CL"},
    {"name": "arXiv CS.AI", "type": "arxiv", "base_url": "http://export.arxiv.org/api/query?search_query=cat:cs.AI"},
    {"name": "arXiv CS.LG", "type": "arxiv", "base_url": "http://export.arxiv.org/api/query?search_query=cat:cs.LG"},
    {"name": "GitHub:langchain-ai/langchain", "type": "github", "base_url": "https://github.com/langchain-ai/langchain"},
    {"name": "GitHub:huggingface/transformers", "type": "github", "base_url": "https://github.com/huggingface/transformers"},
    {"name": "GitHub:vllm-project/vllm", "type": "github", "base_url": "https://github.com/vllm-project/vllm"},
    {"name": "GitHub:ggerganov/llama.cpp", "type": "github", "base_url": "https://github.com/ggerganov/llama.cpp"},
    {"name": "Meta AI Blog", "type": "blog", "base_url": "https://ai.meta.com/blog/"},
    {"name": "NVIDIA AI Blog", "type": "blog", "base_url": "https://blogs.nvidia.com/blog/category/deep-learning/"},
]


async def main() -> None:
    setup_logging()
    await init_db()

    async with async_session_factory() as session:
        for src_data in SEED_SOURCES:
            from sqlalchemy import select

            stmt = select(Source).where(Source.name == src_data["name"]).limit(1)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                print(f"  [skip] {src_data['name']} already exists")
                continue

            source = Source(**src_data, is_active=True)
            session.add(source)
            print(f"  [add]  {src_data['name']}")

        await session.commit()

    print(f"\nSeeded {len(SEED_SOURCES)} sources")
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
