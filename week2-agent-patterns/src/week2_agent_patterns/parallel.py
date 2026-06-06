"""Parallelization pattern: decompose, fan out concurrently, synthesize.

This is the 'sectioning' flavor of parallelization from the Anthropic essay.
Uses asyncio.gather for real concurrency — slowest sub-question dictates total time,
not the sum.
"""

import asyncio
import time

from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from week2_agent_patterns.config import settings
from week2_agent_patterns.llm import call_anthropic


console = Console()


# ============================================================
# Stage 1: Decomposer (sync — one quick call)
# ============================================================


class SubQuestions(BaseModel):
    """The decomposer's output: 3-5 sub-questions covering the full question."""

    questions: list[str] = Field(
        description=(
            "Between 3 and 5 sub-questions that together cover the user's full question. "
            "Each should be focused enough to answer in 2-3 paragraphs. "
            "They should be independent — one's answer shouldn't depend on another's."
        ),
        min_length=3,
        max_length=5,
    )


DECOMPOSER_SYSTEM = (
    "You decompose research questions into independent sub-questions. "
    "Aim for 3-5 sub-questions that together cover the original. "
    "They must be independent — order shouldn't matter. "
    "If you can't decompose cleanly, that's fine — return fewer sub-questions."
)


def decompose(question: str) -> SubQuestions:
    """Stage 1: take a research question, return sub-questions."""
    return call_anthropic(
        prompt=f"Research question to decompose:\n\n{question}",
        schema=SubQuestions,
        system=DECOMPOSER_SYSTEM,
    )


# ============================================================
# Stage 2: Workers (async — concurrent calls)
# ============================================================

WORKER_SYSTEM = (
    "Answer the sub-question precisely. Be concrete: name specific tools, "
    "people, projects, dates. Avoid hedging. 2-3 short paragraphs. "
    "If you're uncertain, say so explicitly rather than fudging."
)


async def worker(sub_question: str, idx: int) -> tuple[int, str, str]:
    """One async worker that answers a single sub-question.

    Returns (index, sub_question, answer) so we can preserve order
    even when results come back out of order.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=WORKER_SYSTEM,
        messages=[{"role": "user", "content": sub_question}],
    )

    answer = "".join(b.text for b in response.content if b.type == "text")
    return idx, sub_question, answer


async def run_workers_parallel(sub_questions: list[str]) -> list[tuple[str, str]]:
    """Fire all workers concurrently. Return (sub_q, answer) pairs in order."""
    tasks = [worker(sq, i) for i, sq in enumerate(sub_questions)]
    results = await asyncio.gather(*tasks)

    # Sort by index to preserve the original sub-question order
    results.sort(key=lambda t: t[0])
    return [(sq, ans) for (_, sq, ans) in results]


# ============================================================
# Stage 3: Synthesizer (sync — final synthesis)
# ============================================================

SYNTHESIZER_SYSTEM = (
    "You synthesize multiple research findings into one coherent response. "
    "Don't just concatenate the findings — weave them. Cite specific details "
    "from the sub-answers. Lead with the most important insight. "
    "End with one practical takeaway. ~400 words, prose, no headings."
)


def synthesize(original_question: str, findings: list[tuple[str, str]]) -> str:
    """Stage 3: combine all sub-answers into the final response."""
    findings_text = "\n\n".join(
        f"Sub-question: {sq}\nFinding:\n{ans}" for sq, ans in findings
    )

    prompt = (
        f"Original question: {original_question}\n\n"
        f"Sub-answers researched in parallel:\n\n{findings_text}\n\n"
        "Synthesize a final response to the original question."
    )

    from week2_agent_patterns.llm import call_text_anthropic

    return call_text_anthropic(
        prompt=prompt,
        system=SYNTHESIZER_SYSTEM,
        max_tokens=2048,
    )


# ============================================================
# Compose the pattern
# ============================================================


async def run_parallel(question: str) -> str:
    """Full parallelization pipeline."""
    console.print(f"\n[bold]Question:[/bold] {question}\n")

    # Stage 1: decompose
    console.print("[dim]Stage 1: Decomposing into sub-questions...[/dim]")
    sub_qs = decompose(question)
    console.print(
        Panel(
            "\n".join(f"{i + 1}. {q}" for i, q in enumerate(sub_qs.questions)),
            title=f"Decomposed into {len(sub_qs.questions)} sub-questions",
            border_style="cyan",
        )
    )

    # Stage 2: fan out workers concurrently
    console.print(
        f"\n[dim]Stage 2: Firing {len(sub_qs.questions)} workers concurrently...[/dim]"
    )
    start = time.perf_counter()
    findings = await run_workers_parallel(sub_qs.questions)
    elapsed = time.perf_counter() - start
    console.print(f"[dim]All workers finished in {elapsed:.2f}s[/dim]\n")

    for i, (sq, ans) in enumerate(findings):
        console.print(
            Panel(
                ans,
                title=f"Worker {i + 1}: {sq}",
                border_style="magenta",
            )
        )

    # Stage 3: synthesize
    console.print("\n[dim]Stage 3: Synthesizing final answer...[/dim]")
    final = synthesize(question, findings)
    console.print(
        Panel(
            Markdown(final),
            title="Final synthesized answer",
            border_style="green",
        )
    )

    return final


def main() -> None:
    question = "What should I know about MCP if I'm building agents in 2026?"
    asyncio.run(run_parallel(question))


if __name__ == "__main__":
    main()
