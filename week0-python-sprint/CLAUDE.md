# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Repo-wide conventions live in `../CLAUDE.md` (the curriculum umbrella). This file covers only what is specific to **week 0**, and where week 0 *departs* from the umbrella's conventions.

## What this week is

Week 0 is a **Python fundamentals sprint** — standalone teaching exercises (one or more files per day) building toward the patterns real agent code uses: type hints + Pydantic at boundaries, `async`/`await` for concurrent I/O, and config/packaging. It is not a single application; most files are independent demos meant to be read and run on their own. `README.md` has the day-by-day index; `d2c.md` is the long-form Day 2 walkthrough.

The progression to keep in mind when explaining or extending: **loose scripts → a real package**. Days 1–4 are top-level scripts (`main.py`, `day2_*.py`, `day3_*.py`, `day4_*.py`); the culmination is `src/fetcher/`, the Day 3 concurrent fetcher reshaped into a proper `src/`-layout package with a console-script entry point.

## Running — note the deviation from the umbrella convention

The root CLAUDE.md says to run modules as `uv run python -m <pkg>.<module>`. **Week 0 does not follow that** — the day files are loose top-level scripts, not a package, so run them directly:

```bash
uv sync                 # install deps (once)
uv run main.py          # Day 1
uv run day2_types.py    # any day file, by filename
uv run day3_async.py
uv run quick_script.py  # PEP 723 inline-metadata script — self-contained venv, no sync needed
uv run fetcher          # the ONLY packaged entry point (src/fetcher/, via [project.scripts])
```

There are no tests in this week. Lint with `uv run ruff check .` (ruff is the only dev dependency).

## Architecture notes that span files

- **Only `src/fetcher/` is a real package.** `pyproject.toml` registers it via `[tool.hatch.build.targets.wheel]` (`packages = ["src/fetcher"]`) and exposes `fetcher = "fetcher.main:main"` as a console script. The top-level `day*.py` files are deliberately *not* packaged — adding a new day means adding a script, not wiring up `pyproject.toml`. `fetcher` splits the Day 3 demo into `models.py` (Pydantic `Post`) / `client.py` (`fetch_post`, `fetch_many` over `httpx.AsyncClient`) / `main.py` (CLI), which is the shape later weeks' agents take.
- **Config resolves to the repo-root `.env`, not a local one.** Both `day4_env.py` and `day4_settings.py` compute `Path(__file__).parent.parent / ".env"` so they read the umbrella's shared `.env` (template at `../.env.example`) regardless of CWD. `day4_env.py` shows the raw `python-dotenv` + `os.getenv` approach; `day4_settings.py` shows the typed `pydantic-settings` `BaseSettings` approach that every later week standardizes on. When touching config here, keep the `.parent.parent` repo-root resolution.
- **`notes.md` is part of the cross-week RAG corpus.** Per the umbrella CLAUDE.md, `week2-agent-patterns/rag_index.py` walks the whole repo for `notes.md` files. Editing this week's `notes.md` means the `.chroma/` index is stale until `rag_index` is re-run.

## Python version

Pinned to 3.13 (`.python-version`, `requires-python = ">=3.13"`). Code uses modern built-in generics (`list[str]`, `str | None`) — match that style; don't reach for `typing.List` / `Optional`.
