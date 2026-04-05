"""Run the pipeline in CI (GitHub Actions) and output results for downstream steps."""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.logging_config import setup_logging
from app.storage.db import async_session_factory, init_db, close_db
from app.storage.repositories.post_repo import DraftPostRepo
from app.storage.repositories.asset_repo import AssetRepo
from app.workflows.daily_pipeline import DailyPipeline


def set_output(name: str, value: str) -> None:
    """Write a key=value pair to GitHub Actions output."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{name}={value}\n")
    # Also print for local runs
    print(f"  output: {name}={value}")


async def main() -> None:
    setup_logging()
    await init_db()

    # Run the pipeline
    pipeline = DailyPipeline()
    result = await pipeline.run()
    print(f"\nPipeline result: {result}")

    set_output("status", result["status"])
    set_output("draft_id", str(result.get("draft_id", "")))

    # If a draft was created, write preview files for the GitHub Issue
    draft_id = result.get("draft_id")
    if draft_id:
        async with async_session_factory() as session:
            draft_repo = DraftPostRepo(session)
            draft = await draft_repo.get_by_id(draft_id)

            asset_repo = AssetRepo(session)
            assets = await asset_repo.get_by_candidate(draft.candidate_id)

            # Write caption for the review issue
            with open("draft_caption.txt", "w", encoding="utf-8") as f:
                f.write(draft.full_caption)

            # Write metadata
            meta = {
                "draft_id": draft.id,
                "candidate_id": draft.candidate_id,
                "hook": draft.hook,
                "topic": draft.candidate.topic if draft.candidate else "unknown",
                "score": draft.candidate.final_score if draft.candidate else 0,
                "hashtags": draft.hashtags,
                "image_strategy": draft.image_strategy,
                "asset_count": len(list(assets)),
            }
            with open("draft_meta.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            print(f"\nDraft #{draft.id} ready for review")
            print(f"  Topic: {meta['topic']} | Score: {meta['score']}")
            print(f"  Images: {meta['asset_count']} ({meta['image_strategy']})")

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
