"""FastAPI application with scheduler for the LinkedIn AI poster pipeline."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_review import router as review_router
from app.config import settings
from app.logging_config import setup_logging
from app.storage.db import close_db, init_db
from app.workflows.daily_pipeline import DailyPipeline

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_pipeline_job() -> None:
    """Scheduled pipeline execution."""
    try:
        pipeline = DailyPipeline()
        result = await pipeline.run()
        logger.info("Scheduled pipeline result: %s", result)
    except Exception:
        logger.exception("Scheduled pipeline failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    setup_logging()
    logger.info("Starting LinkedIn AI Poster")

    await init_db()
    logger.info("Database initialized")

    # Schedule job every N days at the configured time
    interval = settings.post_interval_days
    scheduler.add_job(
        _run_pipeline_job,
        "interval",
        days=interval,
        start_date=f"2026-04-05 {settings.daily_run_hour:02d}:{settings.daily_run_minute:02d}:00",
        timezone=settings.timezone,
        id="pipeline_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started – runs every %d days at %02d:%02d %s",
        interval, settings.daily_run_hour, settings.daily_run_minute, settings.timezone,
    )

    yield

    scheduler.shutdown()
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="LinkedIn AI Poster",
    description="Automated AI/ML content pipeline for LinkedIn",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(review_router)
