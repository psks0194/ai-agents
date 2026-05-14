# Week 0 — Python Sprint

A week of Python fundamentals, building up to the patterns used in real agent code.

## Day index

| Day | Topic | Files |
|-----|-------|-------|
| 1 | Grade calculator — basic syntax, lists, dicts, control flow | `main.py` |
| 2 | Type hints & Pydantic — runtime-validated data at boundaries ([notes](./d2c.md)) | `day2_types.py`, `day2_pydantic.py`, `day2-excercise.py` |
| 3 | `async` / `await` — concurrent I/O with `asyncio` and `httpx` | `day3_sync.py`, `day3_async.py`, `day3_patterns.py`, `day3_gotcha.py`, `day3_projects.py` |
| 4 | Config & packaging — `.env`, `pydantic-settings`, PEP 723 scripts, `src/` layout | `day4_env.py`, `day4_settings.py`, `quick_script.py`, `src/fetcher/` |

---

## Day 1 — Grade calculator (`main.py`)

Grades students by score and prints a sorted class report.

- Assigns a letter grade (A–F) to each student based on their numeric score
- Prints results sorted by score (descending)
- Highlights top performers (A or B grade)
- Reports class average, highest score, and lowest score

| Score | Grade |
|-------|-------|
| 90–100 | A |
| 80–89  | B |
| 70–79  | C |
| 60–69  | D |
| 0–59   | F |

---

## Day 2 — Type hints & Pydantic

See [`d2c.md`](./d2c.md) for the full walkthrough. In short:

- **`day2_types.py`** — built-in type-hint vocabulary (`list[str]`, `dict[str, int]`, `str | None`, …).
- **`day2_pydantic.py`** — `BaseModel` subclasses for runtime validation, coercion, and JSON round-tripping.
- **`day2-excercise.py`** — a mini tool-dispatcher that validates LLM-style JSON tool calls (`web_search`, `calculator`) using `Literal` + `Field` constraints.

---

## Day 3 — `async` / `await`

Concurrency for I/O-bound work. The same three URL fetches done sync vs. async show the payoff immediately.

- **`day3_sync.py`** — fetches three `httpbin.org/delay` URLs sequentially with `httpx.get`. Total time ≈ sum of all delays.
- **`day3_async.py`** — same three URLs via `httpx.AsyncClient` + `asyncio.gather`. Total time ≈ the slowest one.
- **`day3_patterns.py`** — the four patterns you'll reach for constantly:
  1. **Sequential `await`** — each call blocks the next.
  2. **`asyncio.gather`** — fan out, wait for all.
  3. **`asyncio.as_completed`** — process results in finish order.
  4. **`gather(..., return_exceptions=True)`** — keep partial successes when some tasks raise.
- **`day3_gotcha.py`** — the traps:
  - Forgetting `await` (you get a coroutine object, not the result).
  - Calling `time.sleep` inside a coroutine (blocks the whole event loop — use `asyncio.sleep`).
  - Top-level `await` in a `.py` file (only legal inside an `async def`).
  - Calling an async function without an event loop (nothing runs).
- **`day3_projects.py`** — putting it together: fetch 10 posts from JSONPlaceholder concurrently, validate each with a Pydantic `Post` model, separate successes from failures, print a summary. This is the shape of real agent code — concurrent I/O + schema-validated responses.

---

## Day 4 — Config & packaging

Getting secrets out of source code and turning a script into a real installable package.

- **`day4_env.py`** — load API keys and app config from a `.env` file with `python-dotenv` + `os.getenv`. Resolves the `.env` path relative to the repo root so the script works regardless of where it's run from. `.env` is gitignored; the committed `.env.example` at the repo root documents the expected variables.
- **`day4_settings.py`** — same idea, but typed: a `pydantic-settings` `BaseSettings` subclass auto-loads from `.env`, validates required keys, and gives you `settings.openai_api_key` instead of `os.getenv("OPENAI_API_KEY")`. Missing keys fail loudly at startup rather than silently returning `None`.
- **`quick_script.py`** — PEP 723 inline script metadata. The `# /// script` header declares dependencies in the file itself, so `uv run quick_script.py` spins up an isolated venv on the fly. No `pyproject.toml`, no `uv sync` — useful for one-off utilities.
- **`src/fetcher/`** — the Day 3 concurrent fetcher reshaped as a real package using the `src/` layout:
  - `models.py` — the `Post` Pydantic model.
  - `client.py` — `fetch_post` / `fetch_many` (async + `httpx`).
  - `main.py` — CLI entry point exposed as a console script via `[project.scripts]` in `pyproject.toml`.
  - After `uv sync`, run it as `uv run fetcher` from anywhere in the project.

---

## Running

```bash
uv run main.py
uv run day2_types.py
uv run day2_pydantic.py
uv run day2-excercise.py
uv run day3_sync.py
uv run day3_async.py
uv run day3_patterns.py
uv run day3_gotcha.py
uv run day3_projects.py
uv run day4_env.py
uv run day4_settings.py
uv run quick_script.py     # PEP 723 — no install step needed
uv run fetcher             # console script from src/fetcher/
```

## Requirements

- Python 3.13+
- `httpx`, `pydantic`, `pydantic-settings`, `python-dotenv` (installed via `uv sync`)
- Copy `../.env.example` to `../.env` and fill in real API keys before running the Day 4 scripts.
