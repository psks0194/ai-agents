"""A/B comparison of two draft_thread prompt variants, noise-aware.

For each case and each variant:
  1. draft the thread (once per variant per case)
  2. judge it K times, average the score (shrinks the noise floor)
  3. also run the deterministic code scorers
Then aggregate per variant and compare — refusing to over-read small deltas.
"""

import asyncio
import statistics

from evals.judge import judge_thread
from evals.variants import PROMPT_A, PROMPT_B, draft_with_prompt
from evals.eval_draft_thread import CASES  # reuse the draft dataset


JUDGE_SAMPLES = 3  # average this many judge calls per output to cut noise


async def score_output(tweets: list[str], angle: str, want_count: int) -> dict:
    """Score one drafted thread: averaged judge + deterministic checks."""
    text = "\n".join(tweets)

    # Average K judge samples to shrink run-to-run noise.
    judge_scores = []
    for _ in range(JUDGE_SAMPLES):
        verdict = await judge_thread(text, angle=angle)
        judge_scores.append(verdict.score)
    judge_mean = statistics.mean(judge_scores)
    judge_spread = max(judge_scores) - min(judge_scores)

    return {
        "judge_mean": judge_mean,
        "judge_spread": judge_spread,
        "count_ok": 1.0 if len(tweets) == want_count else 0.0,
        "within_280": 1.0 if all(len(t) <= 280 for t in tweets) else 0.0,
    }


async def run_variant(name: str, system_prompt: str) -> dict:
    """Run one variant across all cases, return aggregate scores."""
    per_case = []
    print(
        f"\n[{name}] drafting + judging {len(CASES)} cases "
        f"({JUDGE_SAMPLES} judge samples each)..."
    )

    for case in CASES:
        tweets = await draft_with_prompt(system_prompt, case.inputs)
        scores = await score_output(
            tweets, case.inputs["angle"], case.inputs["num_tweets"]
        )
        per_case.append(scores)
        print(
            f"  {case.id:<18} judge {scores['judge_mean']:.2f} "
            f"(spread {scores['judge_spread']}) "
            f"count_ok {scores['count_ok']:.0f} len_ok {scores['within_280']:.0f}"
        )

    return {
        "judge_mean": statistics.mean(s["judge_mean"] for s in per_case),
        "judge_stdev": statistics.pstdev(s["judge_mean"] for s in per_case),
        "count_ok": statistics.mean(s["count_ok"] for s in per_case),
        "within_280": statistics.mean(s["within_280"] for s in per_case),
        "max_spread": max(s["judge_spread"] for s in per_case),
    }


def interpret(a: dict, b: dict) -> None:
    """Compare A and B, refusing to over-read deltas within the noise."""
    delta = b["judge_mean"] - a["judge_mean"]

    # A conservative resolution floor: within-case judge spread bounds how
    # finely we can resolve a per-variant mean difference. Averaging K samples
    # shrinks it, but stay honest — treat small deltas as noise.
    noise_floor = max(a["max_spread"], b["max_spread"]) / (JUDGE_SAMPLES**0.5) / 5.0

    print("\n" + "=" * 52)
    print(
        f"  A judge mean: {a['judge_mean']:.3f}  (±{a['judge_stdev']:.2f} across cases)"
    )
    print(
        f"  B judge mean: {b['judge_mean']:.3f}  (±{b['judge_stdev']:.2f} across cases)"
    )
    print(f"  delta (B-A) : {delta:+.3f}")
    print(f"  ~noise floor: {noise_floor:.3f}  (judge scale 0-1)")
    print("  " + "-" * 48)

    if abs(delta) < noise_floor:
        print("  VERDICT: within the noise. No real difference detected.")
        print("           Do NOT ship B as an 'improvement' on this evidence.")
    elif delta > 0:
        print("  VERDICT: B looks genuinely better. Candidate improvement.")
        print("           Confirm with a bigger dataset before shipping.")
    else:
        print("  VERDICT: B looks genuinely worse. Reject this change.")

    # Deterministic scorers are exact — report regressions bluntly.
    if b["count_ok"] < a["count_ok"]:
        print(f"  ⚠ count_ok regressed: {a['count_ok']:.0%} → {b['count_ok']:.0%}")
    if b["within_280"] < a["within_280"]:
        print(
            f"  ⚠ within_280 regressed: {a['within_280']:.0%} → {b['within_280']:.0%}"
        )


async def main() -> None:
    a = await run_variant("A: baseline", PROMPT_A)
    b = await run_variant("B: concrete-opener", PROMPT_B)
    interpret(a, b)


if __name__ == "__main__":
    asyncio.run(main())
