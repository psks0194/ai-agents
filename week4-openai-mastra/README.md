# week4-openai-mastra

The agent patterns again — a **third** framework: the **OpenAI Agents SDK**. Same
canonical tasks as Weeks 1–3 (typed output, tool-use loop, a research-note agent),
so the framework is the only variable. The week ends with a three-way bake-off
across Pydantic AI, LangGraph, and the OpenAI Agents SDK on one identical task.

The throughline from the whole curriculum: an agent is a loop (`call → tool →
result → call → final answer`). Each framework just hides or exposes that loop
differently. The OpenAI SDK's stance: **you declare an `Agent`, a `Runner` runs
the loop.**

## Status (Day 1 — 2026-06-22)

- ✅ Config — `pydantic-settings`, OpenAI key from the repo-root `.env` (`config.py`)
- ✅ First agent — typed output, no tools (`first_agent.py`)
- ✅ Tool agent — `@function_tool` functions, `Runner` drives the loop (`tool_agent.py`)
- ✅ Research note — the Week 3 task, OpenAI Agents SDK version (`research_note_oai.py`)
- ✅ Three-way comparison — Pydantic AI vs LangGraph vs OpenAI SDK on one task (`compare_three.py`)

## Core concepts

The OpenAI Agents SDK has a small surface:

1. **`Agent`** — declares `name`, `instructions`, optional `output_type` (a Pydantic
   model for typed results), and `tools`. No model loop logic lives here.
2. **`Runner`** — runs the agent. `Runner.run_sync(agent, prompt)` executes the
   whole tool loop and returns a result; `result.final_output` is the answer
   (typed, if `output_type` was set).
3. **`@function_tool`** — decorates a plain function into a tool. The docstring +
   type hints become the schema the model sees. No `ctx`/deps parameter required
   (unlike Pydantic AI's `RunContext`).
4. **Global key** — `set_default_openai_key(...)`. The SDK reads the key globally,
   *not* per-agent (there's no `api_key=` on `Agent`).

Mental model: **`Agent` = the declaration, `Runner` = the engine.** You never
write the loop.

## The files

### 1. First agent — `first_agent.py`

The smallest agent: `instructions` + `output_type=BookRecommendation`, no tools.
`Runner.run_sync(...)` returns a result whose `final_output` is the validated
Pydantic object. Direct counterpart to Week 3's `pai_first_agent.py` and
`first_graph.py`.

### 2. Tool agent — `tool_agent.py`

The canonical tool-use loop (calculator, time, fetch_url) for the third time:

- Week 1: raw Anthropic SDK — *you* write the ~80-line loop.
- Week 3: Pydantic AI — `@agent.tool`, loop hidden.
- **Week 4: OpenAI SDK — `@function_tool`, `Runner` manages the loop.**

Tools are passed to the agent via `tools=[…]`; `Runner.run_sync` runs call → tool
→ result → repeat. Token usage comes from `result.context_wrapper.usage`.

### 3. Research note — `research_note_oai.py`

The same structured-research-note task from Week 3 Day 4 (`fetch_url` +
`get_current_date`, typed `ResearchNote` output), now in the OpenAI SDK. Exposes
the same `run()` / `display()` interface as the Week 3 versions so the comparison
runner can call all three identically.

### 4. Three-way comparison — `compare_three.py`

Extends Week 3's two-way bake-off to three frameworks. Runs the identical
MCP-adoption topic through Pydantic AI, LangGraph, and the OpenAI SDK, then prints
a table of wall time, tokens, per-provider cost, and lines of code.

> **Cross-project import:** this script reaches into Week 3's source via a
> `sys.path` hack (lines 14–18). That makes Week 3's *code* importable but not its
> *dependencies* — so Week 4's environment must also have `pydantic-ai`,
> `langgraph`, and `langchain-anthropic` installed (already added to
> `pyproject.toml`). In real code this would be a uv workspace, not a path hack.
>
> **Cost note:** the Pydantic AI and LangGraph versions call **Claude** (Anthropic
> billing); the OpenAI version calls **OpenAI** (separate billing). A low balance
> on either provider fails only that provider's runs, not the others.

## Run

```bash
# First agent — typed output, no tools
uv run python -m week4_openai_mastra.first_agent

# Tool agent — calculator / time / fetch_url, Runner drives the loop
uv run python -m week4_openai_mastra.tool_agent

# Research note — OpenAI Agents SDK version
uv run python -m week4_openai_mastra.research_note_oai

# Three-way comparison — Pydantic AI vs LangGraph vs OpenAI SDK on one topic
uv run python -m week4_openai_mastra.compare_three
```

> If another venv is active (e.g. `hntop`), `uv run` warns and ignores it,
> defaulting to this project's `.venv`. `deactivate` to silence it, or `--active`.

## Architecture

```
src/week4_openai_mastra/
├── config.py             # pydantic-settings — OpenAI key from the repo-root .env
│
├── first_agent.py        # Smallest agent: typed output, no tools
├── tool_agent.py         # @function_tool tools; Runner runs the loop
├── research_note_oai.py  # The Week 3 research-note task, OpenAI SDK version
└── compare_three.py      # Pydantic AI vs LangGraph vs OpenAI SDK — one task, head-to-head
```

### A note on the API key

The OpenAI Agents SDK defaults to reading `OPENAI_API_KEY` from the
**environment**. The key here lives in the repo-root `.env`, which
`pydantic-settings` loads into a `settings` object — *not* the OS environment. So
each module calls `set_default_openai_key(settings.openai_api_key)` once at import.
This is the third per-framework key mechanism in the curriculum:

| Framework | How the key goes in |
|---|---|
| LangGraph / LangChain | `ChatAnthropic(..., api_key=settings.anthropic_api_key)` |
| Pydantic AI | `AnthropicModel(..., provider=AnthropicProvider(api_key=...))` |
| OpenAI Agents SDK | `set_default_openai_key(settings.openai_api_key)` — global, once |

Part of the IntellAIgent Agent Builder Curriculum, Week 4.
