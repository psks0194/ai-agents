"""A regression gate: fast, deterministic pass/fail on draft_thread validity.

Run this before shipping a change (or in CI). It uses ONLY deterministic scorers
(no judge) because a gate needs certainty, not noisy signal. Exits non-zero on
regression so it can block a commit/deploy — the quality analogue of a hook.
"""

import asyncio
import sys

from fastmcp import Client

from evals.eval_draft_thread import CASES
from evals.sut import mcp


# The bar the current server must clear. Deterministic scorers only.
THRESHOLDS = {
    "count_ok": 1.0,  # every thread must have the requested tweet count
    "within_280": 1.0,  # every tweet must be within length
    "passes_voice": 0.75,  # at least 75% pass our own voice linter
}


async def main() -> None:
    async with Client(mcp) as client:
        results = {"count_ok": [], "within_280": [], "passes_voice": []}

        for case in CASES:
            draft = (await client.call_tool("draft_thread", case.inputs)).data
            tweets = draft.tweets if hasattr(draft, "tweets") else draft["tweets"]

            results["count_ok"].append(len(tweets) == case.inputs["num_tweets"])
            results["within_280"].append(all(len(t) <= 280 for t in tweets))

            vr = (
                await client.call_tool("check_voice", {"text": "\n".join(tweets)})
            ).data
            passed = vr.passed if hasattr(vr, "passed") else vr["passed"]
            results["passes_voice"].append(passed)

        print("Regression gate — deterministic scorers\n")
        failed = False
        for name, threshold in THRESHOLDS.items():
            rate = sum(results[name]) / len(results[name])
            ok = rate >= threshold
            failed = failed or not ok
            mark = "PASS" if ok else "FAIL"
            print(f"  [{mark}] {name:<14} {rate:.0%}  (need {threshold:.0%})")

        if failed:
            print("\n❌ Regression gate FAILED — do not ship.")
            sys.exit(1)
        print("\n✅ Regression gate passed.")


if __name__ == "__main__":
    asyncio.run(main())
