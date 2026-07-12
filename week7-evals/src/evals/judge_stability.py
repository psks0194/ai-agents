"""Demonstrate run-to-run inconsistency: judge ONE thread N times, at temp 0.

Uses a deliberately BORDERLINE thread — borderline cases are where a judge is
noisiest, which is exactly where you'd be relying on it to break ties.
"""

import asyncio
import statistics

from evals.judge import judge_thread


# A deliberately middling thread: an angle, but generic and slightly hedgy.
# This is the ~3/5 zone where the judge should waver most.
BORDERLINE_THREAD = """1/ AI agents are becoming a big deal for developers.
2/ There are a lot of frameworks out there now and it can be hard to choose.
3/ I think the best one really depends on your specific use case honestly.
4/ Some are better for simple tasks and others for more complex workflows.
5/ The key is to just try a few and see what works for your team.
6/ Agents are the future and worth learning about now."""


async def main() -> None:
    n = 5
    print(f"Judging the SAME borderline thread {n} times at temperature 0...\n")

    scores: list[int] = []
    for i in range(n):
        verdict = await judge_thread(
            BORDERLINE_THREAD, angle="choosing an agent framework"
        )
        scores.append(verdict.score)
        print(f"  run {i + 1}: score={verdict.score}  on_voice={verdict.on_voice}")
        print(f"          reason: {verdict.reasoning[:90]}...")

    spread = max(scores) - min(scores)
    print(f"\n  scores: {scores}")
    print(
        f"  mean {statistics.mean(scores):.2f} | "
        f"stdev {statistics.pstdev(scores):.2f} | spread {spread}"
    )
    if spread == 0:
        print(
            "  → Stable on THIS case. Try a lower/nonzero temperature or a more ambiguous thread."
        )
    else:
        print(
            f"  → The 'same' measurement varies by {spread} point(s). This is the noise floor."
        )


if __name__ == "__main__":
    asyncio.run(main())
