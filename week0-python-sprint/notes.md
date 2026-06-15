# Week 0 — Notes (Python Sprint)

Python fundamentals, built up specifically toward the patterns real agent code uses:
typed boundaries, concurrent I/O, and clean config. See the [README](./README.md) for
the per-day file index and run commands; this file captures the *why* and the lessons.

## The throughline

Every day adds one capability the agent code later depends on:

```
syntax → typed data → concurrency → config/packaging
 (d1)       (d2)          (d3)          (d4)
```

## Day 1 — Syntax & data structures

- Lists, dicts, control flow, sorting with a `key=`, f-strings.
- Mental model: get fluent moving data through plain Python before adding types.

## Day 2 — Type hints & Pydantic

The most important day for everything that follows.

- **Type hints** (`list[str]`, `dict[str, int]`, `str | None`) are documentation +
  tooling — they don't enforce anything at runtime on their own.
- **Pydantic `BaseModel`** is what actually *validates and coerces* at runtime. This is
  the tool for **data at boundaries** — anything coming from an LLM, an API, or a file.
- `Literal` + `Field` constraints let you validate LLM-style JSON tool calls before you
  trust them. This is the seed of every "structured output" / tool-call pattern later.
- Takeaway: **validate at the edges, trust typed objects on the inside.**

## Day 3 — `async` / `await`

Concurrency for **I/O-bound** work (network calls), not CPU work.

- Sync version: total time ≈ **sum** of all delays. Async + `asyncio.gather`: total time
  ≈ the **slowest** single call. That gap is the whole point.
- Four patterns worth memorizing:
  1. **Sequential `await`** — simple, but each call blocks the next.
  2. **`asyncio.gather`** — fan out, wait for all.
  3. **`asyncio.as_completed`** — process results as they finish.
  4. **`gather(..., return_exceptions=True)`** — keep partial successes when some tasks raise.
- Gotchas that bite:
  - Forgetting `await` → you get a coroutine object, not a result.
  - `time.sleep` inside a coroutine **blocks the whole event loop** — use `asyncio.sleep`.
  - Top-level `await` only works inside an `async def`.
  - Calling an async function with no running event loop → nothing happens.
- The shape of real agent code shows up here: **concurrent I/O + schema-validated responses.**

## Day 4 — Config & packaging

Getting secrets out of source and turning scripts into installable code.

- `.env` + `python-dotenv` for secrets; **`.env` is gitignored**, `.env.example` documents
  the expected keys.
- `pydantic-settings` `BaseSettings` is the upgrade: typed config that **fails loudly at
  startup** on a missing key instead of silently returning `None`. Use this over raw
  `os.getenv` everywhere downstream.
- **PEP 723** inline script metadata (`# /// script`) lets `uv run script.py` build an
  isolated venv on the fly — great for one-off utilities, no `pyproject.toml` needed.
- **`src/` layout** + `[project.scripts]` turns a script into a real console command
  (`uv run fetcher`).

## What carries forward

- Pydantic for every LLM/API boundary → Week 1 structured outputs & tool schemas.
- `asyncio.gather` fan-out → Week 2 parallelization pattern.
- `pydantic-settings` config → reused as `config.py` in both Week 1 and Week 2.
