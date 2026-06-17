"""Pydantic AI version of the Week 1 Day 2 tool-using agent.

Same tools (calculator, time, fetch_url), same loop semantics.
Compare to week1-tri-provider-agent/src/week1_tri_provider_agent/agent.py.

Pydantic AI handles the loop internally — you define tools as decorated
functions, the agent decides when to call them, the framework runs the loop.
"""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from rich.console import Console

import asyncio
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartStartEvent,
    FinalResultEvent,
)

from week3_langgraph_pydantic_ai.config import settings


console = Console()


# ============================================================
# Dependencies — anything the agent's tools need at runtime
# ============================================================


@dataclass
class AgentDeps:
    """Dependencies injected into every tool call.

    Holds the HTTP client so we don't open one per tool call.
    In real code this might also hold a database, an API key for a
    specific service, a user identity, etc.
    """

    http_client: httpx.Client


# ============================================================
# The agent — declares its deps type + instructions
# ============================================================

model = AnthropicModel(
    "claude-haiku-4-5-20251001",
    provider=AnthropicProvider(api_key=settings.anthropic_api_key),
)

agent = Agent(
    model,
    deps_type=AgentDeps,
    instructions=(
        "You are a helpful assistant with access to tools. "
        "When a question requires computation or external information, use the "
        "appropriate tool. After receiving results, give a clear, concise final answer."
    ),
)


# ============================================================
# Tools — ordinary Python functions, decorated
# ============================================================


@agent.tool
def calculator(ctx: RunContext[AgentDeps], expression: str) -> str:
    """Evaluate a basic mathematical expression.

    Supports +, -, *, /, **, and parentheses. Use this whenever you need
    to compute a numeric result.

    Args:
        expression: A math expression like '47 * 83 + 199' or '(5 + 3) ** 2'.
    """
    console.print(f"[yellow]→ calculator({expression!r})[/yellow]")
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        console.print(f"[green]← {result}[/green]")
        return str(result)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@agent.tool
def get_current_time(ctx: RunContext[AgentDeps], timezone: str) -> str:
    """Get the current date and time in a specified IANA timezone.

    Use this when the user asks about the current time, today's date, or
    anything time-sensitive. Returns ISO format with timezone.

    Args:
        timezone: IANA timezone name, e.g. 'Asia/Kolkata', 'America/New_York',
            'Europe/London', 'UTC'. Default to 'UTC' if user gave no preference.
    """
    console.print(f"[yellow]→ get_current_time({timezone!r})[/yellow]")
    try:
        now = datetime.now(ZoneInfo(timezone))
        result = now.isoformat()
        console.print(f"[green]← {result}[/green]")
        return result
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@agent.tool
def fetch_url(ctx: RunContext[AgentDeps], url: str) -> str:
    """Fetch the contents of a web page.

    Returns the first 5000 characters of the page text. Use when you need
    current information from a specific URL.

    Args:
        url: The full URL to fetch, including https://.
    """
    console.print(f"[yellow]→ fetch_url({url!r})[/yellow]")
    try:
        response = ctx.deps.http_client.get(
            url,
            timeout=10.0,
            follow_redirects=True,
            headers={"User-Agent": "week3-agent/0.1"},
        )
        response.raise_for_status()
        text = response.text[:5000]
        result = f"URL: {url}\nStatus: {response.status_code}\n\n{text}"
        console.print(f"[green]← fetched {len(text)} chars[/green]")
        return result
    except Exception as e:
        return f"Error fetching {url}: {type(e).__name__}: {e}"


async def run_with_events(prompt: str, deps: AgentDeps) -> None:
    """Stream the agent's execution events to see the loop internals."""
    console.print(f"\n[bold]You:[/bold] {prompt}\n")

    async with agent.iter(prompt, deps=deps) as run:
        async for node in run:
            if Agent.is_user_prompt_node(node):
                console.print("[dim]── user prompt prepared ──[/dim]")
            elif Agent.is_model_request_node(node):
                console.print("[dim]── calling model ──[/dim]")
                async with node.stream(run.ctx) as stream:
                    async for event in stream:
                        if isinstance(event, PartStartEvent):
                            console.print(
                                f"[dim]  start: {type(event.part).__name__}[/dim]"
                            )
                        elif isinstance(event, FinalResultEvent):
                            console.print("[dim]  → final result coming[/dim]")
            elif Agent.is_call_tools_node(node):
                console.print("[dim]── executing tools ──[/dim]")
                async with node.stream(run.ctx) as stream:
                    async for event in stream:
                        if isinstance(event, FunctionToolCallEvent):
                            console.print(
                                f"[yellow]  → tool: {event.part.tool_name}"
                                f"({event.part.args})[/yellow]"
                            )
                        elif isinstance(event, FunctionToolResultEvent):
                            console.print(
                                f"[green]  ← result: {str(event.result.content)[:100]}...[/green]"
                            )
            elif Agent.is_end_node(node):
                console.print("[dim]── done ──[/dim]")

        # run.result has the final output
        console.print(f"\n[bold blue]Agent:[/bold blue] {run.result.output}")


def run_events_demo() -> None:
    """Sync wrapper to call the async event-streaming version."""
    with httpx.Client() as client:
        deps = AgentDeps(http_client=client)
        asyncio.run(
            run_with_events(
                "What time is it in Mumbai? Also, what's 47 * 83 + 199?",
                deps,
            )
        )


# ============================================================
# Run it
# ============================================================


# Update main to demo both modes
def main() -> None:
    console.print("[bold cyan]=== Mode 1: agent.run_sync (loop hidden) ===[/bold cyan]")

    with httpx.Client() as client:
        deps = AgentDeps(http_client=client)
        result = agent.run_sync("What time is it in Mumbai?", deps=deps)
        console.print(f"Result: {result.output}")

    console.print(
        "\n[bold cyan]=== Mode 2: agent.iter (events visible) ===[/bold cyan]"
    )
    run_events_demo()


if __name__ == "__main__":
    main()
