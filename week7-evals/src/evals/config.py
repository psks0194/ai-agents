"""Settings for the eval project (judge model + key)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    # Set JUDGE_MODEL in .env to your current Sonnet string. This default is a
    # reasonable Sonnet-tier guess — verify it against your account's models.
    judge_model: str = "claude-sonnet-4-5"


settings = Settings()
