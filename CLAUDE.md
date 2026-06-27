# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

The **IntellAIgent Agent Builder Curriculum** — self-contained weekly sprints that build the same canonical agent (tool-use loop + structured research-note) across raw SDKs and progressively higher-level frameworks. Each week has its own `pyproject.toml` / `package.json`, lockfile, and venv. There is no monorepo build at the top.

The throughline: **an agent is a loop** (`call → tool → result → call → final answer`). Each framework hides or exposes that loop differently — when working in a week, frame work in terms of where that framework sits on the spectrum.

## Per-week guides

Each week has its own `CLAUDE.md` with commands, layout, and gotchas. Read that file first when working inside a week:

| Folder                         | Stack              | Focus                                     |
| ------------------------------ | ------------------ | ----------------------------------------- |
| `week0-python-sprint/`         | Python / `uv`      | Types, Pydantic, async, config            |
| `hntop/`                       | Python / `uv`      | Week 0 capstone — async HN CLI            |
| `week1-tri-provider-agent/`    | Python / `uv`      | Raw Anthropic + OpenAI + Gemini SDKs      |
| `week2-agent-patterns/`        | Python / `uv`      | Hand-rolled agent patterns + memory + RAG |
| `week3-langgraph-pydantic-ai/` | Python / `uv`      | LangGraph + Pydantic AI                   |
| `week4-openai-mastra/`         | Python / `uv`      | OpenAI Agents SDK (handoffs, guardrails)  |
| `week4-mastra/`                | TypeScript / `npm` | Mastra — see `week4-mastra/AGENTS.md`     |

## Repo-wide things

- **Single `.env` at the repo root** holds `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`. Every Python week's `config.py` uses `pydantic-settings` with `env_file = REPO_ROOT / ".env"`. `week4-mastra/` is the exception — it has its own `.env`. `.env.example` at the repo root is the template.
- **`.chroma/` at the repo root** is the RAG vector store written by `week2-agent-patterns/rag_index.py`, which walks the umbrella repo for `notes.md` files. Gitignored and rebuildable — re-run `rag_index` after notes change.
- **No top-level test runner.** Only `hntop/` has tests.
