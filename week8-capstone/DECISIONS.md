# ng-review — Architecture Decision Record

## Problem

Review an Angular diff against team conventions (SignalStore, AG Grid, component
library usage) and return prioritized, actionable findings. Consumable from Claude
Code during development and from CI as a gate.

## Constraint (decided first)

Client source cannot leave the client's environment or enter my repo. Built and
evaluated against a representative Angular app I own, mirroring the target's shape.
Portable to the real repo as a config change IF client AI policy permits.

## USED — and why

- **MCP server (Week 6), Python/FastMCP.** The reason this beats a Claude Code
  subagent: one server, consumable from Claude Code, CI, and any client. Tools,
  not prompts.
- **Deterministic-first (Weeks 6, 7).** ESLint + angular-eslint + @ngrx/eslint-plugin
  do the mechanical checks. The LLM handles only the residue lint can't express.
- **Evals (Week 7).** Ground-truth dataset of known-bad diffs. Deterministic scorers
  (did it find the planted violation? did it hallucinate one?) = precision/recall.
- **Tracing (Week 7).** Spans per stage so a bad review is diagnosable.
- **Claude Code harness (Week 5).** Consumed via my existing MCP install path.

## NOT USED — and why (the important half)

- **No agent framework (Weeks 3-4).** The workflow shape is: run lint → collect
  residue → one LLM call → structured output. That is a linear pipeline with a
  single model call. No cycles, no handoffs, no multi-agent state. LangGraph would
  be ceremony; a framework dep for one call is negative value. Week 3's own thesis
  ("framework choice is workflow shape") says: this shape doesn't need one.
- **Not TypeScript, despite reviewing TypeScript.** Week 4's rule is "workflow shape
  AND language of your stack." That rule binds when you're _in_ the stack. Here the
  server _calls_ the stack — eslint is a subprocess either way. Python wins because
  the eval harness and tracer (Week 7) are Python and reuse is the bigger prize than
  language homogeneity. Revisit if this ever needs deep in-process AST work.
- **No subagents (Week 5).** Single-purpose service, not multi-context exploration.
  ~7x tokens for no isolation benefit.
- **No LLM-as-judge in the product.** A judge EVALUATES the reviewer; it isn't the
  reviewer. Keeping those roles separate is the point.
- **No RAG (Week 2).** Conventions are a short, fixed document. Retrieval over eight
  rules is over-engineering; put them in the prompt.
