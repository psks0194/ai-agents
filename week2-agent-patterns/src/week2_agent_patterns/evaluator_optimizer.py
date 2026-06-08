"""Evaluator-optimizer pattern: generate, evaluate, revise, loop until shippable.

The drafter and evaluator are decoupled LLMs. The drafter sees its own previous
draft + the evaluator's specific feedback when revising — that's what makes the
loop actually improve quality.

Hard MAX_ITERATIONS prevents the evaluator from being a perfectionist that
never approves.
"""

from typing import Literal

from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from week2_agent_patterns.llm import call_anthropic


console = Console()


MAX_ITERATIONS = 4  # generate + at most 3 revisions


# ============================================================
# Schemas
# ============================================================


class Draft(BaseModel):
    """A draft of the content."""

    post: str = Field(description="The post text, ~250 words.")
    word_count: int = Field(description="Approximate word count.")


class Evaluation(BaseModel):
    """The evaluator's judgment on a draft."""

    verdict: Literal["ship", "revise"] = Field(
        description="'ship' if the post would land with a senior engineer audience. 'revise' otherwise."
    )
    issues: list[str] = Field(
        description=(
            "Specific, actionable issues to fix. Empty list if shipping. "
            "Each issue should be concrete: point at a specific phrase or beat, "
            "not 'could be better'. Example: 'The middle paragraph repeats the "
            "hook without adding new info' — not 'middle is weak'."
        ),
        max_length=5,
    )
    strengths: list[str] = Field(
        description="What's working well — useful even when shipping.",
        max_length=3,
    )


# ============================================================
# Drafter — handles both initial draft AND revisions
# ============================================================

DRAFTER_SYSTEM = (
    "You are a senior engineer-turned-writer in the voice of a sharp, "
    "build-in-public practitioner. Short sentences. No hedging. Concrete "
    "details over abstractions. Never use 'unlock', 'leverage', 'revolutionize'. "
    "~250 words. No headings."
)


def initial_draft(topic: str) -> Draft:
    """Generate the first draft."""
    prompt = (
        f"Topic: {topic}\n\n"
        "Write a ~250-word post on this topic in your voice. "
        "Make it specific. Make it land."
    )
    return call_anthropic(prompt, Draft, system=DRAFTER_SYSTEM)


def revise_draft(topic: str, previous_draft: str, issues: list[str]) -> Draft:
    """Revise based on evaluator feedback. Critical: feedback is *specific*."""
    issues_text = "\n".join(f"- {i}" for i in issues)
    prompt = (
        f"Topic: {topic}\n\n"
        f"Your previous draft:\n\n{previous_draft}\n\n"
        f"The editor flagged these specific issues:\n{issues_text}\n\n"
        "Revise the post addressing each issue. Don't rewrite from scratch — "
        "preserve what's working and fix what's broken. Same target word count."
    )
    return call_anthropic(prompt, Draft, system=DRAFTER_SYSTEM)


# ============================================================
# Evaluator
# ============================================================

EVALUATOR_SYSTEM = (
    "You are a tough editor reviewing posts for an engineer-builder brand. "
    "Look for: vague examples, hedging, generic phrases, missing specifics, "
    "claims without support, weak openings, AI-thought-leader tells. "
    "\n\n"
    "Be honest. The bar: would a senior engineer screenshot this? "
    "If yes → ship. If not → revise with specific actionable issues. "
    "\n\n"
    "Critical: when flagging issues, point at specific phrases or sentences, "
    "not vague complaints. 'Beat 2 starts with a generic claim — needs a "
    "specific example' is good. 'Middle is weak' is not. The drafter needs "
    "to know exactly what to change."
)


def evaluate(draft: Draft) -> Evaluation:
    """Judge the draft — ship or revise with specific issues."""
    prompt = (
        f"Draft to evaluate:\n\n{draft.post}\n\n"
        "Evaluate this draft. Verdict + issues + strengths."
    )
    return call_anthropic(prompt, Evaluation, system=EVALUATOR_SYSTEM)


# ============================================================
# The loop
# ============================================================


def run_evaluator_optimizer(topic: str) -> Draft:
    """Generate, evaluate, revise until ship or MAX_ITERATIONS."""
    console.print(f"\n[bold]Topic:[/bold] {topic}\n")

    console.print("[dim]Iteration 1: initial draft...[/dim]")
    draft = initial_draft(topic)

    for iteration in range(1, MAX_ITERATIONS + 1):
        console.print(
            Panel(
                Markdown(draft.post),
                title=f"Draft v{iteration} — {draft.word_count} words",
                border_style="blue",
            )
        )

        console.print(f"\n[dim]Evaluating draft v{iteration}...[/dim]")
        eval_result = evaluate(draft)

        if eval_result.verdict == "ship":
            console.print(
                Panel(
                    "[bold green]VERDICT: SHIP[/bold green]\n\n"
                    + "Strengths:\n"
                    + "\n".join(f"  ✓ {s}" for s in eval_result.strengths),
                    title=f"Evaluation v{iteration}",
                    border_style="green",
                )
            )
            console.print(
                f"\n[bold green]Converged after {iteration} iteration(s).[/bold green]"
            )
            return draft

        # verdict == "revise"
        console.print(
            Panel(
                "[bold yellow]VERDICT: REVISE[/bold yellow]\n\n"
                "Issues to fix:\n"
                + "\n".join(f"  • {issue}" for issue in eval_result.issues)
                + "\n\nStrengths to preserve:\n"
                + "\n".join(f"  ✓ {s}" for s in eval_result.strengths),
                title=f"Evaluation v{iteration}",
                border_style="yellow",
            )
        )

        if iteration == MAX_ITERATIONS:
            console.print(
                f"\n[yellow]Hit MAX_ITERATIONS ({MAX_ITERATIONS}). "
                "Returning latest draft despite revise verdict.[/yellow]"
            )
            return draft

        console.print(f"\n[dim]Iteration {iteration + 1}: revising...[/dim]")
        draft = revise_draft(topic, draft.post, eval_result.issues)

    return draft


def main() -> None:
    topic = (
        "Why 'agentic everything' is the wrong frame — most useful AI features "
        "are workflows, not agents."
    )
    final = run_evaluator_optimizer(topic)
    console.print("\n[bold]Final post for shipping:[/bold]\n")
    console.print(Markdown(final.post))


if __name__ == "__main__":
    main()
