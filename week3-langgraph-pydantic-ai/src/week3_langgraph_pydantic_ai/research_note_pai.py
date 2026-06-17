"""Research note generator — Pydantic AI version.

Input: a topic.
Output: a typed ResearchNote with title, summary, key points, sources.
Tools: fetch_url, get_current_date.

Build a runnable, observable version with full token tracking.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from rich.console import Console
from rich.panel import Panel

from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from week3_langgraph_pydantic_ai.config import settings


console = Console()


# ============================================================
# Output schema
# ============================================================


class KeyPoint(BaseModel):
    point: str = Field(description="One concrete claim, one sentence.")
    evidence: str = Field(description="Specific support — quote, fact, or example.")


class ResearchNote(BaseModel):
    """A structured research note on a topic."""

    title: str = Field(description="A specific, evocative title for the note.")
    summary: str = Field(description="One-paragraph summary, ~60 words.")
    key_points: list[KeyPoint] = Field(
        description="Three to five key points with evidence.",
        min_length=3,
        max_length=5,
    )
    sources_mentioned: list[str] = Field(
        description=(
            "URLs or named sources referenced. Empty list if you relied only "
            "on general knowledge."
        ),
    )
    generated_at: str = Field(description="ISO timestamp when generated.")


# ============================================================
# Dependencies
# ============================================================


@dataclass
class Deps:
    http_client: httpx.Client


# ============================================================
# Agent
# ============================================================

model = AnthropicModel(
    "claude-haiku-4-5-20251001",
    provider=AnthropicProvider(api_key=settings.anthropic_api_key),
)

agent = Agent(
    model,
    deps_type=Deps,
    output_type=ResearchNote,
    instructions=(
        "You produce structured research notes on technical topics. "
        "Use the available tools when current information matters. "
        "For key points: each point must have specific evidence (a quote, "
        "a fact with a number, a named tool/product). Vague evidence is the "
        "failure mode. Generate ~3-5 key points."
    ),
)


# ============================================================
# Tools
# ============================================================


@agent.tool
def fetch_url(ctx: RunContext[Deps], url: str) -> str:
    """Fetch a web page and return the first 5000 characters.

    Use when you need current information from a specific URL the user
    has provided or that's clearly relevant to the topic.

    Args:
        url: Full URL including https://.
    """
    console.print(f"[yellow]  → fetch_url({url})[/yellow]")
    try:
        response = ctx.deps.http_client.get(
            url,
            timeout=10.0,
            follow_redirects=True,
            headers={"User-Agent": "research-note-agent/0.1"},
        )
        response.raise_for_status()
        text = response.text[:5000]
        console.print(f"[green]  ← {len(text)} chars[/green]")
        return f"URL: {url}\nStatus: {response.status_code}\n\n{text}"
    except Exception as e:
        return f"Error fetching {url}: {type(e).__name__}: {e}"


@agent.tool
def get_current_date(ctx: RunContext[Deps], timezone: str = "UTC") -> str:
    """Get today's date in the specified IANA timezone.

    Use this to timestamp the research note or to know what 'current' means
    when discussing recency.

    Args:
        timezone: IANA timezone name. Defaults to UTC.
    """
    console.print(f"[yellow]  → get_current_date({timezone})[/yellow]")
    try:
        now = datetime.now(ZoneInfo(timezone))
        result = now.isoformat()
        console.print(f"[green]  ← {result}[/green]")
        return result
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


# ============================================================
# Run + measure
# ============================================================


def run(topic: str) -> tuple[ResearchNote, dict]:
    """Run the agent on a topic and return (note, metrics)."""
    console.print(f"\n[bold cyan]Pydantic AI:[/bold cyan] {topic}\n")

    start = time.perf_counter()
    with httpx.Client() as client:
        result = agent.run_sync(topic, deps=Deps(http_client=client))
    elapsed = time.perf_counter() - start

    usage = result.usage()
    metrics = {
        "elapsed_sec": elapsed,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "requests": usage.requests,
    }
    return result.output, metrics


def display(note: ResearchNote, metrics: dict) -> None:
    console.print(
        Panel(
            f"[bold]{note.title}[/bold]\n\n"
            f"[dim]{note.summary}[/dim]\n\n"
            + "\n\n".join(
                f"[cyan]{i + 1}. {kp.point}[/cyan]\n   [dim]Evidence:[/dim] {kp.evidence}"
                for i, kp in enumerate(note.key_points)
            )
            + (
                f"\n\n[dim]Sources: {', '.join(note.sources_mentioned)}[/dim]"
                if note.sources_mentioned
                else "\n\n[dim]Sources: (general knowledge)[/dim]"
            )
            + f"\n\n[dim]Generated at: {note.generated_at}[/dim]",
            title="Research Note (Pydantic AI)",
            border_style="cyan",
        )
    )
    console.print(
        f"\n[dim]Metrics: {metrics['elapsed_sec']:.2f}s, "
        f"{metrics['input_tokens']} in / {metrics['output_tokens']} out, "
        f"{metrics['requests']} requests[/dim]"
    )


def main() -> None:
    topic = (
        "What's the current state of MCP (Model Context Protocol) adoption "
        "across major AI tools in mid-2026? Be specific about which tools "
        "support it and how."
    )
    note, metrics = run(topic)
    display(note, metrics)


if __name__ == "__main__":
    main()
