# Week 5 — Claude Code extensibility

Building the harness around the model: CLAUDE.md, skills, **subagents**, hooks, MCP, plugins.

## The extensibility stack

| Layer       | Loads        | Purpose                                          |
| ----------- | ------------ | ------------------------------------------------ |
| CLAUDE.md   | every session | always-true + short context                     |
| Skills      | on demand    | repeatable playbooks with an explicit trigger    |
| **Subagents** | on demand  | **own context window — isolation + parallelism** |
| Hooks       | deterministic | enforcement the model can't be trusted to do    |
| MCP         | on demand    | external systems                                 |
| Plugins     | bundle       | package all of the above to share                |

## Day 2 — Subagents

Subagents run in their **own context window**, so they keep the main session clean
(fan out a noisy search, get back only the conclusion) and run **in parallel**.
Defined as Markdown files in `.claude/agents/` with YAML frontmatter:
`name`, `description` (drives auto-invocation — write *what AND when*), `tools`
(least-privilege), and `model`.

Two subagents built for this repo (live in the repo-root `.claude/agents/`):

### `curriculum-explorer`

- **Job:** find/understand how something was implemented across the multi-week repo
  ("where did I do the evaluator-optimizer loop", "how did I handle MAX_ITERATIONS").
- **Tools:** `Read, Grep, Glob` (read-only).
- **Model:** Haiku — search-and-summarize, no heavy reasoning needed.
- **Returns:** tight **Answer / Where (path:line) / Notes** summary — findings, not
  file dumps — so the main session avoids reading every file itself.

### `pattern-reviewer`

- **Job:** review recent changes against this repo's hard-won conventions (MAX_ITERATIONS
  caps, pydantic-settings config, no-secrets, naming, Haiku-default, typed pipeline
  boundaries).
- **Tools:** `Read, Grep, Glob, Bash` (read-only review; uses `git diff`).
- **Model:** Sonnet — multi-file review with judgment justifies the step up.
- **Returns:** feedback by priority — **Critical / Convention / Suggestion** — each with
  `file:line` and a concrete fix.

These were exercised together: parallel `curriculum-explorer` fan-out (e.g. mapping
cost-control across every week) synthesized in the main session, with `pattern-reviewer`
auditing the diff.

## Why it matters

The harness is the moat moving up the stack — in my own workflow. The value isn't Claude
writing code, it's the scaffolding that makes it write the *right* code my way, every
time, without re-explaining. Subagents add a new axis: do the noisy work *elsewhere* and
bring back only what matters.
