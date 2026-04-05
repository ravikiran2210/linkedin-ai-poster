"""Backfill: re-run collectors and store items without triggering the full pipeline."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.logging_config import setup_logging
from app.services.fetch_service import FetchService
from app.storage.db import async_session_factory, close_db, init_db


async def main() -> None:
    setup_logging()
    await init_db()

    async with async_session_factory() as session:
        svc = FetchService(session)
        count = await svc.fetch_and_store()
        print(f"Backfilled {count} new items")

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
