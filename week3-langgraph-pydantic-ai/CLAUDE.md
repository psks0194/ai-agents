# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Repo-wide conventions live in `../CLAUDE.md`. This file covers what is specific to **week 3**.

## What this is

Week 2's hand-rolled patterns, re-learned on **two frameworks side by side**:

- **LangGraph** — agent as a **state machine** (typed state, nodes that return partial updates, edges + conditional edges, checkpointer, `interrupt()` / `Command(resume=…)`). You own the control flow.
- **Pydantic AI** — agent as a **typed function with tools** (`Agent(model, deps_type, output_type, instructions)` + `@agent.tool` functions). The framework runs the loop; you declare the pieces.

The capstone is the head-to-head: the **same** structured research-note task, built in both frameworks, then `compare_frameworks.py` runs both on one topic and prints a side-by-side metrics table.

## Commands

From inside `week3-langgraph-pydantic-ai/`:

```bash
uv sync
uv run python -m week3_langgraph_pydantic_ai.first_graph              # smallest LangGraph (no LLM)
uv run python -m week3_langgraph_pydantic_ai.content_chain            # Week 2's chain rebuilt as a graph
uv run python -m week3_langgraph_pydantic_ai.content_loop             # + conditional edge: critic → drafter
uv run python -m week3_langgraph_pydantic_ai.checkpointing_demo
uv run python -m week3_langgraph_pydantic_ai.hitl_workflow            # INTERACTIVE — approves/rejects in your terminal

uv run python -m week3_langgraph_pydantic_ai.pai_first_agent          # Pydantic AI: typed output, no tools
uv run python -m week3_langgraph_pydantic_ai.pai_tool_agent           # full tool loop, hidden
uv run python -m week3_langgraph_pydantic_ai.pai_tool_stream_agent    # agent.iter() — nodes + events visible

uv run python -m week3_langgraph_pydantic_ai.compare_frameworks       # the head-to-head table
```

Full module list is in `README.md` under "Run". Needs `ANTHROPIC_API_KEY` in the repo-root `.env`.

## Architecture

```
src/week3_langgraph_pydantic_ai/
├── config.py                # pydantic-settings — Anthropic key from the repo-root .env
│
│  # LangGraph (state machine)
├── first_graph.py           # state + nodes + edges, no LLM
├── content_chain.py         # 4-node graph w/ structured output
├── content_loop.py          # + conditional edge + iteration cap; backs the next two demos
├── checkpointing_demo.py    # stream + persist per thread_id
├── hitl_workflow.py         # interrupt() / Command(resume=…)
│
│  # Pydantic AI (declarative agent)
├── pai_first_agent.py / pai_tool_agent.py / pai_tool_stream_agent.py
│
│  # Head-to-head
├── research_note_pai.py     # same task, Pydantic AI
├── research_note_lg.py      # same task, hand-built LangGraph loop
└── compare_frameworks.py    # runs both, prints metrics
```

- The two `research_note_*.py` files **expose the same `run()` / `display()` interface** so `compare_frameworks.py` can call them identically. Preserve that interface when editing either.
- `content_loop.build_graph(use_checkpointer=True)` is shared infrastructure for `checkpointing_demo.py` and `hitl_workflow.py`. Touching `content_loop.py` affects both demos.

## Gotchas

- **LangGraph coerces state by the node's first-parameter annotation, not the graph's declared schema.** A router or node annotated `ContentState` will *get* a `ContentState` even if the graph schema is a richer subclass like `HitlState` — accessing a subclass-only field then raises `AttributeError`. **Fix: annotate each function with the exact state subtype whose fields it touches.** This bit `route_after_human` in `hitl_workflow.py`; same trap will recur with any state subclass.
- **Keys are passed explicitly to both frameworks** (since `pydantic-settings` does *not* populate `os.environ`):
  - LangGraph: `ChatAnthropic(..., api_key=settings.anthropic_api_key)`.
  - Pydantic AI: `AnthropicModel(..., provider=AnthropicProvider(api_key=settings.anthropic_api_key))`. The shorthand `Agent("anthropic:claude-…")` only works if the key is in the *environment*, so avoid it here.
- **`research_note_lg.py` has no recursion cap.** The model decides when to stop calling tools; a real MCP run fanned out to ~30 fetches. Pass `invoke(..., {"recursion_limit": N})` if you need a circuit breaker. A silent `fetch_url` failure (403/timeout/etc.) returns an error string and the model adapts — it's not a bug.
- **`grandalf`** is needed for `graph.get_graph().draw_ascii()` in `content_chain.py`. It's an optional install; without it the ASCII print fails but the graph still runs.
