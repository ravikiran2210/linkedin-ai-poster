"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration – all values come from env vars or .env file."""

    # Database
    database_url: str = "postgresql+asyncpg://poster:poster@localhost:5432/linkedin_ai_poster"

    # Google Gemini
    gemini_api_key: str = ""

    # LinkedIn
    linkedin_access_token: str = ""
    linkedin_person_urn: str = ""

    # Pipeline
    auto_approve: bool = False
    fetch_window_hours: int = 48
    min_score_to_post: float = 0.35

    # Logging
    log_level: str = "INFO"

    # Image fetching (SerpAPI)
    serpapi_key: str = ""
    image_count: int = 3

    # Scheduling
    post_interval_days: int = 3
    daily_run_hour: int = 16
    daily_run_minute: int = 50
    timezone: str = "Asia/Kolkata"

    # Paths
    generated_assets_dir: str = "generated_assets"

    # Daily fetch digest email (Gmail: use an App Password, not your login password)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    digest_to_email: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
