"""Demonstrate loading environment variables from .env."""

import os
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).parent.parent
ENV_PATH = REPO_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

def main() -> None:
    app_env = os.getenv("APP_ENV", "production")
    log_level = os.getenv("APP_LOG_LEVEL", "warning")
    print(f"APP_ENV = {app_env}")
    print(f"APP_LOG_LEVEL = {log_level}")

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key is None:
        print("OPENAI_API_KEY not set.")
    else:
        print(f"OPENAI_API_KEY = {openai_key[:4]}...{openai_key[-4:]}")

if __name__ == "__main__":
    main()