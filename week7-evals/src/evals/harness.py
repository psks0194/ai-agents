"""A from-scratch eval harness: dataset + task + scorer(s) -> results.

Deliberately tiny and readable — the point is to see the primitives, not hide
them behind a framework. For each case: run the task, run each scorer, collect.
Both tasks and scorers are async so LLM-as-judge scorers drop in later (Day 2).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    """One case: an id, the inputs to the task, and optional expected data."""

    id: str
    inputs: dict[str, Any]
    expected: dict[str, Any] = Field(default_factory=dict)


class Score(BaseModel):
    """One scorer's result on one case. value is 0.0-1.0 (or 0/1 for pass/fail)."""

    name: str
    value: float
    detail: str = ""


class CaseResult(BaseModel):
    """Everything about one case after running and scoring."""

    case_id: str
    output_repr: str = ""
    scores: list[Score] = Field(default_factory=list)
    error: str = ""


# A task runs the system under test on a case and returns an output.
Task = Callable[[EvalCase], Awaitable[Any]]
# A scorer maps (case, output) -> Score or list[Score]. Async for future judges.
Scorer = Callable[[EvalCase, Any], Awaitable["Score | list[Score]"]]


async def run_eval(
    dataset: list[EvalCase],
    task: Task,
    scorers: list[Scorer],
) -> list[CaseResult]:
    """Run every case through the task and all scorers. Errors are captured,
    never fatal — one bad case shouldn't sink the whole run."""
    results: list[CaseResult] = []

    for case in dataset:
        try:
            output = await task(case)
        except Exception as e:
            results.append(CaseResult(case_id=case.id, error=f"task failed: {e}"))
            continue

        case_scores: list[Score] = []
        for scorer in scorers:
            try:
                out = await scorer(case, output)
                case_scores.extend(out if isinstance(out, list) else [out])
            except Exception as e:
                case_scores.append(Score(name="scorer_error", value=0.0, detail=str(e)))

        results.append(
            CaseResult(
                case_id=case.id,
                output_repr=str(output)[:160],
                scores=case_scores,
            )
        )

    return results


def pass_rate(results: list[CaseResult], scorer_name: str) -> float:
    """Mean of a boolean/0-1 scorer across cases that produced it."""
    vals = [s.value for r in results for s in r.scores if s.name == scorer_name]
    return sum(vals) / len(vals) if vals else 0.0


def print_report(results: list[CaseResult], scorer_names: list[str]) -> None:
    """Human-readable per-case table plus aggregate pass rates."""
    print(f"\n{'case':<22} " + " ".join(f"{n:<16}" for n in scorer_names))
    print("-" * (22 + 17 * len(scorer_names)))
    for r in results:
        if r.error:
            print(f"{r.case_id:<22} ERROR: {r.error}")
            continue
        by_name = {s.name: s for s in r.scores}
        cells = []
        for n in scorer_names:
            s = by_name.get(n)
            cells.append(f"{s.value:.2f} {s.detail}"[:16] if s else "-")
        print(f"{r.case_id:<22} " + " ".join(f"{c:<16}" for c in cells))

    errors = sum(1 for r in results if r.error)
    print("-" * (22 + 17 * len(scorer_names)))
    for n in scorer_names:
        print(f"  {n} pass rate: {pass_rate(results, n):.1%}")
    if errors:
        print(f"  errors: {errors}/{len(results)}")
