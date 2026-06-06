"""Centralized config for Week 2 — patterns work."""

from pydantic import Field
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Runtime config for Week 2."""

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(..., min_length=1)
    openai_api_key: str = Field(..., min_length=1)


settings = Settings()
