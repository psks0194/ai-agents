"""Eval: does draft_thread produce VALID threads? (property checks on subjective output)

No ground-truth 'correct thread' exists — but validity is code-checkable:
- correct tweet count
- passes our own check_voice linter (composition!)
- every tweet within 280 chars
This is deterministic scoring of a subjective output. Quality judgment is Day 2.

NOTE: each case makes one real LLM call (Haiku). Keep the dataset small.
Requires ANTHROPIC_API_KEY available to the server (see below).
"""

import asyncio

from fastmcp import Client

from evals.harness import EvalCase, Score, print_report, run_eval
from evals.sut import mcp


CASES: list[EvalCase] = [
    EvalCase(
        id="harness-thesis",
        inputs={
            "source_title": "Most AI harness posts skip the cost",
            "source_summary": "A five-layer Claude Code setup, measured honestly.",
            "angle": "The harness pays off only above a complexity threshold.",
            "num_tweets": 6,
        },
    ),
    EvalCase(
        id="mcp-determinism",
        inputs={
            "source_title": "I built an MCP server",
            "source_summary": "Content-ops server with tools, resources, prompts.",
            "angle": "The best MCP servers keep the intelligence in the client.",
            "num_tweets": 5,
        },
    ),
    EvalCase(
        id="eval-theater",
        inputs={
            "source_title": "Evals can be theater",
            "source_summary": "A green dashboard measuring the wrong thing.",
            "angle": "A scorer that always passes tells you nothing.",
            "num_tweets": 7,
        },
    ),
    EvalCase(
        id="framework-shape",
        inputs={
            "source_title": "Which agent framework",
            "source_summary": "Four frameworks, two languages, measured.",
            "angle": "Framework choice is workflow shape, not capability.",
            "num_tweets": 6,
        },
    ),
]


async def main() -> None:
    async with Client(mcp) as client:

        async def task(case: EvalCase):
            result = await client.call_tool("draft_thread", case.inputs)
            return result.data  # ThreadDraft (or dict)

        def _tweets(draft) -> list[str]:
            return draft.tweets if hasattr(draft, "tweets") else draft["tweets"]

        async def correct_count(case: EvalCase, draft) -> Score:
            want = case.inputs["num_tweets"]
            got = len(_tweets(draft))
            return Score(
                name="correct_count",
                value=1.0 if got == want else 0.0,
                detail=f"{got}/{want}",
            )

        async def passes_voice(case: EvalCase, draft) -> Score:
            joined = "\n".join(_tweets(draft))
            vr = await client.call_tool("check_voice", {"text": joined})
            report = vr.data
            passed = report.passed if hasattr(report, "passed") else report["passed"]
            return Score(name="passes_voice", value=1.0 if passed else 0.0)

        async def within_280(case: EvalCase, draft) -> Score:
            ok = all(len(t) <= 280 for t in _tweets(draft))
            return Score(name="within_280", value=1.0 if ok else 0.0)

        scorers = [correct_count, passes_voice, within_280]
        results = await run_eval(CASES, task, scorers)
        print_report(results, ["correct_count", "passes_voice", "within_280"])


if __name__ == "__main__":
    asyncio.run(main())
