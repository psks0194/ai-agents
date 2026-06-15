# Week 1 — Notes (Tri-Provider Agent)

Goal: build the **same** tool-using agent three times — Anthropic, OpenAI, Gemini — to
feel the protocol that lives underneath every "agent framework." See the
[README](./README.md) for the file index and run commands; this file is the conceptual
distillation.

## The core insight

An "agent" is not magic. It's a **loop**:

```
call model → model asks for a tool → run the tool → feed result back → repeat → final answer
```

Once you've written that loop by hand, frameworks stop looking mysterious — they're just
this loop with ergonomics bolted on.

## What's actually the same across providers

- The **tool implementations** (`tools.py`: calculator, current time, web fetch) are
  provider-agnostic plain Python. Written once, reused by all three.
- The **agent loop shape** is identical everywhere.

## What actually differs

Only two things change between SDKs:

1. **Tool schema vocabulary** — how you describe a tool to the model.
   - Anthropic: `tools` with input schemas.
   - OpenAI: function/tool wrappers.
   - Gemini: `FunctionDeclaration`.
2. **Message/response plumbing** — the field names and the way a tool call comes back and
   a tool result goes in (`tool_use`/`tool_result` vs OpenAI/Gemini equivalents).

Mental model: **same protocol, three dialects.** The hard part of "porting" an agent is
purely translation, not redesign.

## Building blocks, in order

For each provider the progression was the same:

```
first_call  →  chat (multi-turn)  →  streaming  →  agent (tool loop)
```

- **first_call** — the smallest possible LLM call; prove the SDK + key work.
- **chat** — maintain a `messages` history across turns (the state an agent keeps).
- **streaming** — print tokens as generated; UX, not capability.
- **agent** — the tool-use loop; the real payoff.

## Day 5 — cross-cutting

- **Streaming agent loop** — combine the loop with token-by-token output.
- **Structured outputs** — force the model to return JSON matching a Pydantic schema
  (Anthropic via tool use, OpenAI via native structured outputs). Direct continuation of
  Week 0 Day 2: *validate at the boundary.*
- **Benchmark** — run one task across all three providers and compare latency, tokens, and
  cost. The honest way to pick a provider.

## Gotchas / lessons

- Streaming is a UX feature, not a capability — don't conflate the two.
- Tool *results* must be fed back in the provider's exact expected shape, or the loop
  silently stalls.
- Keep tool logic out of the provider layer; the moment it leaks in, you can't reuse it.

## What carries forward

- The hand-written tool loop → Week 2's orchestrator/evaluator loops are this idea with
  *planning* on top.
- Structured outputs → Week 2 leans on schema-constrained calls for **every** pattern.
- The "thin typed LLM layer" instinct → becomes `llm.py` in Week 2.

Part of the IntellAIgent Agent Builder Curriculum, Week 1.
