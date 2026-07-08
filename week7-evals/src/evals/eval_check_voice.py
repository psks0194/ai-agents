"""Eval: does check_voice flag exactly the right terms? (detection task)

Ground-truth dataset. We compute global (micro-averaged) precision, recall, and
F1 from per-case true/false positives and false negatives.
"""

import asyncio

from fastmcp import Client

from evals.harness import EvalCase, Score, run_eval
from evals.sut import mcp


CASES: list[EvalCase] = [
    EvalCase(
        id="hype-heavy",
        inputs={
            "text": "This will revolutionize your workflow and seamlessly unlock synergy."
        },
        expected={"terms": {"revolutionize", "seamlessly", "unlock", "synergy"}},
    ),
    EvalCase(
        id="clean",
        inputs={
            "text": "I measured it: the harness cost 7x tokens and saved 40 files of context."
        },
        expected={"terms": set()},
    ),
    EvalCase(
        id="hedges",
        inputs={"text": "I think this is arguably the best approach, sort of."},
        expected={"terms": {"i think", "arguably", "sort of"}},
    ),
    EvalCase(
        id="intensifiers",
        inputs={"text": "This is a very really deeply important point."},
        expected={"terms": {"very", "really", "deeply"}},
    ),
    EvalCase(
        id="mixed",
        inputs={"text": "Leverage this cutting-edge tool to truly elevate results."},
        expected={"terms": {"leverage", "cutting-edge", "truly", "elevate"}},
    ),
    # The important one: a substring that must NOT false-positive.
    # "lever" should not trip the "leverage" rule.
    EvalCase(
        id="tricky-substring",
        inputs={"text": "The lever on the machine is broken."},
        expected={"terms": set()},
    ),
]


async def main() -> None:
    async with Client(mcp) as client:

        async def task(case: EvalCase) -> set[str]:
            result = await client.call_tool(
                "check_voice", {"text": case.inputs["text"]}
            )
            report = result.data
            issues = report.issues if hasattr(report, "issues") else report["issues"]
            return {(i.term if hasattr(i, "term") else i["term"]) for i in issues}

        async def confusion(case: EvalCase, flagged: set[str]) -> list[Score]:
            expected: set[str] = case.expected["terms"]
            tp = len(flagged & expected)
            fp = len(flagged - expected)
            fn = len(expected - flagged)
            detail = f"tp{tp} fp{fp} fn{fn}"
            return [
                Score(name="tp", value=tp, detail=detail),
                Score(name="fp", value=fp),
                Score(name="fn", value=fn),
            ]

        results = await run_eval(CASES, task, [confusion])

        # Global (micro) precision / recall / F1 from summed confusion counts.
        total = {"tp": 0, "fp": 0, "fn": 0}
        for r in results:
            for s in r.scores:
                if s.name in total:
                    total[s.name] += int(s.value)

        tp, fp, fn = total["tp"], total["fp"], total["fn"]
        precision = tp / (tp + fp) if (tp + fp) else 1.0
        recall = tp / (tp + fn) if (tp + fn) else 1.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )

        print("\ncheck_voice detection eval")
        for r in results:
            det = next((s.detail for s in r.scores if s.name == "tp"), "")
            print(f"  {r.case_id:<20} {det}  {r.output_repr}")
        print(f"\n  precision {precision:.1%} | recall {recall:.1%} | F1 {f1:.2f}")
        print(f"  (tp={tp} fp={fp} fn={fn})")


if __name__ == "__main__":
    asyncio.run(main())
