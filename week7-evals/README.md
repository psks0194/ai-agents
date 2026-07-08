# week7-evals

We spent six weeks building the agent; now we **measure it**. This week is a
from-scratch **eval harness** — dataset + task + scorer(s) → results — pointed at
the week-6 content-ops MCP server as its **system under test**. No eval framework,
no green-dashboard theater: just the primitives, so you can see exactly what a
score is made of.

The throughline from the whole curriculum: an agent is a loop (`call → tool →
result → call → final answer`). An eval wraps that loop — run the system on a
known case, score the output against something you can defend. Two kinds of
scoring show up here: **detection** against ground truth (precision/recall/F1)
and **property checks** on subjective output (validity you can assert in code).
LLM-as-judge scoring is deliberately deferred to Day 2 — the harness is already
async so judges drop in without changes.

## Status

**Day 1 — 2026-07-08**

- ✅ Harness — tiny, readable runner: `EvalCase` / `Score` / `CaseResult`, async `run_eval`, per-case error capture, `pass_rate` + `print_report` helpers (`harness.py`)
- ✅ System under test — imports the week-6 server (`intellaigent_mcp.server.mcp`) via a path insert anchored to the repo root, driven in-process through a `fastmcp.Client` (`sut.py`)
- ✅ `eval_check_voice` — **detection** eval with a ground-truth dataset; micro-averaged precision/recall/F1 from summed tp/fp/fn, including a `tricky-substring` case that guards against "lever" false-positiving on the "leverage" rule (`eval_check_voice.py`)
- ✅ `eval_draft_thread` — **property checks** on subjective LLM output: correct tweet count, every tweet ≤ 280 chars, and the draft passes our own `check_voice` linter (scorer composition). One real Haiku call per case (`eval_draft_thread.py`)
- ✅ Packaging — `hatchling` build config so the `evals` package installs editable via `uv sync` (run evals with plain `-m`, no `PYTHONPATH`)

## Layout

```
src/evals/
  harness.py             # the eval primitives: EvalCase, Score, run_eval, print_report
  sut.py                 # locates & imports the week-6 server as the system under test
  eval_check_voice.py    # detection eval — ground truth, precision/recall/F1
  eval_draft_thread.py   # property-check eval — validity of subjective output
main.py                  # placeholder entrypoint (unused by the evals)
```

## Setup

```bash
uv sync   # installs deps + this project (editable) into the week's .venv
```

`eval_draft_thread` makes real LLM calls, so the week-6 server needs
`ANTHROPIC_API_KEY` from the **shared repo-root `.env`** (week 6's `config.py`
reads that file). `eval_check_voice` is fully deterministic and needs no key.

`sut.py` imports the week-6 server from `../week6-mcp-server/src`, resolved
relative to the repo root — that sibling week must be present on disk.

## Running

```bash
uv run python -m evals.eval_check_voice    # deterministic, no API key
uv run python -m evals.eval_draft_thread   # one Haiku call per case, needs the key
```

Each prints a per-case table and its aggregate metrics — precision/recall/F1 for
the detection eval, per-property pass rates for the draft eval.
