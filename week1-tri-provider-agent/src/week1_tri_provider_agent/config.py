"""Centralized config for the Week 1 agent."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH, env_file_encoding="utf-8", extra="ignore"
    )

    anthropic_api_key: str = Field(..., min_length=1)


settings = Settings()
