# Week 8 — Day 1: Scope, constraints, decision record

## The constraint came first (and improved the design)

Tapestry = Macquarie's code. Can't send to APIs without client AI policy, can't publish,
can't build an eval dataset from it. → Build against a representative Angular repo I own.
NOT a compromise: Week 7's eval discipline REQUIRES ground truth in my repo, so the
constraint and the methodology agree. Portable to the real repo as config, if policy allows.
→ Flagging data-handling before writing code IS the architect move. ACE evidence.

## Narrowed 3 products to 1

ticket→scaffold (3 risky surfaces, demo not tool) / docs (low value) / REVIEW A DIFF (one
input, one output, one surface). Picked review.

## Not redundant with Week 5's pattern-reviewer — it's the UPGRADE

subagent→MCP server; Claude-Code-only→CC+CI+any client; Python conv→Angular conv;
prompt that hopes→deterministic+LLM residue; never evaluated→eval'd; advisory→gate-able.
The capstone is the mature version of an old idea. Better story than novelty.

## The architecture finding

THE DETERMINISTIC LAYER ALREADY EXISTS: eslint + angular-eslint + @ngrx/eslint-plugin.
Don't rebuild an AST checker. Delegate mechanical → lint. LLM only for the residue lint
can't express (architectural judgment). Same lesson as Wk6 + Wk7. Third appearance.

## The decision record (the real deliverable)

USED: MCP server (Wk6, Python/FastMCP), deterministic-first (Wk6/7), evals + ground truth
(Wk7), tracing (Wk7), CC harness (Wk5).
NOT USED (the important half): no framework (shape = linear pipeline + 1 LLM call; Wk3's own
thesis says don't); NOT TypeScript despite reviewing TS (Wk4's language rule binds when you're
IN the stack — here I CALL it via subprocess; Python wins for eval/tracer reuse); no subagents
(single-purpose, 7x tokens for nothing); no judge in the product (a judge EVALUATES the
reviewer, isn't the reviewer); no RAG (8 rules fit in a prompt).
→ Exclusion list is LONGER than inclusion. That's the capstone. Using all 8 weeks proves
homework; correctly dropping 5 proves judgment.

## Built

- Representative repo: Angular 20 + NgRx 20 signals + AG Grid + eslint plugins (pinned to
  Tapestry's version; Angular 21 shipped Nov 2025, 22 ~May 2026 — enterprise lag is normal)
- Clean baseline committed (tomorrow's eval dataset = diffs against it)
- spike.py: proved Python → npx eslint --format json → structured findings. Riskiest
  integration spiked FIRST. 4 days is no time to discover a wrong assumption on day 3.
