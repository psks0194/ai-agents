# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Repo-wide conventions live in `../CLAUDE.md`. This file covers what is specific to **hntop**.

## What this is

The Week 0 capstone — a small async CLI that fetches Hacker News top stories. The point of the project is *production-shape Python on a tiny task*: typed Pydantic models, `asyncio.gather` for concurrent I/O, `pydantic-settings` for config, `argparse` + `rich` for the CLI, ruff for lint. The implementation is intentionally small; treat the architecture as the lesson.

## Commands

```bash
uv sync                                          # install deps
uv run hntop                                     # console script (default 10 stories)
uv run hntop --count 30 --min-score 50           # flags override .env defaults
uv run pytest test_client.py test_model.py       # the only tests in the umbrella repo
uv run ruff check .                              # lint
```

`hntop` is wired as a console script via `[project.scripts]` in `pyproject.toml`. Flags always win over `.env` values; missing `.env` is fine (defaults apply).

## Architecture

`src/hntop/` is a real `src/`-layout package — four files, each one job:

- `models.py` — `Story` Pydantic model + computed properties.
- `client.py` — `fetch_story` (single) and `fetch_stories` (concurrent via `asyncio.gather` over an `httpx.AsyncClient`). 30 stories in ~1s vs ~10s sequentially is the headline lesson.
- `config.py` — `pydantic-settings` `Settings` with `DEFAULT_COUNT`, `DEFAULT_MIN_SCORE`, etc. Reads the repo-root `.env` (resolve path the same way the rest of the repo does).
- `main.py` — `argparse` CLI + `rich` table rendering. Flag values override `Settings`.

## Tests

The only week with tests. `test_client.py` and `test_model.py` live at the project root (not under `tests/`), so reference them by filename: `uv run pytest test_client.py::test_name`.
