"""Composing patterns: routing dispatches to either a chain or a single specialist.

This is how real agent systems are structured — small patterns composed cleanly,
not one giant prompt.
"""

from typing import Literal

from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel

from week2_agent_patterns.chain import run_chain
from week2_agent_patterns.llm import call_anthropic, call_text_anthropic
from week2_agent_patterns.router import (
    TECHNICAL_SYSTEM,
    QUICK_LOOKUP_SYSTEM,
)


console = Console()


# ============================================================
# Composed router — three handlers, one is a full chain
# ============================================================

ComposedRoute = Literal["content_creator", "technical_qa", "quick_lookup"]


class ComposedRouteDecision(BaseModel):
    category: ComposedRoute = Field(
        description=(
            "'content_creator' if the user wants a written post or content piece. "
            "'technical_qa' for engineering/debugging/'how do I' questions. "
            "'quick_lookup' for simple factual/'what is X' questions."
        )
    )
    reasoning: str = Field(description="One sentence on why this category.")


COMPOSED_ROUTER_SYSTEM = (
    "You route user requests. Classify into one of three categories. "
    "You do NOT answer — you only decide. "
    "'content_creator' is for requests like 'write a post about X' or "
    "'draft a thread on Y' — anything where the user wants generated content. "
    "'technical_qa' is for 'how do I do X' or 'why is X happening'. "
    "'quick_lookup' is for 'what is X' or 'define X' — simple factual."
)


def route_composed(request: str) -> ComposedRouteDecision:
    return call_anthropic(
        prompt=f"Classify this request:\n\n{request}",
        schema=ComposedRouteDecision,
        max_tokens=256,
        system=COMPOSED_ROUTER_SYSTEM,
    )


# ============================================================
# Handlers
# ============================================================


def handle_content_creator(request: str) -> str:
    """Run the full chain from Day 1 — Scout, Outline, Drafter, Critic."""
    console.print("\n[dim]Routing to: content_creator (full chain)[/dim]\n")
    draft, critique = run_chain(request)
    return draft.post


def handle_technical_qa(request: str) -> str:
    """Single-call technical specialist."""
    console.print("\n[dim]Routing to: technical_qa[/dim]\n")
    answer = call_text_anthropic(prompt=request, system=TECHNICAL_SYSTEM)
    console.print(Panel(answer, title="Technical answer", border_style="cyan"))
    return answer


def handle_quick_lookup(request: str) -> str:
    """Single-call quick lookup."""
    console.print("\n[dim]Routing to: quick_lookup[/dim]\n")
    answer = call_text_anthropic(
        prompt=request,
        system=QUICK_LOOKUP_SYSTEM,
        max_tokens=300,
    )
    console.print(Panel(answer, title="Quick lookup", border_style="green"))
    return answer


COMPOSED_DISPATCH = {
    "content_creator": handle_content_creator,
    "technical_qa": handle_technical_qa,
    "quick_lookup": handle_quick_lookup,
}


def run_composed(request: str) -> str:
    """Route → dispatch to the right pipeline (chain or single-call)."""
    console.print(f"\n[bold]Request:[/bold] {request}\n")

    decision = route_composed(request)
    color = {
        "content_creator": "yellow",
        "technical_qa": "cyan",
        "quick_lookup": "green",
    }[decision.category]

    console.print(
        Panel(
            f"[bold]Route:[/bold] [{color}]{decision.category}[/{color}]\n"
            f"[dim]Why:[/dim] {decision.reasoning}",
            title="Router decision",
            border_style=color,
        )
    )

    handler = COMPOSED_DISPATCH[decision.category]
    return handler(request)


def main() -> None:
    requests = [
        "Write a short post about why most agent frameworks are wrappers around 80 lines of code.",
        "How do I handle malformed tool inputs in an Anthropic SDK loop?",
        "What is JSON Schema?",
    ]

    for r in requests:
        run_composed(r)
        console.print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
