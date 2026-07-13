"""A multi-step content pipeline, fully traced.

Stages: generate an angle from a headline → draft the thread → lint the voice.
Every stage is a span; LLM calls are child spans with token counts. When the
final output is bad, the trace tells you WHICH stage drifted.
"""

import asyncio

from anthropic import AsyncAnthropic
from fastmcp import Client

from evals.config import settings
from evals.sut import mcp
from evals.tracer import Tracer
from evals.variants import PROMPT_A, draft_with_prompt


async def llm_call(tracer: Tracer, name: str, system: str, user: str) -> str:
    """One traced LLM call: model, latency, and token counts on the span."""
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    with tracer.span(name, model="claude-haiku-4-5") as s:
        resp = await client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = resp.content[0].text.strip()
        s.attributes.update(
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            output=text[:200],  # a preview; full text would go to events in prod
        )
        return text


async def run_pipeline(headline: str, summary: str) -> None:
    tracer = Tracer("content-pipeline")

    try:
        # Stage 1: angle
        with tracer.span("angle", headline=headline) as s:
            angle = await llm_call(
                tracer,
                "llm.angle",
                system=(
                    "You find sharp practitioner-contrarian angles. Return ONE "
                    "declarative sentence stating the angle. No hype words."
                ),
                user=f"Headline: {headline}\nSummary: {summary}",
            )
            s.attributes["angle"] = angle

        # Stage 2: draft (reuses the Day 3 variant function, traced around it)
        with tracer.span("draft", num_tweets=6) as s:
            tweets = await draft_with_prompt(
                PROMPT_A,
                {
                    "source_title": headline,
                    "source_summary": summary,
                    "angle": angle,
                    "num_tweets": 6,
                },
            )
            s.attributes.update(tweet_count=len(tweets), output="\n".join(tweets)[:200])

        # Stage 3: voice lint via the MCP tool
        with tracer.span("check_voice") as s:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "check_voice", {"text": "\n".join(tweets)}
                )
                report = result.data
                passed = (
                    report.passed if hasattr(report, "passed") else report["passed"]
                )
                count = (
                    report.issue_count
                    if hasattr(report, "issue_count")
                    else report["issue_count"]
                )
                s.attributes.update(passed=passed, issue_count=count)

    finally:
        tracer.finish()
        path = tracer.save()
        print("\n=== TRACE ===")
        tracer.print_tree()
        print(f"\nSaved: {path}")


if __name__ == "__main__":
    asyncio.run(
        run_pipeline(
            headline="Most AI eval dashboards measure the wrong thing",
            summary="Green metrics that don't track real quality give false confidence.",
        )
    )
