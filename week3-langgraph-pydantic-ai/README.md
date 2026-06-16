# week3-langgraph-pydantic-ai

Re-learning the agent patterns from Week 2 — this time on top of **LangGraph**.
Same ideas (typed state, focused steps, explicit control flow), now expressed as
a **state machine**: nodes that read/write a shared state, wired by edges.

The throughline: a LangGraph "graph" is just `state → node → node → state`. Once
you've hand-rolled these patterns in Week 2, LangGraph stops looking like magic —
it's the loop and the plumbing, standardized.

## Status (Day 2 — 2026-06-16)

- ✅ First graph — state, nodes, edges, compile, invoke (no LLM) (`first_graph.py`)
- ✅ Config — `pydantic-settings`, Anthropic key from the repo-root `.env` (`config.py`)
- ✅ Content chain — Week 2's Scout → Outline → Drafter → Critic, rebuilt as a graph (`content_chain.py`)
- ✅ Content loop — critic loops back to drafter via a conditional edge, with an iteration cap (`content_loop.py`)
- ✅ Checkpointing — stream intermediate state, persist per `thread_id`, resume (`checkpointing_demo.py`)
- ✅ Human-in-the-loop — `interrupt()` pauses for approval, `Command(resume=…)` continues (`hitl_workflow.py`)

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

Three more primitives unlock the interesting workflows:

5. **Conditional edges** — `add_conditional_edges(node, router_fn, mapping)`. The
   router function reads state and returns the name of the next node (or `END`).
   This is how loops and branches happen.
6. **Checkpointer** — `compile(checkpointer=MemorySaver())`. Saves state after every
   node, keyed by a `thread_id`. Enables streaming intermediate state, inspecting
   it (`graph.get_state(config)`), and resuming. Required for human-in-the-loop.
7. **Interrupt / resume** — `interrupt(payload)` pauses the graph and hands the
   payload back to the caller; `graph.stream(Command(resume=value), config)`
   continues, with `interrupt()` returning `value`. Needs a checkpointer.

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

### 3. Content loop — `content_loop.py`

The content chain plus a **feedback loop**. After the critic, a conditional edge
(`route_after_critic`) decides: `ship` → `END`, else loop back to `drafter` —
until the verdict is `ship` or `iteration` hits `max_iterations`. The drafter
itself branches: a first draft vs. a revision that incorporates the critic's
reasons. This is Week 2's evaluator–optimizer, expressed as a graph.

```
START ─▶ scout ─▶ outline ─▶ drafter ─▶ critic ─▶ (route_after_critic)
                              ▲                       │
                              └──── revise ◀──────────┤ verdict == revise & under cap
                                                      └─ ship / cap ─▶ END
```

It also compiles with a checkpointer, so the same graph backs the next two demos.

### 4. Checkpointing — `checkpointing_demo.py`

Reuses `content_loop`'s `build_graph(use_checkpointer=True)` to show what a
checkpointer buys you:

- `graph.stream(initial, config)` yields `{node_name: partial_state}` after each
  node — you watch the run progress live instead of waiting for one final result.
- State persists per **`thread_id`** (a session id), so parallel runs don't bleed
  into each other.
- `graph.get_state(config)` reads the final (or any) saved state back out.

### 5. Human-in-the-loop — `hitl_workflow.py`

The payoff feature, and the one you can't cleanly hand-roll. After the critic, a
`human_approval` node calls `interrupt()` — the graph **pauses** and surfaces the
draft to you. You resume with `Command(resume={"action": "approve"|"reject", …})`;
`route_after_human` then ends the graph or loops back to the drafter with your
notes.

```
… ─▶ critic ─▶ human_approval ─[interrupt: pause]→  (you decide)
                     ▲                                  │
                     │         approve ─▶ END           │
                     └──────── reject (notes) ◀─────────┘
```

> **Gotcha (today's bug):** LangGraph coerces state into whatever Pydantic type a
> node/router annotates its **first parameter** as — the annotation overrides the
> graph's declared schema. `route_after_human` was annotated `ContentState` but
> needed the subclass field `human_decision`, so it crashed with
> `AttributeError: 'ContentState' object has no attribute 'human_decision'`. Fix:
> annotate each function with the exact state type whose fields it touches
> (`HitlState` here).

## Run

```bash
# Smallest possible graph — no LLM, just state/nodes/edges
uv run python -m week3_langgraph_pydantic_ai.first_graph

# Content chain — Scout → Outline → Drafter → Critic as a graph (prints the ASCII topology first)
uv run python -m week3_langgraph_pydantic_ai.content_chain

# Content loop — critic loops back to drafter until 'ship' or the iteration cap
uv run python -m week3_langgraph_pydantic_ai.content_loop

# Checkpointing — stream node-by-node state, then read final state from the checkpointer
uv run python -m week3_langgraph_pydantic_ai.checkpointing_demo

# Human-in-the-loop — pauses for your approve/reject (interactive; run in your terminal)
uv run python -m week3_langgraph_pydantic_ai.hitl_workflow
```

> If you have another venv active (e.g. `hntop`), `uv run` warns and ignores it,
> defaulting to this project's `.venv` — which is what you want. `deactivate` to
> silence the warning, or pass `--active`.

## Architecture

```
src/week3_langgraph_pydantic_ai/
├── config.py          # pydantic-settings — Anthropic key from the repo-root .env
│
├── first_graph.py        # Minimal graph: TypedDict state, 2 nodes, linear edges (no LLM)
├── content_chain.py      # Week 2's content pipeline as a 4-node LangGraph (structured output)
├── content_loop.py       # + conditional edge: critic loops back to drafter (iteration cap)
├── checkpointing_demo.py # Streaming + persisted state per thread_id (reuses content_loop)
└── hitl_workflow.py      # Human-in-the-loop: interrupt() pauses, Command(resume=…) continues
```

### A note on the API key

`ChatAnthropic` defaults to reading `ANTHROPIC_API_KEY` from the **environment**.
The key here lives in the repo-root `.env`, which `pydantic-settings` loads into a
`settings` object — *not* into the OS environment. So models are constructed with
`api_key=settings.anthropic_api_key` explicitly. Same single source of truth as
Week 2.

Part of the IntellAIgent Agent Builder Curriculum, Week 3.
