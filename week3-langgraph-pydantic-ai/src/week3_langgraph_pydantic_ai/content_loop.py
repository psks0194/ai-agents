"""The Week 2 Day 1 content pipeline, rebuilt as a LangGraph graph.

Same four stages (Scout → Outline → Drafter → Critic), now expressed as
nodes in a state machine. Compare line-by-line to week2_agent_patterns/chain.py
to see what LangGraph adds and what it abstracts away.
"""

from typing import Literal

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from week3_langgraph_pydantic_ai.config import settings
from langgraph.checkpoint.memory import MemorySaver


console = Console()


# ============================================================
# State schema — everything that flows through the graph
# ============================================================


class ContentState(BaseModel):
    """The full state of the content pipeline."""

    # Input
    topic: str = Field(description="What we're writing about.")

    # Loop control
    iteration: int = Field(default=0, description="How many drafter rounds completed.")
    max_iterations: int = Field(default=3, description="Hard cap on revisions.")

    # Produced by each stage
    angle: str | None = None
    angle_reasoning: str | None = None
    hook: str | None = None
    beats: list[dict] | None = None
    close: str | None = None
    post: str | None = None
    word_count: int | None = None
    verdict: Literal["ship", "revise"] | None = None
    critique_reasons: list[str] | None = None


# ============================================================
# Schemas for structured LLM output at each stage
# ============================================================


class AngleOutput(BaseModel):
    angle: str = Field(description="One sharp, specific declarative sentence.")
    reasoning: str = Field(description="One sentence on why this angle lands.")


class OutlineBeat(BaseModel):
    claim: str
    example: str


class OutlineOutput(BaseModel):
    hook: str
    beats: list[OutlineBeat] = Field(min_length=3, max_length=3)
    close: str


class DraftOutput(BaseModel):
    post: str = Field(description="The full post, ~250 words.")
    word_count: int


class CritiqueOutput(BaseModel):
    verdict: Literal["ship", "revise"]
    reasons: list[str] = Field(min_length=1, max_length=4)


# ============================================================
# LLM helpers
# ============================================================

# Default model — Haiku for speed
HAIKU = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    max_tokens=2048,
    api_key=settings.anthropic_api_key,
)


def _call_with_schema(model, system: str, user: str, schema):
    """Helper: call the model with a typed-output schema."""
    structured = model.with_structured_output(schema)
    return structured.invoke(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    )


# ============================================================
# Nodes — one per stage
# ============================================================

SCOUT_SYSTEM = (
    "You find sharp, specific angles on technical topics. "
    "Avoid generic 'X is the future' hype. Look for what people miss, "
    "what's overrated, what the real win actually is."
)


def scout_node(state: ContentState) -> dict:
    """Stage 1: find an angle on the topic."""
    console.print("[dim]→ scout[/dim]")
    result: AngleOutput = _call_with_schema(
        HAIKU,
        SCOUT_SYSTEM,
        f"Topic: {state.topic}\n\nGenerate one sharp angle.",
        AngleOutput,
    )
    return {"angle": result.angle, "angle_reasoning": result.reasoning}


OUTLINE_SYSTEM = (
    "Given an angle, produce a tight outline: hook, three beats, close. "
    "Each beat = one specific claim with one concrete example."
)


def outline_node(state: ContentState) -> dict:
    """Stage 2: structure the angle into an outline."""
    console.print("[dim]→ outline[/dim]")
    result: OutlineOutput = _call_with_schema(
        HAIKU,
        OUTLINE_SYSTEM,
        f"Angle: {state.angle}\n\nBuild the outline.",
        OutlineOutput,
    )
    return {
        "hook": result.hook,
        "beats": [b.model_dump() for b in result.beats],
        "close": result.close,
    }


DRAFTER_SYSTEM = (
    "You're a senior engineer-turned-writer. Short sentences, no hedging, "
    "concrete details, no 'unlock' or 'leverage'. ~250 words, prose only."
)


def drafter_node(state: ContentState) -> dict:
    """Stage 3: write the post — or revise if there's prior critique."""
    is_revision = state.iteration > 0 and state.critique_reasons

    if is_revision:
        console.print(f"[dim]→ drafter (revision {state.iteration})[/dim]")
        beats_text = "\n".join(
            f"- {b['claim']}\n  Example: {b['example']}" for b in state.beats
        )
        reasons_text = "\n".join(f"- {r}" for r in state.critique_reasons)
        user = (
            f"Angle: {state.angle}\n\n"
            f"Hook: {state.hook}\n\n"
            f"Beats:\n{beats_text}\n\n"
            f"Close: {state.close}\n\n"
            f"Your previous draft:\n\n{state.post}\n\n"
            f"Editor flagged these specific issues:\n{reasons_text}\n\n"
            "Revise the post addressing each issue. Preserve what works, "
            "fix what's broken. Same target word count."
        )
    else:
        console.print("[dim]→ drafter (initial)[/dim]")
        beats_text = "\n".join(
            f"- {b['claim']}\n  Example: {b['example']}" for b in state.beats
        )
        user = (
            f"Angle: {state.angle}\n\n"
            f"Hook: {state.hook}\n\n"
            f"Beats:\n{beats_text}\n\n"
            f"Close: {state.close}\n\n"
            "Write the post as flowing prose."
        )

    result: DraftOutput = _call_with_schema(HAIKU, DRAFTER_SYSTEM, user, DraftOutput)
    return {
        "post": result.post,
        "word_count": result.word_count,
        "iteration": state.iteration + 1,
    }


CRITIC_SYSTEM = (
    "You're a tough editor for an engineer-builder audience. "
    "The bar: would a senior engineer screenshot this? "
    "Be specific in your feedback."
)


def critic_node(state: ContentState) -> dict:
    """Stage 4: evaluate the post."""
    console.print("[dim]→ critic[/dim]")
    result: CritiqueOutput = _call_with_schema(
        HAIKU,
        CRITIC_SYSTEM,
        f"Post:\n\n{state.post}\n\nEvaluate.",
        CritiqueOutput,
    )
    return {"verdict": result.verdict, "critique_reasons": result.reasons}


def route_after_critic(state: ContentState) -> Literal["drafter", "__end__"]:
    """Decide where to go after the critic runs.

    'ship' or iteration cap → END
    'revise' and iterations remain → back to drafter
    """
    if state.verdict == "ship":
        console.print(f"[green]→ ship (iteration {state.iteration})[/green]")
        return END

    if state.iteration >= state.max_iterations:
        console.print(
            f"[yellow]→ end (hit max_iterations {state.max_iterations})[/yellow]"
        )
        return END

    console.print(
        f"[cyan]→ loop back to drafter (iteration {state.iteration}/{state.max_iterations})[/cyan]"
    )
    return "drafter"


# ============================================================
# Build the graph
# ============================================================


def build_graph(use_checkpointer: bool = True):
    builder = StateGraph(ContentState)

    builder.add_node("scout", scout_node)
    builder.add_node("outline", outline_node)
    builder.add_node("drafter", drafter_node)
    builder.add_node("critic", critic_node)

    builder.add_edge(START, "scout")
    builder.add_edge("scout", "outline")
    builder.add_edge("outline", "drafter")
    builder.add_edge("drafter", "critic")
    builder.add_conditional_edges(
        "critic", route_after_critic, {"drafter": "drafter", END: END}
    )
    if use_checkpointer:
        checkpointer = MemorySaver()
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()


# Compile once at import time; both run() and main() use this.
graph = build_graph()


# ============================================================
# Run + display
# ============================================================


def run(topic: str, max_iterations: int = 3) -> ContentState:
    graph = build_graph()

    console.print(f"\n[bold]Topic:[/bold] {topic}")
    console.print(f"[dim]Max iterations: {max_iterations}[/dim]\n")

    final_state = graph.invoke(
        {
            "topic": topic,
            "max_iterations": max_iterations,
        }
    )

    state = ContentState.model_validate(final_state)

    # Display final state
    console.print(
        Panel(
            f"[bold]Angle:[/bold] {state.angle}",
            title="Scout",
            border_style="cyan",
        )
    )

    console.print(
        Panel(
            Markdown(state.post),
            title=f"Final draft (after {state.iteration} drafter runs) — {state.word_count} words",
            border_style="green",
        )
    )

    verdict_color = "green" if state.verdict == "ship" else "yellow"
    console.print(
        Panel(
            f"[bold]Verdict:[/bold] [{verdict_color}]{state.verdict.upper()}[/{verdict_color}]\n\n"
            + "\n".join(f"• {r}" for r in state.critique_reasons),
            title="Final critique",
            border_style=verdict_color,
        )
    )

    return state


def main() -> None:
    run(
        "why 'agentic everything' is the wrong frame for most AI features",
        max_iterations=3,
    )


if __name__ == "__main__":
    main()
