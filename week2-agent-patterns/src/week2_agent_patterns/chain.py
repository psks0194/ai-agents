"""The three-stage content pipeline: Scout → Outline → Drafter.

This is the prompt chaining pattern in its most useful form.
Each stage is one focused LLM call with a typed output.
The chain composes them; data flows through Pydantic models.
"""

import argparse

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from week2_agent_patterns.llm import call_anthropic
from week2_agent_patterns.models import Angle, Critique, Outline, Draft


console = Console()


# ============================================================
# Stage 1: Scout — find a sharp angle
# ============================================================

SCOUT_SYSTEM = (
    "You are a senior practitioner who writes for builders. "
    "Your goal is to find sharp, specific angles on technical topics — "
    "the kind of angle a working engineer would nod at, not the kind that "
    "lands on a thought-leadership LinkedIn slide. "
    "Avoid hype. Avoid 'X is here, X is the future'. "
    "Look for: what people miss, what's overrated, what's harder than it looks, "
    "what the real win actually is."
)


def scout(topic: str) -> Angle:
    """Stage 1: take a raw topic, return a sharp angle."""
    prompt = (
        f"Topic: {topic}\n\n"
        "Generate ONE sharp angle on this topic. Make it specific and "
        "non-obvious. Pretend you're talking to another engineer who's "
        "been in the trenches with this technology."
    )
    return call_anthropic(prompt, Angle, system=SCOUT_SYSTEM)


# ============================================================
# Stage 2: Outline — structure the angle
# ============================================================

OUTLINE_SYSTEM = (
    "You are a structural writing coach. Given an angle, you produce a tight, "
    "publishable outline: one punchy hook, exactly three beats, one close. "
    "Each beat is a single claim with one specific example or detail. "
    "Examples must be concrete — code patterns, actual product names, "
    "specific numbers, real workflows. Vague examples are the failure mode."
)


def outline(angle: Angle) -> Outline:
    """Stage 2: take an angle, return a structured outline."""
    prompt = (
        f"Angle: {angle.angle}\n"
        f"Why it lands: {angle.why_it_lands}\n\n"
        "Build an outline: hook, three beats, close. "
        "Each beat must be a concrete claim with a specific example."
    )
    return call_anthropic(prompt, Outline, system=OUTLINE_SYSTEM)


# ============================================================
# Stage 3: Drafter — turn outline into a post
# ============================================================

DRAFTER_SYSTEM = (
    "You are a senior engineer-turned-writer in the voice of a sharp, "
    "build-in-public practitioner. Voice traits: short sentences, no hedging, "
    "concrete details over abstractions, occasional dry humor, never use "
    "the word 'unlock' or 'leverage' or 'revolutionize'. "
    "Final output is ~250 words. No headings. No bullet points unless the "
    "post truly needs one short list. Reads like a tweet thread compressed "
    "into a paragraph-style post."
)


def drafter(angle: Angle, outline_obj: Outline) -> Draft:
    """Stage 3: take an outline, write the actual post."""
    beats_text = "\n".join(
        f"- Beat: {b.claim}\n  Example: {b.example}" for b in outline_obj.beats
    )
    prompt = (
        f"Angle: {angle.angle}\n\n"
        f"Hook: {outline_obj.hook}\n\n"
        f"Beats:\n{beats_text}\n\n"
        f"Close: {outline_obj.close}\n\n"
        "Write the post. ~250 words. Match the voice in your system prompt. "
        "The hook, beats, and close are the structure — but write it as flowing "
        "prose, not as labeled sections."
    )
    return call_anthropic(prompt, Draft, system=DRAFTER_SYSTEM)


# ============================================================
# Stage 4: Critic — does this post ship?
# ============================================================

CRITIC_SYSTEM = (
    "You are a tough editor reviewing a post for an engineer-builder brand. "
    "You're looking for: vague examples, hedging language, generic phrases "
    "('in today's fast-paced world'), missing specific details, claims without "
    "support, weak openings, weak closings, or any 'AI thought leader' tells. "
    "Be harsh. The bar is: would a senior engineer screenshot this? "
    "Verdict 'ship' only if it would pass that bar."
)


def critic(draft: Draft) -> "Critique":
    """Stage 4: judge whether the draft ships, or what needs to change."""
    from week2_agent_patterns.models import Critique

    prompt = (
        f"Post draft:\n\n{draft.post}\n\n"
        "Evaluate this post. Verdict 'ship' if it would land with a senior "
        "engineer audience, 'revise' otherwise. Be specific about what's "
        "working or what's broken. Give at most 4 reasons — the sharpest ones."
    )
    return call_anthropic(prompt, Critique, system=CRITIC_SYSTEM)


# ============================================================
# The chain — compose them
# ============================================================


def run_chain(topic: str) -> tuple[Draft, Critique]:
    """Run the full Scout → Outline → Drafter chain on a topic."""
    console.print(f"\n[bold]Topic:[/bold] {topic}\n")

    console.print("[dim]Stage 1: Scout — finding angle...[/dim]")
    angle = scout(topic)
    console.print(
        Panel(
            f"[bold]Angle:[/bold] {angle.angle}\n"
            f"[dim]Why it lands:[/dim] {angle.why_it_lands}",
            title="Stage 1 output",
            border_style="cyan",
        )
    )

    console.print("\n[dim]Stage 2: Outline — structuring...[/dim]")
    outline_obj = outline(angle)
    console.print(
        Panel(
            f"[bold]Hook:[/bold] {outline_obj.hook}\n\n"
            + "\n\n".join(
                f"[bold]Beat {i + 1}:[/bold] {b.claim}\n[dim]Example:[/dim] {b.example}"
                for i, b in enumerate(outline_obj.beats)
            )
            + f"\n\n[bold]Close:[/bold] {outline_obj.close}",
            title="Stage 2 output",
            border_style="magenta",
        )
    )

    console.print("\n[dim]Stage 3: Drafter — writing post...[/dim]")
    draft = drafter(angle, outline_obj)
    console.print(
        Panel(
            Markdown(draft.post),
            title=f"Stage 3 output — {draft.word_count} words",
            border_style="green",
        )
    )

    console.print("\n[dim]Stage 4: Critic — evaluating...[/dim]")
    critique = critic(draft)
    verdict_color = "green" if critique.verdict == "ship" else "yellow"
    console.print(
        Panel(
            f"[bold]Verdict:[/bold] [{verdict_color}]{critique.verdict.upper()}[/{verdict_color}]\n\n"
            + "\n".join(f"• {r}" for r in critique.reasons),
            title="Stage 4 output",
            border_style=verdict_color,
        )
    )

    return draft, critique


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the IntellAIgent content chain on a topic."
    )
    parser.add_argument(
        "topic",
        nargs="?",
        default="MCP servers — most people consume them, very few build them",
        help="The topic to write about.",
    )
    args = parser.parse_args()
    run_chain(args.topic)


if __name__ == "__main__":
    main()
