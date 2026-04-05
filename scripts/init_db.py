"""Initialize database tables."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.storage.db import init_db


async def main():
    await init_db()
    print("DB tables ready")


if __name__ == "__main__":
    asyncio.run(main())
