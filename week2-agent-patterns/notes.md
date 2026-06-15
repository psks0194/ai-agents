# Week 2 — Notes (Agent Patterns)

Building the classic agent design patterns from scratch — no framework, just typed LLM
calls. See the [README](./README.md) for diagrams and run commands; this file is the
conceptual distillation.

## The thesis

> Most "agents" are a handful of **focused LLM calls composed cleanly** — not one giant
> prompt.

Each pattern is a different way of composing those calls. The thin typed layer (`llm.py`)
exists so the focus stays on *composition*, not plumbing. It is deliberately **not** a
framework.

## The two big ideas

1. **One call = one job.** Every stage gets a narrow system prompt and does exactly one
   thing. Narrow scope is what makes output reliable.
2. **Type the boundaries.** Schema-constrained output (Pydantic) at every step — tool use
   on Anthropic, native structured outputs on OpenAI.

## The six patterns

| # | Pattern | One-liner | Shape |
|---|---------|-----------|-------|
| 1 | Prompt chaining | decompose a fuzzy task into focused stages | linear pipeline |
| 2 | Routing | classify, then dispatch to a specialist | fan-in decision |
| 3 | Parallelization | decompose → fan out concurrently → synthesize | fan-out (async) |
| 4 | Composition | patterns nest (a router handler *is* a chain) | recursive |
| 5 | Orchestrator–workers | a planner loops, deciding the next step adaptively | adaptive loop |
| 6 | Evaluator–optimizer | generate → evaluate → revise until shippable | feedback loop |

### Distinctions worth keeping straight

- **Routing vs Orchestrator**: a router classifies **once** and dispatches. An orchestrator
  runs in a **loop**, re-deciding each step based on what's been found so far.
- **Parallelization vs Orchestrator**: parallelization is **one-shot** decomposition (plan
  everything up front, fan out). The orchestrator is **adaptive** (decide one step at a
  time, follow up on findings).
- **Chaining vs Composition**: composition is just chaining where a "step" can itself be a
  whole other pattern. Patterns nest.

### Latency mental model (parallelization)

Total time ≈ the **slowest** worker, not the sum. (Straight from Week 0's `asyncio.gather`.)

## The non-negotiable: stop conditions

Every **loop** pattern needs a hard `MAX_ITERATIONS` cap.

- Orchestrator: stops runaway cost from endless worker dispatch.
- Evaluator–optimizer: stops a perfectionist evaluator that *never* approves.

Loops without a cap are a cost/footgun, not a feature.

## Why evaluator–optimizer actually improves quality

Drafter and evaluator are **decoupled** LLMs with opposing roles. The win comes from
**specific, actionable feedback**: on each revision the drafter sees its own previous draft
*plus* the evaluator's concrete issues ("beat 2 opens with a generic claim" — not "middle is
weak"). Vague feedback → no improvement.

## Memory / context management (separate from the 6 patterns)

A conversation only stays cheap and coherent if you **actively manage** its history.

- **Naive baseline** (`memory_naive.py`): resend the whole history every turn → input
  tokens climb every turn. The point is to *see* the cost curve.
- **`Conversation` abstraction** (`conversation.py`): wraps the message-list mess; tracks
  cumulative tokens/cost; holds the `summarize_oldest` strategy (compress old turns, keep
  recent N verbatim).
- **Summarization in action** (`memory_summarized.py`): same conversation + a token
  threshold → curve becomes a **sawtooth** (grow, drop on summary, grow) instead of a
  straight climb.
- **Scratchpad** (`scratchpad.py`): a *different* kind of memory — structured, typed notes
  the agent **curates** across a run, vs. unstructured dialogue that just grows.

Two axes of memory: **dialogue (compress it)** vs **working memory (curate it)**.

## RAG — retrieval over the notes (separate again)

Memory keeps context *inside* a run. **RAG** pulls relevant context *in from outside*.

RAG has two phases: **index once** (offline), then **retrieve + generate** per question.

**Indexing** (`rag_index.py`):
- Walk the umbrella repo for `notes.md`, **chunk** each file at heading boundaries, store
  chunks in a persistent **ChromaDB** collection (`.chroma/`). ChromaDB embeds each chunk,
  so retrieval is by **meaning**, not keywords.
- Chunking at headings keeps each chunk semantically coherent (one heading = one idea).
  Tiny chunks (<30 chars) are dropped — they rarely carry meaning.
- **Rebuilt from scratch** each run (delete + recreate the collection) to stay in sync.
  Persists on disk → index once, query many times.

**Retrieval** (`rag_retrieve.py`):
- `retrieve(query, n_results)` embeds the question and asks ChromaDB for the **top-K nearest
  chunks**, returned as typed `RetrievedChunk` objects (text + source + heading + distance).
- **Distance: smaller = more similar.** It's a *distance*, not a similarity score — low is good.
- Run it standalone to sanity-check retrieval *before* wiring in an LLM.

**The agent** (`rag_agent.py`):
- Full pipeline: retrieve → format chunks as context → ask the LLM to answer **grounded only
  in that context**, cite the source note/day, and **admit when context is insufficient**
  instead of falling back on general knowledge.
- This "ground + cite + refuse if unsupported" framing is what separates real RAG from "LLM
  guesses with extra steps."

Mental model: **chunk → embed → store** (index), then **embed query → nearest chunks →
stuff into prompt → grounded answer** (answer). `.chroma/` is gitignored — it's a
rebuildable artifact, not source.

## Gotcha: Anthropic schema constraints are hints, not limits

Anthropic tool use treats Pydantic `min_length`/`max_length` on lists as **hints** — the
model can overshoot and validation then fails client-side. Fix: leave headroom in the
schema **and** state the target count in the prompt.

## What carries forward

- Composition + loops with stop conditions → the foundation for any real multi-step agent.
- Memory strategies → the thing that makes long-running agents affordable.

Part of the IntellAIgent Agent Builder Curriculum, Week 2.
