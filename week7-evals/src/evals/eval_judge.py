"""Run the judge as a scorer alongside yesterday's code scorers."""

import asyncio

from fastmcp import Client

from evals.harness import EvalCase, Score, print_report, run_eval
from evals.judge import judge_thread
from evals.sut import mcp
from evals.eval_draft_thread import CASES  # reuse yesterday's draft cases


async def main() -> None:
    async with Client(mcp) as client:

        async def task(case: EvalCase):
            result = await client.call_tool("draft_thread", case.inputs)
            return result.data

        def _tweets(draft) -> list[str]:
            return draft.tweets if hasattr(draft, "tweets") else draft["tweets"]

        async def code_valid(case: EvalCase, draft) -> Score:
            want = case.inputs["num_tweets"]
            got = len(_tweets(draft))
            return Score(
                name="count_ok",
                value=1.0 if got == want else 0.0,
                detail=f"{got}/{want}",
            )

        async def judge_quality(case: EvalCase, draft) -> Score:
            text = "\n".join(_tweets(draft))
            verdict = await judge_thread(text, angle=case.inputs["angle"])
            return Score(
                name="judge",
                value=verdict.score / 5.0,
                detail=f"{verdict.score}/5",
            )

        results = await run_eval(CASES, task, [code_valid, judge_quality])
        print_report(results, ["count_ok", "judge"])

        # Print the judge's reasoning for one case so you SEE the "why".
        print(
            "\n(Judge reasoning is available per-call — inspect it, don't just trust the number.)"
        )


if __name__ == "__main__":
    asyncio.run(main())
