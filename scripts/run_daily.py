"""Run the daily pipeline manually from the command line."""

import asyncio
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.logging_config import setup_logging
from app.storage.db import close_db, init_db
from app.workflows.daily_pipeline import DailyPipeline


async def main() -> None:
    setup_logging()
    await init_db()

    pipeline = DailyPipeline()
    result = await pipeline.run()
    print(f"\nPipeline result: {result}")

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
