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
Day 2 adds the third kind — **LLM-as-judge** scoring for subjective quality you
can't assert in code — and treats the judge itself as an instrument to be
calibrated and stress-tested, not trusted on sight.

## Status

**Day 2 — 2026-07-12**

- ✅ Judge — LLM-as-judge for thread quality built to fight known failure modes: an **anchored 1-5 rubric** (each level described) against score-clustering, **reasoning before score**, structured `JudgeVerdict` output, temperature 0, and defensive JSON parsing so one malformed response can't kill a run (`judge.py`)
- ✅ Calibration — scores the judge against **human labels** (a 6-thread set spanning 1-5): exact/within-1 agreement, MAE, Pearson correlation, and good-vs-bad separation, then prints a verdict — trust it for absolute grading, relative comparison only, or not yet (`calibrate_judge.py`)
- ✅ Stability — judges the *same* borderline thread N times at temp 0 to expose the run-to-run **noise floor** (spread/stdev); borderline cases are where a judge wavers most and where you'd lean on it to break ties (`judge_stability.py`)
- ✅ `eval_judge` — drops the judge in as a scorer **alongside** yesterday's code scorers, reusing the Day 1 draft cases: a deterministic `count_ok` next to a subjective `judge` score, proving the async harness takes judges with no changes (`eval_judge.py`)
- ✅ Config — local `pydantic-settings` for the judge's `anthropic_api_key` + `judge_model` (`config.py`)

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
  judge.py               # LLM-as-judge: anchored rubric, reasoning-first, structured verdict
  calibrate_judge.py     # judge vs human labels — agreement, correlation, separation
  judge_stability.py     # same thread N times — expose the temp-0 noise floor
  eval_judge.py          # judge as a scorer next to the Day 1 code scorers
  config.py              # judge model + API key (pydantic-settings)
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

# Day 2 — LLM-as-judge (all need the key)
uv run python -m evals.calibrate_judge     # judge vs human labels — agreement, correlation
uv run python -m evals.judge_stability     # same thread ×5 — the temp-0 noise floor
uv run python -m evals.eval_judge          # judge as a scorer beside the code scorers
```

Each prints a per-case table and its aggregate metrics — precision/recall/F1 for
the detection eval, per-property pass rates for the draft eval, and for Day 2 the
judge's agreement/correlation/separation and its run-to-run spread.

The judge calls the Anthropic API directly (not through the week-6 server), so
Day 2 reads `ANTHROPIC_API_KEY` and an optional `JUDGE_MODEL` via this project's
own `config.py` — set `JUDGE_MODEL` to your account's current Sonnet-tier model
string (the default is `claude-sonnet-4-5`).
