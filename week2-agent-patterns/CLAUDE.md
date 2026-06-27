# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Repo-wide conventions live in `../CLAUDE.md`. This file covers what is specific to **week 2**.

## What this is

The six classic agent design patterns, plus memory management, plus a working RAG pipeline — all **hand-rolled on a thin typed LLM layer (`llm.py`)**. No framework. Each pattern is a single runnable module; the throughline is that most "agents" are a handful of focused LLM calls composed cleanly, not one giant prompt.

This is the substrate every later week's framework hides. When extending, prefer adding a new module over expanding an existing one — each pattern is meant to stand alone and be diffable against the others.

## Commands

From inside `week2-agent-patterns/`:

```bash
uv sync
uv run python -m week2_agent_patterns.chain                  # any pattern module
uv run python -m week2_agent_patterns.chain "your topic"     # most take an optional topic arg

# RAG flow — run in order the first time
uv run python -m week2_agent_patterns.rag_index              # rebuild ../.chroma/ from all notes.md
uv run python -m week2_agent_patterns.rag_retrieve           # eyeball top-K chunks for sample queries
uv run python -m week2_agent_patterns.rag_agent "question?" --n 6
```

Full module list is in `README.md` under "Run". Needs `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` in the repo-root `.env`.

## Architecture

```
src/week2_agent_patterns/
├── llm.py       # the thin layer — schema-forced calls (Anthropic + OpenAI), plus plain text
├── models.py    # Pydantic models shared by chain.py (Angle, Outline, Draft, Critique)
│
├── chain.py / router.py / parallel.py / composed.py / orchestrator.py / evaluator_optimizer.py
│             # The six patterns. composed.py reuses chain.py — patterns compose.
│
├── memory_naive.py / conversation.py / memory_summarized.py / scratchpad.py
│             # Memory: see the naive cost curve, then the Conversation abstraction with summarization,
│             # then sawtooth in action; scratchpad.py is a different kind of memory (structured notes).
│
└── rag_index.py / rag_retrieve.py / rag_agent.py
              # RAG: index → retrieve → grounded answer over the curriculum's notes.md files
```

- **`llm.py` is deliberately NOT a framework** — just the minimal glue so each pattern's code is the pattern. Schema-constrained output via tool use on Anthropic, native structured outputs on OpenAI.
- **`composed.py` calls `chain.py`** — when changing `chain.run()`'s signature, update `composed.py`'s `content_creator` handler too.
- **`conversation.py`'s `Conversation` is shared infrastructure** for `memory_summarized.py`. `memory_naive.py` deliberately does *not* use it — that's the whole pedagogical point (compare the cost curves).

## RAG and the umbrella `.chroma/`

`rag_index.py` walks the **whole umbrella repo** (`../`) for `notes.md` files and writes the index to **`../.chroma/`** (repo root, gitignored). That folder is shared infrastructure — re-run `rag_index` any time a `notes.md` anywhere in the repo changes, or retrieval will return stale chunks.

Both halves of RAG must agree on the embedding model and the store location — `rag_retrieve.py` re-imports `CHROMA_DIR`/`COLLECTION_NAME` from `rag_index.py` to keep them in sync. Don't hardcode either.

## Gotchas

- **Anthropic treats list `min_length`/`max_length` as hints, not limits.** The model can overshoot and validation fails client-side. Constrained list fields (e.g. `Critique.reasons`) keep schema headroom *and* state the target count in the prompt. Repeat this when adding new schemas.
- **Async only in `parallel.py`.** The other patterns are sync. Don't introduce `asyncio` elsewhere without a real reason — it muddies the pattern.
