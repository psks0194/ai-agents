"""Research note generator — OpenAI Agents SDK version.

Third implementation of the same task from Week 3 Day 4.
Compare line-by-line to research_note_pai.py and research_note_lg.py.
"""

import time
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from agents import Agent, Runner, function_tool, set_default_openai_key
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from week4_openai_mastra.config import settings


console = Console()
set_default_openai_key(settings.openai_api_key)


# ============================================================
# Output schema — SAME as Week 3 Day 4 versions
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
            "URLs or named sources referenced. Empty list if you relied "
            "only on general knowledge."
        ),
    )
    generated_at: str = Field(description="ISO timestamp when generated.")


# ============================================================
# Tools
# ============================================================

_http_client = httpx.Client()


@function_tool
def fetch_url(url: str) -> str:
    """Fetch a web page and return the first 5000 characters.

    Use when you need current information from a specific URL the user
    has provided or that's clearly relevant to the topic.

    Args:
        url: Full URL including https://.
    """
    console.print(f"[yellow]  → fetch_url({url})[/yellow]")
    try:
        response = _http_client.get(
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


@function_tool
def get_current_date(timezone: str = "UTC") -> str:
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
# Agent
# ============================================================

researcher = Agent(
    name="ResearchNoteGenerator",
    instructions=(
        "You produce structured research notes on technical topics. "
        "Use the available tools when current information matters. "
        "For key points: each point must have specific evidence (a quote, "
        "a fact with a number, a named tool/product). Vague evidence is "
        "the failure mode. Generate 3-5 key points."
    ),
    tools=[fetch_url, get_current_date],
    output_type=ResearchNote,
)


# ============================================================
# Run + measure
# ============================================================


def run(topic: str) -> tuple[ResearchNote, dict]:
    """Run the agent on a topic and return (note, metrics)."""
    console.print(f"\n[bold magenta]OpenAI Agents SDK:[/bold magenta] {topic}\n")

    start = time.perf_counter()
    result = Runner.run_sync(researcher, topic)
    elapsed = time.perf_counter() - start

    usage = result.context_wrapper.usage
    metrics = {
        "elapsed_sec": elapsed,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "requests": usage.requests,
    }
    return result.final_output, metrics


def display(note: ResearchNote, metrics: dict) -> None:
    console.print(
        Panel(
            f"[bold]{note.title}[/bold]\n\n"
            f"[dim]{note.summary}[/dim]\n\n"
            + "\n\n".join(
                f"[magenta]{i + 1}. {kp.point}[/magenta]\n"
                f"   [dim]Evidence:[/dim] {kp.evidence}"
                for i, kp in enumerate(note.key_points)
            )
            + (
                f"\n\n[dim]Sources: {', '.join(note.sources_mentioned)}[/dim]"
                if note.sources_mentioned
                else "\n\n[dim]Sources: (general knowledge)[/dim]"
            )
            + f"\n\n[dim]Generated at: {note.generated_at}[/dim]",
            title="Research Note (OpenAI Agents SDK)",
            border_style="magenta",
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
