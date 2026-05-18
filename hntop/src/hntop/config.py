"""App configuration loaded from .env."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = REPO_ROOT / ".env"


class AppSettings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    sentry_dsn: str | None = None
    default_count: int = 10
    default_min_score: int = 0
    app_env: str = "development"
