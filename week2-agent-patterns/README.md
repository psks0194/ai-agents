# week2-agent-patterns

Building the classic agent design patterns from scratch — no framework, just
typed LLM calls and the patterns underneath every "agent framework."

Each pattern is its own runnable module built on a thin, typed LLM layer
(`llm.py`). The throughline: most "agents" are a handful of focused LLM calls
composed cleanly — not one giant prompt.

## Status (Day 4 — 2026-06-06)

- ✅ Typed LLM helpers — schema-constrained calls for Anthropic + OpenAI (`llm.py`)
- ✅ Prompt chaining — Scout → Outline → Drafter → Critic pipeline (`chain.py`)
- ✅ Routing — classify, then dispatch to a specialist (`router.py`)
- ✅ Parallelization — decompose, fan out with `asyncio`, synthesize (`parallel.py`)
- ✅ Composition — a router whose handlers are themselves chains (`composed.py`)
- ⏳ Orchestrator–workers, evaluator–optimizer (next)

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
```

## Architecture

```
src/week2_agent_patterns/
├── config.py    # pydantic-settings config (Anthropic + OpenAI keys)
├── llm.py       # thin typed LLM helpers — schema-forced calls (Anthropic + OpenAI), plus plain text
├── models.py    # Pydantic models for the chain (Angle, Outline, Draft, Critique)
│
├── chain.py     # Pattern 1: prompt chaining — Scout → Outline → Drafter → Critic
├── router.py    # Pattern 2: routing — classify, then dispatch to a specialist
├── parallel.py  # Pattern 3: parallelization — decompose, async fan-out, synthesize
└── composed.py  # Pattern 4: composition — a router whose handlers include the chain
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
