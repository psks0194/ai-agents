# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Repo-wide conventions live in `../CLAUDE.md`. This file covers what is specific to **week 1**.

## What this is

The **same tool-using agent built three times** — once each on the raw Anthropic, OpenAI, and Gemini SDKs. The point is to feel the agent loop *underneath* every framework: you write the `call → tool_use → tool_result → call → final answer` loop yourself, so when later weeks' frameworks hide it, you know exactly what they're hiding.

Files come in parallel triples — `agent.py` / `openai_agent.py` / `gemini_agent.py`, `chat.py` / `openai_chat.py` / `gemini_chat.py`, etc. — so the three providers can be diffed side by side. Day 5 adds streaming, structured output, and a cross-provider benchmark.

## Commands

From inside `week1-tri-provider-agent/`:

```bash
uv sync
uv run python -m week1_tri_provider_agent.agent              # Anthropic tool agent
uv run python -m week1_tri_provider_agent.openai_agent       # OpenAI tool agent
uv run python -m week1_tri_provider_agent.gemini_agent       # Gemini tool agent
uv run python -m week1_tri_provider_agent.benchmark          # all three on one task — latency, tokens, cost
```

Full module list is in `README.md` under "Run". Needs all three keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`) in the repo-root `.env`.

## Architecture

```
src/week1_tri_provider_agent/
├── config.py     # pydantic-settings — all 3 provider keys
├── tools.py      # provider-agnostic tool IMPLEMENTATIONS (calculator, time, fetch_url)
│
├── *_first_call.py / *_chat.py / *_agent.py   # parallel triples per provider
├── *_tools.py                                 # per-provider schema wrappers around tools.py
│
├── agent_streaming.py     # Anthropic agent with token-by-token streaming
├── structured_output.py   # schema-forced JSON via Pydantic (Anthropic + OpenAI)
└── benchmark.py           # one task, all 3 providers, side-by-side metrics
```

The key shape: **tool *implementations* in `tools.py` are shared across providers; only the schema wrapper (`*_tools.py`) and the loop's API vocabulary differ per SDK.** When extending a tool, write it in `tools.py` and add the schema in all three `*_tools.py` files — that's what keeps the parallel structure honest.

## Gotchas

- **Schema headroom for Anthropic.** Anthropic tool-use treats Pydantic `min_length`/`max_length` on lists as *hints* — the model can overshoot, and validation fails client-side. Keep schema headroom on constrained list fields and state the target count in the prompt. (This also bites in Week 2.)
- **No Gemini key on the benchmark** — `benchmark.py` will skip Gemini cleanly if `GOOGLE_API_KEY` is missing, but warns. Same for the other providers.
