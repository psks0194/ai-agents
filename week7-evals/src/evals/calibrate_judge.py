"""Calibrate the judge against human labels.

Do the judge's scores agree with mine? Metrics:
- exact agreement, within-1 agreement, mean absolute error (absolute accuracy)
- Pearson correlation (does it move WITH me?)
- good/bad SEPARATION (does it reliably rank good above bad?)

The decision this produces: trust the judge for absolute grading, only for
relative comparison, or not at all.
"""

import asyncio

from pydantic import BaseModel

from evals.judge import judge_thread


class Labeled(BaseModel):
    id: str
    angle: str
    thread: str
    human: int  # YOUR score 1-5 — adjust these to your real judgment


# Starter set — ADJUST the human labels to your taste, and add your own.
LABELED: list[Labeled] = [
    Labeled(
        id="sharp",
        angle="harness cost",
        human=5,
        thread=(
            "1/ I built a 5-layer Claude Code harness and measured it.\n"
            "2/ On a real multi-week task it saved ~40 files of context.\n"
            "3/ It also cost ~7x the tokens. Both are true.\n"
            "4/ On a one-line fix, all that scaffolding is pure ceremony.\n"
            "5/ The skill isn't building the harness. It's knowing when it clears the threshold."
        ),
    ),
    Labeled(
        id="good",
        angle="mcp determinism",
        human=4,
        thread=(
            "1/ Built an MCP server this week. The surprise: how little AI belonged in it.\n"
            "2/ My two best tools don't think. They resolve tokens and enforce rules.\n"
            "3/ The client's model is the brain. The server is reliable hands.\n"
            "4/ Determinism is why I could test it in under a second."
        ),
    ),
    Labeled(
        id="generic",
        angle="agent frameworks",
        human=3,
        thread=(
            "1/ Choosing an agent framework is an important decision.\n"
            "2/ There are several good options with different strengths.\n"
            "3/ It really depends on your use case and team.\n"
            "4/ Try a few and see what fits best."
        ),
    ),
    Labeled(
        id="hedgy",
        angle="evals",
        human=2,
        thread=(
            "1/ Evals are arguably kind of important for AI systems I think.\n"
            "2/ There are many ways to maybe approach them.\n"
            "3/ It sort of depends on what you're trying to do.\n"
            "4/ Testing is generally a good idea in most cases."
        ),
    ),
    Labeled(
        id="hype",
        angle="ai agents",
        human=1,
        thread=(
            "1/ AI agents will revolutionize how we work! 🚀\n"
            "2/ Unlock seamless productivity and supercharge your workflow.\n"
            "3/ This game-changing tech is truly the future.\n"
            "4/ Leverage cutting-edge agents to elevate everything!"
        ),
    ),
    Labeled(
        id="good2",
        angle="the moat",
        human=4,
        thread=(
            "1/ 'The moat moved up the stack' is easy to say and hard to show.\n"
            "2/ Concretely: the model is the commodity. The scaffolding around it isn't.\n"
            "3/ I measured a harness and a server this month to test that claim.\n"
            "4/ The durable value was the boring, testable, deterministic part."
        ),
    ),
]


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (vx * vy) if vx and vy else 0.0


async def main() -> None:
    human, machine = [], []
    print("Calibrating judge against human labels...\n")
    print(f"  {'id':<10} {'human':<6} {'judge':<6} {'delta':<6}")
    print("  " + "-" * 30)

    for item in LABELED:
        verdict = await judge_thread(item.thread, angle=item.angle)
        human.append(item.human)
        machine.append(verdict.score)
        print(
            f"  {item.id:<10} {item.human:<6} {verdict.score:<6} {verdict.score - item.human:+d}"
        )

    n = len(human)
    exact = sum(1 for h, m in zip(human, machine) if h == m) / n
    within1 = sum(1 for h, m in zip(human, machine) if abs(h - m) <= 1) / n
    mae = sum(abs(h - m) for h, m in zip(human, machine)) / n
    corr = _pearson([float(h) for h in human], [float(m) for m in machine])

    good = [m for h, m in zip(human, machine) if h >= 4]
    bad = [m for h, m in zip(human, machine) if h <= 2]
    good_mean = sum(good) / len(good) if good else 0
    bad_mean = sum(bad) / len(bad) if bad else 0

    print("\n  --- calibration ---")
    print(f"  exact agreement : {exact:.0%}")
    print(f"  within-1        : {within1:.0%}")
    print(f"  mean abs error  : {mae:.2f} (on a 1-5 scale)")
    print(f"  correlation     : {corr:+.2f}")
    print(
        f"  separation      : good avg {good_mean:.1f} vs bad avg {bad_mean:.1f} "
        f"(gap {good_mean - bad_mean:+.1f})"
    )

    print("\n  --- verdict ---")
    if corr >= 0.7 and mae <= 1.0:
        print("  Trustworthy for ABSOLUTE grading (tracks you closely).")
    elif good_mean - bad_mean >= 1.5:
        print("  Trust for RELATIVE comparison only (separates good/bad, but")
        print("  absolute numbers are noisy — use it to compare A vs B, not to grade).")
    else:
        print("  DO NOT trust this judge yet. Revise the rubric and recalibrate.")


if __name__ == "__main__":
    asyncio.run(main())
