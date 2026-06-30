# IntellAIgent Agent Builder Curriculum

Weekly sprints that build the **same canonical agent** — a tool-use loop that
produces a structured research note — across raw SDKs and progressively
higher-level frameworks.

The throughline: **an agent is a loop** (`call → tool → result → call → final
answer`). Every framework hides or exposes that loop differently. Each week
re-learns the same patterns one rung higher up the stack, so you can see exactly
what each abstraction buys — and what it costs.

Each week is self-contained: its own `pyproject.toml` / `package.json`,
lockfile, venv, and `CLAUDE.md`. There's no monorepo build at the top.

## The weeks

### [Week 0 — Python fundamentals sprint](./week0-python-sprint/) · [capstone: hntop](./hntop/)

Builds the foundations for agent code: syntax and data structures, type hints +
Pydantic for runtime-validated data at boundaries, async/await and concurrent
I/O via `asyncio.gather`, and config with `pydantic-settings` plus `src/` layout
packaging. The capstone [`hntop`](./hntop/) applies all of it to a
production-shaped async CLI that fetches Hacker News top stories concurrently.
Key concepts: Pydantic validates at program *edges*, async concurrency collapses
network time to the slowest call rather than the sum, and repo-root `.env`
resolution becomes the config template for every later week. **Standout
artifact:** the `src/fetcher/` package and `hntop/`, demonstrating the canonical
src-layout structure (Pydantic models, async client, argparse CLI) that every
agent week builds on.

### [Week 1 — Tri-provider agent](./week1-tri-provider-agent/)

Builds the same tool-using agent (calculator, current-time, fetch-url) three
times across the Anthropic, OpenAI, and Gemini SDKs to expose the agent loop
under every framework: call model → tool request → run tool → feed result back →
repeat → final answer. The key insight: tool *implementations* are
provider-agnostic Python in `tools.py`, while only the *schema vocabulary* and
message plumbing differ — "same protocol, three dialects." The progression runs
first_call → chat → streaming → full tool loop, then adds structured outputs and
a cross-provider benchmark. **Standout artifact:** `benchmark.py`, running one
task across all three providers with a side-by-side latency/tokens/cost table —
proof the hand-written loop is portable.

### [Week 2 — Hand-rolled agent patterns](./week2-agent-patterns/)

Distills the thesis that most agents are a handful of focused LLM calls composed
cleanly, not one giant prompt. Hand-rolls six design patterns (prompt chaining,
routing, parallelization, composition, orchestrator-workers,
evaluator-optimizer) on a thin typed LLM layer with no framework, each built on
`llm.py` (schema-constrained calls) and `models.py` (Pydantic schemas). Also
covers memory management (naive → Conversation → summarization → scratchpad) and
a working RAG pipeline that chunks the repo's `notes.md` files into ChromaDB for
grounded retrieval. Key concepts: narrow scope makes output reliable, every loop
needs a hard `MAX_ITERATIONS` cap, and memory comes in two flavors (dialogue
compression vs curated notes). **Standout artifact:** `llm.py` + `orchestrator.py`,
showing an adaptive planning loop where one LLM picks the next step and
dispatches workers.

### [Week 3 — LangGraph + Pydantic AI](./week3-langgraph-pydantic-ai/)

Re-learns the Week 2 patterns on two frameworks side by side: LangGraph models
an agent as a **state machine** (typed state, nodes returning partial updates,
edges, checkpointing, human-in-the-loop), while Pydantic AI models it as a
**typed function with tools** (output_type, deps, instructions, `@agent.tool`).
Key concepts: LangGraph gives full control-flow visibility, Pydantic AI hides
the loop with less ceremony, and both expose the same underlying patterns in
different syntax. **Standout artifact:** `research_note_lg.py` and
`research_note_pai.py` (identical task, two implementations) plus
`compare_frameworks.py`, which runs both on one topic and prints a
latency/tokens metrics table.

### Week 4 — OpenAI Agents SDK + Mastra · [Python](./week4-openai-mastra/) · [TypeScript](./week4-mastra/)

Covers the patterns a third time in two parallel tracks. The Python
[**OpenAI Agents SDK**](./week4-openai-mastra/) track builds a canonical agent
via `Agent` declarations + `Runner` loop, extends to a three-way bake-off with
Pydantic AI and LangGraph, then adds the SDK's signatures — **handoffs**
(model-driven control transfer) and **guardrails** (input/output tripwires). The
[**Mastra (TypeScript)**](./week4-mastra/) track rebuilds the tool agent, then
adds **workflows** (typed step pipelines with `.then()` / `.parallel()`) and
**RAG** (Markdown chunking → OpenAI embeddings → LibSQL vector store). Key
concepts: Mastra's model router abstracts provider keys via a gateway, and
workflows enforce typed contracts between steps at compile time. **Standout
artifacts:** `compare_three.py` (three-way metrics table) for Python, and
`content-workflow.ts` + `parallel-critic-workflow.ts` for Mastra (sequential
chaining and concurrent fan-out/fan-in with typed schemas).

### [Week 5 — Claude Code extensibility](./week5-claude-code/)

Builds the extensibility harness around Claude Code itself: CLAUDE.md
(always-true context every session), **skills** (repeatable playbooks whose
`description` drives auto-invocation), **subagents** (own context window for
isolation/parallelism, defined as YAML-frontmatter Markdown in
`.claude/agents/`), plus hooks, MCP, and plugins as the full stack. Two
subagents are built for this repo: `curriculum-explorer` (Haiku-powered
search-and-summarize across weeks) and `pattern-reviewer` (Sonnet-powered
convention audit via git diff). Key concepts: skills earn their place at a ~30+
use threshold, subagents fan out noisy work and return only conclusions,
`description` must state both *what* and *when*, and the harness is the moat.
**Standout artifact:** the subagent architecture itself — YAML-frontmatter
`.claude/agents/*.md` files with least-privilege tool grants.

## Repo-wide setup

- **Single `.env` at the repo root** holds `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
  `GOOGLE_API_KEY`. Every Python week's `config.py` resolves it via
  `pydantic-settings`. `week4-mastra/` is the exception — it has its own `.env`.
  Copy `.env.example` to get started.
- **`.chroma/` at the repo root** is the shared RAG vector store written by
  `week2-agent-patterns/rag_index.py`. Gitignored and rebuildable — re-run
  `rag_index` after any `notes.md` changes.
- **No top-level test runner.** Each week stands alone; only `hntop/` has tests.
