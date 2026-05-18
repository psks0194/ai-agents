# hntop

A small CLI that fetches and displays the current top stories from Hacker News.

Built as the Week 0 capstone of the IntellAIgent Agent Builder Curriculum — a foundations sprint covering Python, Pydantic, async I/O, and project tooling.

## Why this exists

Most Python-for-AI tutorials skip the parts that make code production-ready: typed data models, concurrent I/O, configuration via environment, proper CLI argument parsing, pretty terminal output. This project uses all of them on a small, useful task.

## Features

- Fetches top stories from the Hacker News API
- Concurrent fetching with `asyncio.gather` — 30 stories in ~1s instead of ~10s
- Type-safe response validation with Pydantic
- Configurable via `.env` or command-line flags
- Pretty terminal output with `rich`

## Quick start

```bash
# Install (uses uv)
uv sync

# Default: top 10 stories
uv run hntop

# Top 20 stories
uv run hntop --count 20

# Only stories with 100+ points
uv run hntop --min-score 100

# Combine
uv run hntop --count 30 --min-score 50
```

## Configuration

Optional environment variables (in `.env` at the repo root):

```
DEFAULT_COUNT=10
DEFAULT_MIN_SCORE=0
APP_ENV=development
SENTRY_DSN=
```

Command-line flags override the defaults.

## Architecture

```
src/hntop/
├── models.py    # Pydantic Story model with computed properties
├── client.py    # Async HTTP fetchers — single + batch
├── config.py    # pydantic-settings config loading
├── main.py      # CLI: argparse + rich rendering
└── __init__.py
```

## Tech

- Python 3.13
- uv for project + dependency management
- httpx for async HTTP
- Pydantic for data validation
- pydantic-settings for config
- rich for terminal output
- ruff for linting/formatting

---

Part of the IntellAIgent Agent Builder Curriculum.
