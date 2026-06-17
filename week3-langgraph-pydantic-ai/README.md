# week3-langgraph-pydantic-ai

Re-learning the agent patterns from Week 2 on two frameworks: **LangGraph** and
**Pydantic AI**. Same ideas (typed state, focused steps, explicit control flow),
seen through two different philosophies.

- **LangGraph** models an agent as a **state machine**: nodes that read/write a
  shared state, wired by edges. You own the control flow.
- **Pydantic AI** models an agent as a **typed function with tools**: you declare
  the output type, the deps, and the tools — the framework runs the loop.

The throughline from Week 2: once you've hand-rolled the agent loop, both
frameworks stop looking like magic — they're the loop and the plumbing,
standardized in two different shapes.

## Status (Day 3 — 2026-06-17)

**LangGraph**

- ✅ First graph — state, nodes, edges, compile, invoke (no LLM) (`first_graph.py`)
- ✅ Config — `pydantic-settings`, Anthropic key from the repo-root `.env` (`config.py`)
- ✅ Content chain — Week 2's Scout → Outline → Drafter → Critic, rebuilt as a graph (`content_chain.py`)
- ✅ Content loop — critic loops back to drafter via a conditional edge, with an iteration cap (`content_loop.py`)
- ✅ Checkpointing — stream intermediate state, persist per `thread_id`, resume (`checkpointing_demo.py`)
- ✅ Human-in-the-loop — `interrupt()` pauses for approval, `Command(resume=…)` continues (`hitl_workflow.py`)

**Pydantic AI**

- ✅ First agent — typed output, no tools (`pai_first_agent.py`)
- ✅ Tool agent — decorated tools + injected deps; framework runs the loop (`pai_tool_agent.py`)
- ✅ Streaming the loop — `agent.iter()` exposes nodes + events (`pai_tool_stream_agent.py`)

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

## Pydantic AI

A different shape from LangGraph. Instead of wiring nodes and edges, you declare
an **`Agent`** and let the framework run the loop. The moving parts:

1. **Model + provider** — `AnthropicModel("claude-…", provider=AnthropicProvider(api_key=…))`.
   The provider carries the key (ours comes from `settings`, not the env).
2. **`Agent`** — bundles the model, an `output_type` (a Pydantic model for typed
   results), `instructions`, and a `deps_type`.
3. **Tools** — plain functions decorated with `@agent.tool`. The first param is
   always `ctx: RunContext[Deps]`; the docstring becomes the tool description the
   model sees. The model decides when to call them; the framework runs the loop.
4. **Deps** — a dataclass injected into every tool via `ctx.deps` (e.g. a shared
   `httpx.Client`). Declared once with `deps_type`, passed per run with `deps=…`.

Mental model: **LangGraph = you build the loop; Pydantic AI = you declare the
pieces and it runs the loop.**

### 6. First agent — `pai_first_agent.py`

The smallest Pydantic AI agent: no tools, just typed output. The agent's
`output_type=BookRecommendation` forces the model to return a validated Pydantic
object; `result.output` is that typed object, and `result.usage` has token counts.
Compare to `first_graph.py` to feel the two philosophies side by side.

### 7. Tool agent — `pai_tool_agent.py`

Week 1's tool-using agent (calculator, time, fetch_url), now in Pydantic AI. Tools
are decorated functions; deps (`AgentDeps` holding an `httpx.Client`) are injected
via `ctx.deps`. `agent.run_sync(prompt, deps=deps)` runs the **whole tool loop
internally** — call → tool → result → call → final answer — and hands back the
final output. The loop is hidden.

### 8. Streaming the loop — `pai_tool_stream_agent.py`

Same agent, two run modes:

- **Mode 1 — `run_sync()`**: loop hidden (as above).
- **Mode 2 — `agent.iter()`**: step through the agent's internal **graph**
  node-by-node and stream **events** — the black box becomes glass.

`agent.iter()` yields four node types, checked with `Agent.is_*_node(node)`:

```
UserPrompt ─▶ ModelRequest ─▶ CallTools ─▶ ModelRequest ─▶ … ─▶ End
                  │                              ▲
                  └── model asks for tools ──────┘
              (alternates until the model returns text, not a tool call)
```

- **ModelRequest** node → stream gives `PartStartEvent` (a `TextPart` or
  `ToolCallPart` began) and `FinalResultEvent` (the answer, not another tool call).
- **CallTools** node → stream gives `FunctionToolCallEvent` (tool name + args) and
  `FunctionToolResultEvent` (the tool's return value).

This is exactly Week 1's hand-written `call → tool_use → tool_result` loop — now
driven by Pydantic AI, with `iter()` letting you watch each turn.

> `PartDeltaEvent` is imported but unhandled — add a branch on it for true
> token-by-token streaming of the model's text/args.

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

# --- Pydantic AI ---
# First agent — typed output, no tools
uv run python -m week3_langgraph_pydantic_ai.pai_first_agent

# Tool agent — runs the full tool loop internally
uv run python -m week3_langgraph_pydantic_ai.pai_tool_agent

# Streaming — Mode 1 (loop hidden) then Mode 2 (nodes + events visible)
uv run python -m week3_langgraph_pydantic_ai.pai_tool_stream_agent
```

> If you have another venv active (e.g. `hntop`), `uv run` warns and ignores it,
> defaulting to this project's `.venv` — which is what you want. `deactivate` to
> silence the warning, or pass `--active`.

## Architecture

```
src/week3_langgraph_pydantic_ai/
├── config.py          # pydantic-settings — Anthropic key from the repo-root .env
│
│   # --- LangGraph ---
├── first_graph.py           # Minimal graph: TypedDict state, 2 nodes, linear edges (no LLM)
├── content_chain.py         # Week 2's content pipeline as a 4-node LangGraph (structured output)
├── content_loop.py          # + conditional edge: critic loops back to drafter (iteration cap)
├── checkpointing_demo.py    # Streaming + persisted state per thread_id (reuses content_loop)
├── hitl_workflow.py         # Human-in-the-loop: interrupt() pauses, Command(resume=…) continues
│   # --- Pydantic AI ---
├── pai_first_agent.py       # Typed-output agent, no tools
├── pai_tool_agent.py        # Decorated tools + injected deps; run_sync runs the loop
└── pai_tool_stream_agent.py # agent.iter() — step the loop's nodes, stream events
```

### A note on the API key

Both frameworks default to reading `ANTHROPIC_API_KEY` from the **environment**.
The key here lives in the repo-root `.env`, which `pydantic-settings` loads into a
`settings` object — *not* into the OS environment. So the key is always passed
explicitly, the same single source of truth as Week 2:

- **LangGraph:** `ChatAnthropic(..., api_key=settings.anthropic_api_key)`.
- **Pydantic AI:** `AnthropicModel(..., provider=AnthropicProvider(api_key=settings.anthropic_api_key))`.
  The string form `Agent("anthropic:claude-…")` only works if the key is in the
  environment, so it's avoided here.

Part of the IntellAIgent Agent Builder Curriculum, Week 3.
