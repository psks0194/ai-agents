"""Better env loading: Pydantic-Settings with type-safe config."""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    app_env: str = "production"
    log_level: str = "info"
    openai_api_key: str = Field(..., min_length=0)
    anthropic_api_key: str = Field(..., min_length=0)
    google_api_key: str = Field(..., min_length=0)

    model_config = {
        "env_file": Path(__file__).parent.parent / ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

def main() -> None:
    settings = Settings()
    print(f"APP_ENV = {settings.app_env}")
    print(f"LOG_LEVEL = {settings.log_level}")
    print(f"OPENAI_API_KEY = {settings.openai_api_key[:4]}...{settings.openai_api_key[-4:]}")


if __name__ == "__main__":
    main()
