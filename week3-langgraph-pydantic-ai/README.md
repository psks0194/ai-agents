# week3-langgraph-pydantic-ai

Re-learning the agent patterns from Week 2 — this time on top of **LangGraph**.
Same ideas (typed state, focused steps, explicit control flow), now expressed as
a **state machine**: nodes that read/write a shared state, wired by edges.

The throughline: a LangGraph "graph" is just `state → node → node → state`. Once
you've hand-rolled these patterns in Week 2, LangGraph stops looking like magic —
it's the loop and the plumbing, standardized.

## Status (Day 1 — 2026-06-15)

- ✅ First graph — state, nodes, edges, compile, invoke (no LLM) (`first_graph.py`)
- ✅ Config — `pydantic-settings`, Anthropic key from the repo-root `.env` (`config.py`)
- ✅ Content chain — Week 2's Scout → Outline → Drafter → Critic, rebuilt as a graph (`content_chain.py`)

## Core concepts

LangGraph has four moving parts. Every file here is some combination of them:

1. **State** — a typed object (`TypedDict` or a Pydantic `BaseModel`) that flows
   through the graph. Every node reads it and returns a *partial update*.
2. **Nodes** — plain functions `(state) -> dict`. The returned dict is merged into
   the state. A node does one thing.
3. **Edges** — the control flow. `START → node → node → END` defines execution order.
4. **Compile + invoke** — `builder.compile()` produces a runnable graph;
   `graph.invoke(initial_state)` runs it and returns the final state.

Mental model: **nodes transform state; edges decide what runs next.** That's the
whole framework.

## The files

### 1. First graph — `first_graph.py`

The smallest possible LangGraph, deliberately **with no LLM** — so the framework
itself is the only new thing. State is a `TypedDict`; two nodes transform it
(`add_greeting` → `count_words`); edges run them in order.

```
START ─▶ greeting ─▶ counter ─▶ END
        (mutates text)  (counts words)
```

Run it and watch the initial state become the final state. This is the skeleton
every other graph fills in.

### 2. Content chain — `content_chain.py`

Week 2's `chain.py` content pipeline, rebuilt node-for-node as a graph — the
direct "same task, now in LangGraph" comparison. Four nodes, each a single
structured LLM call, threaded through one Pydantic `ContentState`:

```
START ─▶ scout ─▶ outline ─▶ drafter ─▶ critic ─▶ END
        find an   hook + 3    ~250-word   ship or
        angle     beats+close  post        revise?
```

What LangGraph adds over the hand-written Week 2 version:

- **State is declared once** (`ContentState`) instead of passed call-to-call.
- Each node returns only the fields it produces; LangGraph merges them in.
- The graph is **inspectable** — `graph.get_graph().draw_ascii()` prints the
  topology (needs `grandalf`).
- Structured output via LangChain's `model.with_structured_output(schema)` instead
  of raw tool-use plumbing.

## Run

```bash
# Smallest possible graph — no LLM, just state/nodes/edges
uv run python -m week3_langgraph_pydantic_ai.first_graph

# Content chain — Scout → Outline → Drafter → Critic as a graph (prints the ASCII topology first)
uv run python -m week3_langgraph_pydantic_ai.content_chain
```

> If you have another venv active (e.g. `hntop`), `uv run` warns and ignores it,
> defaulting to this project's `.venv` — which is what you want. `deactivate` to
> silence the warning, or pass `--active`.

## Architecture

```
src/week3_langgraph_pydantic_ai/
├── config.py          # pydantic-settings — Anthropic key from the repo-root .env
│
├── first_graph.py     # Minimal graph: TypedDict state, 2 nodes, linear edges (no LLM)
└── content_chain.py   # Week 2's content pipeline as a 4-node LangGraph (structured output)
```

### A note on the API key

`ChatAnthropic` defaults to reading `ANTHROPIC_API_KEY` from the **environment**.
The key here lives in the repo-root `.env`, which `pydantic-settings` loads into a
`settings` object — *not* into the OS environment. So models are constructed with
`api_key=settings.anthropic_api_key` explicitly. Same single source of truth as
Week 2.

Part of the IntellAIgent Agent Builder Curriculum, Week 3.
