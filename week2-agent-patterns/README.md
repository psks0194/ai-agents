# week2-agent-patterns

Building the classic agent design patterns from scratch — no framework, just
typed LLM calls and the patterns underneath every "agent framework."

Each pattern is its own runnable module built on a thin, typed LLM layer
(`llm.py`). The throughline: most "agents" are a handful of focused LLM calls
composed cleanly — not one giant prompt.

## Status (Day 14 — 2026-06-15)

- ✅ Typed LLM helpers — schema-constrained calls for Anthropic + OpenAI (`llm.py`)
- ✅ Prompt chaining — Scout → Outline → Drafter → Critic pipeline (`chain.py`)
- ✅ Routing — classify, then dispatch to a specialist (`router.py`)
- ✅ Parallelization — decompose, fan out with `asyncio`, synthesize (`parallel.py`)
- ✅ Composition — a router whose handlers are themselves chains (`composed.py`)
- ✅ Orchestrator–workers — planning LLM dispatches tasks in a loop (`orchestrator.py`)
- ✅ Evaluator–optimizer — generate, evaluate, revise until shippable (`evaluator_optimizer.py`)
- ✅ Memory: naive baseline — watch the token cost curve grow (`memory_naive.py`)
- ✅ Memory: `Conversation` abstraction + summarization strategy (`conversation.py`)
- ✅ Memory: threshold-triggered summarization in action (`memory_summarized.py`)
- ✅ Memory: structured scratchpad for a research agent (`scratchpad.py`)
- ✅ RAG: index the curriculum `notes.md` files into ChromaDB (`rag_index.py`)
- ✅ RAG: retrieval layer — query the index for top-K chunks (`rag_retrieve.py`)
- ✅ RAG: "chat with your notes" agent — retrieve → ground → answer (`rag_agent.py`)

## The patterns

### 1. Prompt chaining — `chain.py`

Decomposes one fuzzy task ("write a good post about X") into four focused stages,
each a single LLM call with a typed Pydantic output. Data flows through the
models in `models.py`:

```
topic ─▶ Scout ─▶ Angle ─▶ Outline ─▶ Outline ─▶ Drafter ─▶ Draft ─▶ Critic ─▶ Critique
        find a          structure:           write the         ship or
        sharp angle     hook + 3 beats        ~250-word post    revise?
                        + close
```

Each stage has a narrow system prompt and does exactly one thing — which is what
makes the output reliable. The chain just composes them.

### 2. Routing — `router.py`

A small, cheap classifier LLM decides *which* specialist should handle a request,
then dispatches to it. The router only classifies (it never answers); each
specialist has its own system prompt.

```
question ─▶ Router ─▶ technical | business | quick_lookup ─▶ specialist answer
```

### 3. Parallelization — `parallel.py`

The "sectioning" flavor: decompose a research question into independent
sub-questions, fan them out concurrently with `asyncio.gather`, then synthesize.
Total latency is the *slowest* worker, not the sum.

```
question ─▶ Decompose ─▶ [worker, worker, worker] ─▶ Synthesize ─▶ final answer
                          (concurrent)
```

### 4. Composition — `composed.py`

Patterns compose. A top-level router dispatches to handlers, but one of those
handlers (`content_creator`) is the *entire* chain from pattern 1 — while the
others are single specialist calls.

```
request ─▶ Router ─▶ content_creator ─▶ run_chain()  (Scout→Outline→Drafter→Critic)
                  ├─ technical_qa    ─▶ single specialist call
                  └─ quick_lookup    ─▶ single specialist call
```

### 5. Orchestrator–workers — `orchestrator.py`

Unlike parallelization's one-shot decomposer, the orchestrator runs in a **loop**.
At each step it sees what's been done so far and *adaptively* decides the next
move: dispatch another focused sub-question to a worker, or finalize. A hard
`MAX_ITERATIONS` cap keeps runaway cost off the table.

```
question ─▶ Orchestrator ─▶ dispatch_worker ─▶ worker finding ─┐
                ▲   │                                          │
                └───┴──────────── (loop, sees history) ◀───────┘
                    │
                    └─▶ finalize ─▶ synthesize findings ─▶ final answer
```

The orchestrator only plans; workers only answer; the finalizer only synthesizes.
Each has its own narrow system prompt.

### 6. Evaluator–optimizer — `evaluator_optimizer.py`

A generate → evaluate → revise loop. The drafter and evaluator are **decoupled**
LLMs with opposing roles. On each revision the drafter sees its own previous
draft *plus* the evaluator's specific, actionable issues — that targeted feedback
is what makes the loop actually improve quality. `MAX_ITERATIONS` stops a
perfectionist evaluator from never approving.

```
topic ─▶ Drafter ─▶ draft ─▶ Evaluator ─┬─ ship ─▶ final post
            ▲                            │
            └──── revise (issues) ◀──────┘
```

## Memory / context management

Separate from the six design patterns: a conversation only stays cheap and
coherent if you actively manage its history. These modules build up the problem,
then the fix.

### Naive baseline — `memory_naive.py`

What every Day 1 chat does: keep appending messages and resend the *whole*
history every turn. The module runs a fixed 10-turn conversation and prints the
per-turn token table — input tokens climb every turn because you re-pay for all
prior context. The point is to *see* the cost curve, not to fix it.

### `Conversation` abstraction + summarization — `conversation.py`

A `Conversation` dataclass wraps the message-list mess: it owns `messages`,
tracks cumulative token usage and cost, and exposes `send()`,
`estimated_tokens`, and `print_stats()`. The summarization strategy
(`summarize_oldest`) compresses the oldest turns into a single summary message
while keeping the most recent N turns verbatim — so history stops growing
unbounded.

```
[old turns] + [recent N turns]  ─▶ summarize oldest ─▶ [summary msg] + [recent N turns]
```

### Summarization in action — `memory_summarized.py`

Runs the *same* 10-turn conversation as `memory_naive.py`, but through a
`Conversation` with a token threshold. Before each turn, if `estimated_tokens`
crosses `SUMMARIZE_THRESHOLD_TOKENS` it calls `summarize_oldest()` first. The
result is the payoff: per-turn input tokens grow, drop sharply after a summary
fires, then grow again — a sawtooth instead of the naive straight climb. Run it
right after `memory_naive` to compare the two cost curves side by side.

### Scratchpad memory — `scratchpad.py`

A different kind of memory: instead of compressing *dialogue*, the agent keeps a
typed, structured **scratchpad** of notes and decisions it accumulates across a
run. A research agent loops — at each step it reads its scratchpad, may add a
note, commit a decision, dispatch a worker for the next question, or conclude —
then writes a final answer from the notes alone.

```
question ─▶ [read scratchpad] ─▶ ResearchStep ─┬─ add note / commit decision
                ▲                               ├─ next_question ─▶ worker ─┐
                └──────── (loop) ◀──────────────┘                          │
                                                └─ ready_to_conclude ─▶ final answer
```

Conversation history is unstructured and grows; a scratchpad is structured and
*curated* — the agent decides what's worth keeping.

## RAG — retrieval over the curriculum notes

Memory keeps context *inside* a single run. RAG (retrieval-augmented generation)
pulls relevant context *in from outside* — here, the `notes.md` files written across
every week of the curriculum.

RAG splits into two phases: **index once** (offline), then **retrieve + generate**
on every question (online).

```
INDEX (once):     notes.md ─▶ chunk ─▶ embed ─▶ ChromaDB (.chroma/)
ANSWER (per Q):   question ─▶ embed ─▶ top-K chunks ─▶ stuff into prompt ─▶ LLM answer
```

### Indexing — `rag_index.py`

The build-once step. It walks the umbrella repo for `notes.md` files, splits each
into chunks at markdown heading boundaries, and stores them in a persistent
**ChromaDB** collection on disk (`.chroma/`). ChromaDB embeds each chunk
automatically, so later you can search by *meaning*, not keywords. Re-run any time
the notes change — it rebuilds the collection from scratch.

```
notes.md files ─▶ chunk at headings ─▶ ChromaDB (embed + persist to .chroma/)
```

### Retrieval — `rag_retrieve.py`

The query layer. `retrieve(query, n_results)` embeds the question, asks ChromaDB
for the top-K nearest chunks, and returns them as typed `RetrievedChunk` objects
(text + `source` + `heading` + `distance`, where **smaller distance = more
similar**). It reuses `CHROMA_DIR`/`COLLECTION_NAME` from the indexer so both
halves point at the same store. Run it directly to eyeball what comes back for a
few sample queries — useful for sanity-checking retrieval *before* an LLM is
involved.

### The RAG agent — `rag_agent.py`

The full "chat with your notes" pipeline: retrieve top-K chunks → format them as
context → ask Claude to answer **grounded only in that context**, citing which
note/day it came from and admitting when the context is insufficient (rather than
falling back on general knowledge). A CLI takes the question, `--n` (chunk count),
and `--quiet` (hide the retrieved chunks).

```
question ─▶ retrieve() ─▶ format_context ─▶ [grounded prompt] ─▶ Claude ─▶ cited answer
```

This is the substrate of every "chat with your docs" product — and the payoff of
having written `notes.md` files all along.

## Run

```bash
# Prompt chaining — default topic, or pass your own
uv run python -m week2_agent_patterns.chain
uv run python -m week2_agent_patterns.chain "prompt caching — the win nobody measures"

# Routing — demos three question types
uv run python -m week2_agent_patterns.router

# Parallelization — decompose, fan out, synthesize
uv run python -m week2_agent_patterns.parallel

# Composition — router whose content_creator handler is the full chain
uv run python -m week2_agent_patterns.composed

# Orchestrator–workers — adaptive planning loop
uv run python -m week2_agent_patterns.orchestrator

# Evaluator–optimizer — generate, evaluate, revise until shippable
uv run python -m week2_agent_patterns.evaluator_optimizer

# Memory: naive accumulation — watch the token cost curve grow
uv run python -m week2_agent_patterns.memory_naive

# Memory: same conversation, but summarize past a token threshold (sawtooth curve)
uv run python -m week2_agent_patterns.memory_summarized

# Memory: research agent with a structured scratchpad
uv run python -m week2_agent_patterns.scratchpad

# RAG: (re)build the curriculum notes index in ChromaDB — run once
uv run python -m week2_agent_patterns.rag_index

# RAG: inspect what retrieval returns for a few sample queries
uv run python -m week2_agent_patterns.rag_retrieve

# RAG: ask a question about your notes (retrieve → grounded answer)
uv run python -m week2_agent_patterns.rag_agent
uv run python -m week2_agent_patterns.rag_agent "How does the orchestrator differ from routing?" --n 6
```

## Architecture

```
src/week2_agent_patterns/
├── config.py    # pydantic-settings config (Anthropic + OpenAI keys)
├── llm.py       # thin typed LLM helpers — schema-forced calls (Anthropic + OpenAI), plus plain text
├── models.py    # Pydantic models for the chain (Angle, Outline, Draft, Critique)
│
├── chain.py                # Pattern 1: prompt chaining — Scout → Outline → Drafter → Critic
├── router.py               # Pattern 2: routing — classify, then dispatch to a specialist
├── parallel.py             # Pattern 3: parallelization — decompose, async fan-out, synthesize
├── composed.py             # Pattern 4: composition — a router whose handlers include the chain
├── orchestrator.py         # Pattern 5: orchestrator–workers — adaptive planning loop
├── evaluator_optimizer.py  # Pattern 6: evaluator–optimizer — generate, evaluate, revise loop
│
├── memory_naive.py         # Memory: naive accumulation — the cost-curve baseline
├── conversation.py         # Memory: Conversation abstraction + summarization strategy
├── memory_summarized.py    # Memory: threshold-triggered summarization in action
├── scratchpad.py           # Memory: structured scratchpad for a research agent
│
├── rag_index.py            # RAG: chunk + index the curriculum notes.md files into ChromaDB
├── rag_retrieve.py         # RAG: query the index — top-K nearest chunks as typed objects
└── rag_agent.py            # RAG: "chat with your notes" — retrieve → grounded, cited answer
```

`llm.py` is deliberately *not* a framework — just the minimal glue so the focus
stays on the patterns. Schema-constrained output is done via tool use on
Anthropic and native structured outputs on OpenAI.

### A note on schema constraints

Anthropic tool-use treats Pydantic `min_length`/`max_length` on lists as *hints*,
not hard limits — the model can overshoot, and validation then fails client-side.
So constrained list fields (e.g. `Critique.reasons`) keep a little headroom in the
schema **and** state the target count in the prompt.

Part of the IntellAIgent Agent Builder Curriculum, Week 2.
