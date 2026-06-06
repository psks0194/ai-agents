"""Routing pattern: classify input, dispatch to a specialist.

The router is a small, cheap, fast LLM whose only job is classification.
Specialists are full handlers with their own system prompts.
"""

from typing import Literal

from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel

from week2_agent_patterns.llm import call_anthropic, call_text_anthropic


console = Console()


# ============================================================
# The route classification
# ============================================================

RouteCategory = Literal["technical", "business", "quick_lookup"]


class RouteDecision(BaseModel):
    """The router's output."""

    category: RouteCategory = Field(
        description=(
            "Which specialist should handle this. "
            "'technical' for engineering/debugging/architecture questions. "
            "'business' for pricing/strategy/decision-making questions. "
            "'quick_lookup' for simple factual/definition/'what is X' questions."
        )
    )
    reasoning: str = Field(
        description="One sentence on why this category, for observability."
    )


ROUTER_SYSTEM = (
    "You are a request router. Your only job is to classify the user's question "
    "into one of three categories. You do NOT answer the question — you only "
    "decide which specialist should handle it. Be decisive. If genuinely "
    "ambiguous, lean toward 'technical' (most expensive, most thorough)."
)


def route(question: str) -> RouteDecision:
    """Classify a question into one of the specialist categories."""
    # Use a cheap, fast model for the router — it's a one-shot classifier
    return call_anthropic(
        prompt=f"Classify this question:\n\n{question}",
        schema=RouteDecision,
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=ROUTER_SYSTEM,
    )


# ============================================================
# The three specialists
# ============================================================

TECHNICAL_SYSTEM = (
    "You are a senior staff engineer answering technical questions for a "
    "working developer. Be concrete: show specific code patterns, name "
    "real tools, mention concrete tradeoffs. Avoid hedging. If the question "
    "is ambiguous, ask one clarifying question and stop. Answer in ≤200 words."
)


BUSINESS_SYSTEM = (
    "You are an experienced engineering manager helping someone think through "
    "a business or strategic decision. Frame the tradeoffs clearly. Surface "
    "what's actually at stake. Give one concrete recommendation if asked, but "
    "make it clear it's a recommendation, not a fact. ≤200 words."
)


QUICK_LOOKUP_SYSTEM = (
    "You answer simple factual questions in one or two sentences. No preamble. "
    "No 'great question'. No bullet points unless absolutely necessary. "
    "Just the answer."
)


def specialist_technical(question: str) -> str:
    return call_text_anthropic(
        prompt=question,
        model="claude-haiku-4-5-20251001",  # could use Sonnet for harder questions
        system=TECHNICAL_SYSTEM,
    )


def specialist_business(question: str) -> str:
    return call_text_anthropic(
        prompt=question,
        model="claude-haiku-4-5-20251001",
        system=BUSINESS_SYSTEM,
    )


def specialist_quick(question: str) -> str:
    return call_text_anthropic(
        prompt=question,
        model="claude-haiku-4-5-20251001",
        max_tokens=300,  # short answers only
        system=QUICK_LOOKUP_SYSTEM,
    )


SPECIALIST_DISPATCH = {
    "technical": specialist_technical,
    "business": specialist_business,
    "quick_lookup": specialist_quick,
}


# ============================================================
# The full router pipeline
# ============================================================


def run_router(question: str) -> str:
    """Route the question and dispatch to the right specialist."""
    console.print(f"\n[bold]Question:[/bold] {question}\n")

    console.print("[dim]Routing...[/dim]")
    decision = route(question)
    color = {"technical": "cyan", "business": "magenta", "quick_lookup": "green"}[
        decision.category
    ]
    console.print(
        Panel(
            f"[bold]Route:[/bold] [{color}]{decision.category}[/{color}]\n"
            f"[dim]Why:[/dim] {decision.reasoning}",
            title="Router decision",
            border_style=color,
        )
    )

    console.print(f"\n[dim]Dispatching to {decision.category} specialist...[/dim]")
    handler = SPECIALIST_DISPATCH[decision.category]
    answer = handler(question)
    console.print(
        Panel(
            answer,
            title=f"{decision.category} specialist response",
            border_style=color,
        )
    )

    return answer


def main() -> None:
    """Demo with three different question types."""
    questions = [
        "What's the difference between LangGraph and Pydantic AI?",
        "How much does Claude cost?",
        "My agent loop is hitting MAX_STEPS — what's going on?",
        # "How do I handle rate limits in an async tool-use loop without dropping requests?",
        # "Should I build my own MCP server or use an existing one for our Slack workspace?",
        # "What's a Pydantic BaseModel?",
    ]

    for q in questions:
        run_router(q)
        console.print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
